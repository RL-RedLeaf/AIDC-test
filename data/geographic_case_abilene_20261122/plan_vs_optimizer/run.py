"""Original eight-building Abilene plan and a land-limited redesign; run from any directory."""
import argparse
import csv
import gzip
import json
import math
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, vstack

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CASE = HERE.parent.relative_to(ROOT)
TECHS = {"coal", "gas", "wind", "pv"}
TOL = 2e-6
sys.path.insert(0, str(ROOT / "code"))
from immc_power_capacity.core import assess_site, solve_storage_capacity


def write_csv(out, name, rows):
    with (out / name).open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_case(data_root, params):
    parent = data_root / CASE
    with (parent / "outputs/04_design_day_weather_to_PV.csv").open(encoding="utf-8-sig") as f:
        weather = list(csv.DictReader(f))
    assert len(weather) == 24 and {r["local_time"][:10] for r in weather} == {"2025-01-29"}
    db = parent / "eight_building_land_review/site-land.gpkg"
    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as conn:
        ledger = {m: (a, b) for m, a, b in conn.execute("select metric,drawn,lots from area_ledger")}
        first = conn.execute("select area_ha from patch_areas_lots where rank_no=1").fetchone()[0]
        assert math.isclose(ledger["largest"][1], first)
    history = data_root / "正稿/Q1-v2/IMMC2027-Q1/图片和附件/data_center_timelines.csv"
    with history.open(encoding="utf-8-sig") as f:
        epoch = next(r for r in csv.DictReader(f) if r["Data center"] == "OpenAI Stargate Abilene"
                     and r["Date"] == params["reference_date"])
    assert int(float(epoch["Buildings operational"])) == params["buildings"]
    return weather, ledger, epoch


def site_inputs(params, weather, grid, water, k, slope, working_area, fixed):
    tech = params["tech"]
    wind = [float(w["wind_turbine_power_ratio_assumed"]) for w in weather]
    solar = [float(w["PV_AC_supply_ratio_PR_0_85_temp_adjusted"]) for w in weather]
    battery_mw = tech["storage_mw_per_renewable_mw"]
    battery = {"C_max_mw": battery_mw, "D_max_mw": battery_mw,
               "E_usable_mwh": battery_mw * tech["storage_hours"],
               "charge_efficiency": tech["charge_efficiency"], "discharge_efficiency": tech["discharge_efficiency"]}
    pv_ha = tech["pv_acres_per_mwac"] * params["acre_to_ha"]
    scenarios = [{"name": "planned_import", "type": "grid", "generation_land_ha": 0}]
    for kind in ("coal", "gas"):
        t = tech[kind]
        scenarios.append({"name": kind, "type": kind, "units": t["max_units"], "unit_net_mw": t["net_mw"],
                          "unit_land_ha": t["ha_per_unit"], "generation_land_ha": t["max_units"] * t["ha_per_unit"],
                          "generation_water_l_per_kwh": t["water_l_per_kwh"]})
    scenarios.extend([
        {"name": "wind", "type": "combined_battery", "installed_mw": 1, "supply_series_mw": wind,
         "generation_land_ha": tech["wind_ha_per_mw"], "dt_hours": 1, "battery": battery},
        {"name": "pv", "type": "solar", "area_km2": pv_ha / 100, "density_mw_per_km2": 100 / pv_ha,
         "generation_land_ha": pv_ha, "supply_ratios": solar, "dt_hours": 1, "battery": battery},
    ])
    for option in scenarios:
        option["online_year"] = 2026 if option["type"] == "grid" else params["redesign_horizon_year"]
    return {"model": "q1", "site": "Original eight-building Abilene footprint",
            "assessment_year": params["redesign_horizon_year"], "period_note": "2025-01-29 weather; hypothetical ready-by horizon for redesign",
            "service_level": "Normal operation, constant IT load, existing backup excluded",
            "P_grid_mw": grid, "k_factor": k, "water": {"basis": "withdrawal", "source_m3_h": water,
            "wue_l_per_kwh_it": params["wue_l_kwh_it"]}, "land": {"effective_ha": working_area + fixed,
            "fixed_it_ha": fixed, "generation_land_ha": 0, "ha_per_mw_it": slope}, "scenarios": scenarios}


def firm_renewable(mix, w, s):
    total = w + s
    if total < 1e-9:
        return 0.0
    hourly_supply = (mix.profile @ [w, s]).clip(0)
    return solve_storage_capacity(hourly_supply, 1, mix.charge * total, mix.discharge * total,
                                  mix.energy * total, mix.ec, mix.ed)[0]


def fit_portfolio(mix_class, config, weather, patch, allowed, ordinary_cap=None, retained_it=None):
    """Keep the repository's Mix LP; constrain all generation to one eligible patch."""
    mix = mix_class(config, weather)
    n = len(mix.power_objective)
    land_row = np.zeros(n)
    land_row[1:3] = mix.land_per_mw[2:]
    extra = [land_row]
    limits = [patch]
    for idx, kind in [(1, "wind"), (2, "pv")]:
        if kind not in allowed:
            row = np.zeros(n)
            row[idx] = 1
            extra.append(row)
            limits.append(0)
    if ordinary_cap is not None:
        row = np.zeros(n)
        row[0] = 1
        extra.append(row)
        limits.append(ordinary_cap)
    if retained_it is not None:
        # Existing IT lots stay occupied. Only incremental IT and new generation use the patch:
        # a * (IT - retained_it) + A_generation <= patch.
        mix.area = patch + mix.intensity * retained_it
        mix.b[0] = mix.area
        row = np.zeros(n)
        row[0] = -1
        extra.append(row)
        limits.append(-retained_it)
    patch_idx = len(mix.b)
    mix.A = vstack([mix.A, csr_matrix(np.asarray(extra))], format="csr")
    mix.b = np.r_[mix.b, limits]
    candidates, branches = [], []
    for counts in mix.counts:
        coal, gas = counts
        if (coal and "coal" not in allowed) or (gas and "gas" not in allowed):
            continue
        thermal = np.asarray(counts) * mix.unit
        thermal_land = float(thermal @ mix.land_per_mw[:2])
        mix.b[patch_idx] = patch - thermal_land
        if thermal_land > patch + TOL:
            branches.append((coal, gas, "exceeds_patch", None))
            continue
        initial = mix.solve(counts)
        if initial is None:
            branches.append((coal, gas, "infeasible", None))
            continue
        # Repository's tie-break minimizes renewable nameplate at a fixed IT optimum.
        solution = mix.solve(counts, peak=initial[0])
        total = thermal.sum() + solution[1:3].sum()
        installed, water, hourly = mix.audit(counts, solution, total)
        gen_area = float(installed @ mix.land_per_mw)
        assert gen_area <= patch + TOL
        branches.append((coal, gas, "optimal_for_counts", float(solution[0])))
        candidates.append((float(solution[0]), float(total), gen_area, installed, water, hourly))
    peak = max(c[0] for c in candidates)
    chosen = min((c for c in candidates if c[0] >= peak - TOL), key=lambda c: (c[1], c[2]))
    p, total, gen_area, installed, water, hourly = chosen
    coal, gas, w, s = np.maximum(installed, 0)
    firm = firm_renewable(mix, w, s)
    electric = (mix.grid + coal + gas + firm) / mix.k
    land_max = (mix.area - gen_area) / mix.intensity
    if ordinary_cap is not None:
        land_max = min(land_max, ordinary_cap)
    assert p <= min(electric, land_max) + TOL and water.max() <= mix.q + TOL
    binding = []
    if abs(electric - p) <= TOL:
        binding.append("electricity")
    if abs(land_max - p) <= TOL:
        binding.append("land")
    if abs(float(water.max()) - mix.q) <= TOL and min(electric, land_max) > p + TOL:
        binding.append("water")
    assert binding, (p, electric, land_max, water.max())
    return {"it_mw": p, "coal_mw": coal, "gas_mw": gas, "wind_mw": w, "pv_mw": s,
            "battery_mw": mix.charge * (w+s), "battery_mwh": mix.energy * (w+s),
            "gen_ha": gen_area, "firm_renewable_mw": firm, "p_e_mw_it": electric,
            "p_l_mw_it": land_max, "water_budget_m3_h": mix.q,
            "max_water_feasible_schedule_m3_h": float(water.max()), "binding": "+".join(binding)}, branches


def validate_weather(p, renewable, grid, k):
    model = p["weather_model"]
    with gzip.open(HERE / "weather_2024.csv.gz", "rt", encoding="utf8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 8784
    assert all(datetime.fromisoformat(r["time_utc"]) == datetime(2024,1,1) + timedelta(hours=i)
               for i,r in enumerate(rows))
    ghi, temp, wind = (np.array([float(r[key]) for r in rows])
                       for key in ("ghi_w_m2", "temperature_c", "wind10_km_h"))
    assert all(np.isfinite(a).all() for a in (ghi, temp, wind))
    cell = temp + (model["noct_c"]-20)*ghi/800
    pv = np.maximum(0, ghi / 1000 * model["pv_pr"] * np.maximum(0, 1 + model["pv_temp_coeff_per_c"]*(cell-25)))
    speed = wind/3.6*(model["wind_hub_m"]/model["wind_measurement_m"])**model["wind_exponent"]
    cut, rated, end = (model[x] for x in ("wind_cutin_ms","wind_rated_ms","wind_cutout_ms"))
    wind_ratio = np.where((speed < cut)|(speed >= end), 0, np.clip((speed**3-cut**3)/(rated**3-cut**3),0,1))
    supply = pv*renewable["pv_mw"] + wind_ratio*renewable["wind_mw"]
    t = p["tech"]
    annual, _ = solve_storage_capacity(supply, 1, renewable["battery_mw"], renewable["battery_mw"],
                                       renewable["battery_mwh"], t["charge_efficiency"], t["discharge_efficiency"])
    return [{"window": label, "hours": hours, "reliable_extra_mw": firm, "extra_it_if_power_binds": firm/k,
             "electric_bound_mw_it": (grid+firm)/k}
            for label,hours,firm in [("2025-01-29_selected",24,renewable["firm_renewable_mw"]),
                                     ("2024_full_year_holdout",len(rows),annual)]]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=ROOT, help="Full repository tree holding the upstream case files")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    args = ap.parse_args()
    data_root = args.data_root.resolve()
    sys.path.insert(0, str(data_root / CASE))
    from plot_fixed_installation import Mix
    p = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    weather, ledger, epoch = load_case(data_root, p)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    grid = p["firm_share"] * p["grid_nameplate_mw"]
    k = p["k_factor"]
    q = p["city_2030_surplus_acre_ft_year"] * p["acre_ft_m3"] / p["hours_year"]
    a = p["phase1_leased_acres"] * p["acre_to_ha"] / p["phase1_mw_it"]
    op, fixed, patch = (ledger[s][1] for s in ("operation", "substations", "largest"))
    module = p["halls_per_building"] * p["hall_mw_it"] + p["other_mw_it_per_building"]
    equipment = module * p["buildings"]
    reference = float(epoch["IT power (MW)"])
    facility = float(epoch["Power (MW)"])
    def config(g=grid, water=q, factor=k, slope=a, extra=0):
        return site_inputs(p, weather, g, water, factor, slope, op+extra, fixed)
    base = config()
    base["scenarios"] = base["scenarios"][:1]
    base["assessment_year"] = 2026
    base["period_note"] = "Original eight-building design; assessment stage November 2026"
    core = assess_site(base)["scenarios"][0]
    uncapped = core["P_mw_it"]
    plan = min(uncapped, equipment)
    plan_rows = []
    for name, val, detail in [
        ("halls_only",p["buildings"]*p["halls_per_building"]*p["hall_mw_it"], "design subtotal"),
        ("installed_it_design",equipment,"halls plus separately listed building IT"),
        ("resource_only_q1",uncapped,"electricity/water/land minimum"),
        ("fixed_plan_deliverable",plan,"minimum of configured equipment and resources"),
        ("epoch_2026-11-01_it",reference,"stage estimate; comparison only"),
        ("epoch_facility_divided_by_k",facility/k,"same-stage diagnostic; comparison only")]:
        plan_rows.append({"view": name, "mw_it": val, "difference_vs_epoch_mw": val-reference,
                          "difference_vs_epoch_pct": 100*(val/reference-1), "meaning": detail})
    write_csv(out, "plan.csv", plan_rows)
    plans = [{"scenario": "grid_as_planned", **{key:core[key] for key in
             ("P_E_mw_it","P_W_mw_it","P_L_mw_it","P_mw_it")}, "equipment_mw_it": equipment,
              "deliverable_mw_it": plan, "k": k, "grid_mw": grid, "water_proxy_m3_h": q,
              "it_lots_ha": op, "fixed_outside_lots_ha": fixed, "a_ha_mw_it": a}]
    write_csv(out, "plan_limits.csv", plans)
    portfolios = []
    for label, allowed in [("grid",set()),("coal",{"coal"}),("gas",{"gas"}),("wind",{"wind"}),
                           ("pv",{"pv"}),("renewables",{"wind","pv"}),("all",TECHS)]:
        win, branches = fit_portfolio(Mix, config(extra=patch), weather, patch, allowed)
        portfolios.append({"option":label,**win})
        if label=="all":
            write_csv(out,"integer_branches.csv",[dict(coal_units=c,gas_units=g,status=status,it_mw=val)
                                                  for c,g,status,val in branches])
    write_csv(out,"portfolio.csv",portfolios)
    best = portfolios[-1]
    assert all(best["it_mw"]+TOL>=r["it_mw"] for r in portfolios)
    assert abs(portfolios[0]["it_mw"]-uncapped)<TOL
    phase1_ha = p["phase1_leased_acres"] * p["acre_to_ha"]
    ex_post_slope = (op - phase1_ha) / (reference - p["phase1_mw_it"])
    anchored, _ = fit_portfolio(Mix, config(slope=ex_post_slope,extra=patch), weather, patch,
                                 TECHS, retained_it=equipment)
    used_patch = ex_post_slope*(anchored["it_mw"]-equipment) + anchored["gen_ha"]
    assert anchored["it_mw"] >= equipment-TOL and used_patch <= patch+TOL
    write_csv(out,"anchored_extension.csv",[{"retained_mw_it":equipment,"marginal_proxy_ha_mw_it":ex_post_slope,
              "increment_mw_it":anchored["it_mw"]-equipment,"used_patch_ha":used_patch, **anchored}])
    checks = validate_weather(p,portfolios[-2],grid,k)
    write_csv(out,"weather_check.csv",checks)
    sensitivity = []
    for gf,qf in [(g,w) for g in (.70,.80,.90,1.0) for w in (300.,400.,450.,500.,q)]:
        cfg=config(g=gf*p["grid_nameplate_mw"],water=qf,extra=patch)
        win,_=fit_portfolio(Mix,cfg,weather,patch,TECHS)
        sensitivity.append({"test":"grid_water","grid_mw":cfg["P_grid_mw"],"water_m3_h":qf,"k":k,"a_ha_mw_it":a,
                            "patch_ha":patch,"it_mw":win["it_mw"],"gas_mw":win["gas_mw"],"binding":win["binding"]})
    for name, factor, slope, area, only in [
            *(("annual_pue_as_k",x,a,patch,False) for x in (1.2,1.3,1.4)),
            *(("land_intensity",k,a*x,patch,False) for x in (.8,1.2)),
            *(("patch_budget",k,a,x,False) for x in (0,10,20)),
            ("patch_only_for_generation",k,a,patch,True)]:
        cfg=config(factor=factor,slope=slope,extra=area)
        win,_=fit_portfolio(Mix,cfg,weather,area,TECHS,op/slope if only else None)
        sensitivity.append({"test":name,"grid_mw":grid,"water_m3_h":q,"k":factor,"a_ha_mw_it":slope,
                            "patch_ha":area,"it_mw":win["it_mw"],"gas_mw":win["gas_mw"],"binding":win["binding"]})
    for row in sensitivity:
        row["wue_l_kwh_it"] = p["wue_l_kwh_it"]
    for site_wue in (.20, .80, 1.0):
        cfg = config(extra=patch)
        cfg["water"]["wue_l_per_kwh_it"] = site_wue
        win, _ = fit_portfolio(Mix, cfg, weather, patch, TECHS)
        sensitivity.append({"test":"site_wue","grid_mw":grid,"water_m3_h":q,"k":k,"a_ha_mw_it":a,
                            "patch_ha":patch,"it_mw":win["it_mw"],"gas_mw":win["gas_mw"],
                            "binding":win["binding"],"wue_l_kwh_it":site_wue})
    # Actual-plan hardware stays fixed in every sensitivity. A plot-area change only affects redesign.
    for row in sensitivity:
        trial = config(g=row["grid_mw"], water=row["water_m3_h"], factor=row["k"], slope=row["a_ha_mw_it"])
        trial["assessment_year"] = 2026
        trial["scenarios"] = trial["scenarios"][:1]
        trial["water"]["wue_l_per_kwh_it"] = row["wue_l_kwh_it"]
        raw_plan = assess_site(trial)["P_max_mw_it"]
        row["plan_resource_mw"] = raw_plan
        row["fixed_plan_mw"] = min(equipment, raw_plan)
    write_csv(out,"sensitivity.csv",sensitivity)
    summary={"source_commit":p["model_commit"],"module_mw":module,"reference_mw_it":reference,
             "reference_facility_mw":facility,"facility_ratio_diagnostic":facility/reference,
             "phase1_ha":p["phase1_leased_acres"]*p["acre_to_ha"],"slope":a,"calibration_mw":p["phase1_mw_it"],
             "lots_ha":op,"fixed_ha":fixed,"patch_ha":patch,"patch_drawn_ha":ledger["largest"][0],
             "water_m3_h":q,"plan_min_grid_mw":equipment*k,"plan_min_water_m3_h":equipment*p["wue_l_kwh_it"],
             "plan_grid_share_needed":equipment*k/p["grid_nameplate_mw"],
             "plan_resources_mw":uncapped,"plan_deliverable_mw":plan,
             "redesign_mw":best["it_mw"],"increment_over_plan_mw":best["it_mw"]-plan,
             "increment_over_resources_mw":best["it_mw"]-uncapped,"modules_possible":math.floor((best["it_mw"]+TOL)/module),
             "whole_module_mw":module*math.floor((best["it_mw"]+TOL)/module),
             "min_gas_for_winner_mw":max(0,k*best["it_mw"]-grid) if best["wind_mw"]+best["pv_mw"]<TOL and best["coal_mw"]<TOL else None,
             "epoch_power_to_it_mw":facility/k,"reference_gap_grid_rating_mw_it":(grid-facility)/k,
             "reference_gap_factor_mw_it":facility/k-reference,"weather_check":checks,"ex_post_slope":ex_post_slope,"anchored_extension_mw":anchored["it_mw"]}
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
