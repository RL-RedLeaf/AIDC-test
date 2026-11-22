"""Run a geography-only Abilene PV-storage screening case with Q1 model."""

import csv
import json
import sys
from pathlib import Path

import yaml
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
CASE = Path(__file__).resolve().parent
RAW = CASE / "raw" / "open_meteo_abilene_2025-01-29.json"
OUT = CASE / "outputs"
sys.path.insert(0, str(ROOT / "code"))
from immc_power_capacity.core import assess_site  # noqa: E402


ACRE_TO_HA = 0.40468564224
ACRE_FT_TO_M3 = 1233.48183754752
HOURS_PER_YEAR = 8760


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    weather = json.loads(RAW.read_text(encoding="utf-8"))
    hourly = weather["hourly"]
    if len(hourly["time"]) != 24:
        raise ValueError("Design-day source must contain exactly 24 hourly records")
    month_weather = json.loads((CASE / "raw" / "open_meteo_abilene_2025-01_month.json").read_text(encoding="utf-8"))
    month_hourly = month_weather["hourly"]
    daily_sums = {}
    for timestamp, irradiance in zip(month_hourly["time"], month_hourly["shortwave_radiation"]):
        day = timestamp[:10]
        daily_sums[day] = daily_sums.get(day, 0.0) + irradiance
    selected_day = min(daily_sums, key=daily_sums.get)
    if selected_day != "2025-01-29":
        raise ValueError(f"Expected lowest-radiation January day 2025-01-29; got {selected_day}")
    selection_rows = [
        {"date": day, "daily_shortwave_Wh_m2": total,
         "rank_low_to_high": rank, "selected_design_day": day == selected_day}
        for rank, (day, total) in enumerate(sorted(daily_sums.items(), key=lambda item: item[1]), 1)
    ]
    write_csv(OUT / "08_design_day_selection.csv", selection_rows)

    # Translate hourly horizontal irradiation to AC output ratios for an explicitly
    # declared fixed-tilt performance ratio. Irradiance remains a saved source series.
    pr = 0.85
    noct_c = 45.0
    temperature_coefficient_per_c = -0.0035
    supply_ratio = []
    for ghi, ambient_c in zip(hourly["shortwave_radiation"], hourly["temperature_2m"]):
        cell_c = ambient_c + (noct_c - 20) * ghi / 800
        temperature_factor = max(0.0, 1 + temperature_coefficient_per_c * (cell_c - 25))
        supply_ratio.append(max(0.0, ghi / 1000 * pr * temperature_factor))
    gross_ha = 1100 * ACRE_TO_HA
    fixed_ha = 12.5 * ACRE_TO_HA
    floor_m2 = 4_000_000 * 0.09290304
    floor_site_ratio = floor_m2 / (gross_ha * 10_000)
    rack_cell_m2 = 6.0
    rack_mw = 0.1
    it_hall_fraction = 0.5
    a_site = (rack_cell_m2 / rack_mw / it_hall_fraction / floor_site_ratio) / 10_000

    pv_ha_per_mwac = 8.9 * ACRE_TO_HA
    pv_density = 100 / pv_ha_per_mwac  # MWac/km2
    regional_surplus_acft_y = 4496
    water_m3_h = regional_surplus_acft_y * ACRE_FT_TO_M3 / HOURS_PER_YEAR

    coarse_options = list(range(20, 401, 20))
    fine_options = [400 + step / 10 for step in range(0, 401)]
    pv_area_options_ha = sorted(set(coarse_options + fine_options))
    wind_area_options_ha = [100, 200, 300, 400]
    wind_ha_per_mw = 30.0  # midpoint reference scenario within 9-100 ha/MW spacing range
    wind_power_ratio = []
    for speed_kmh in hourly["wind_speed_10m"]:
        hub_speed = (speed_kmh / 3.6) * (100 / 10) ** (1 / 7)
        if hub_speed < 3 or hub_speed >= 25:
            ratio = 0.0
        elif hub_speed < 12:
            ratio = (hub_speed**3 - 3**3) / (12**3 - 3**3)
        else:
            ratio = 1.0
        wind_power_ratio.append(ratio)

    scenarios = [{
        "name": "电网供电",
        "type": "grid",
        "online_year": 2025,
        "generation_land_ha": 0,
    }]
    for area_ha in pv_area_options_ha:
        installed_mw = area_ha / pv_ha_per_mwac
        battery_power_mw = installed_mw / 4
        scenarios.append({
            "name": f"电网+光伏储能 {area_ha:.1f} ha",
            "type": "solar",
            "online_year": 2025,
            "area_km2": area_ha / 100,
            "density_mw_per_km2": pv_density,
            "supply_ratios": supply_ratio,
            "dt_hours": 1,
            "generation_land_ha": area_ha,
            "battery": {
                "C_max_mw": battery_power_mw,
                "D_max_mw": battery_power_mw,
                "E_usable_mwh": 4 * battery_power_mw,
                "charge_efficiency": 0.90,
                "discharge_efficiency": 0.90,
            },
        })
    for area_ha in wind_area_options_ha:
        installed_mw = area_ha / wind_ha_per_mw
        battery_power_mw = installed_mw / 4
        scenarios.append({
            "name": f"电网+风电储能 {area_ha} ha",
            "type": "combined_battery",
            "online_year": 2025,
            "installed_mw": installed_mw,
            "supply_series_mw": [installed_mw * ratio for ratio in wind_power_ratio],
            "dt_hours": 1,
            "generation_land_ha": area_ha,
            "generation_land_required_ha": area_ha,
            "battery": {
                "C_max_mw": battery_power_mw,
                "D_max_mw": battery_power_mw,
                "E_usable_mwh": 4 * battery_power_mw,
                "charge_efficiency": 0.90,
                "discharge_efficiency": 0.90,
            },
        })
    for units in (1, 2):
        scenarios.append({
            "name": f"电网+燃气（干冷）{units}×100 MW",
            "type": "gas",
            "online_year": 2025,
            "units": units,
            "unit_net_mw": 100,
            "unit_land_ha": 10,
            "generation_land_ha": 10 * units,
            "net_efficiency": 0.50,
            "generation_water_l_per_kwh": 0.02,
        })
        scenarios.append({
            "name": f"电网+燃煤（湿冷）{units}×100 MW",
            "type": "coal",
            "online_year": 2025,
            "units": units,
            "unit_net_mw": 100,
            "unit_land_ha": 20,
            "generation_land_ha": 20 * units,
            "net_efficiency": 0.38,
            "generation_water_l_per_kwh": 132.5,
        })

    def build_config(grid_mw):
        return {
            "model": "q1",
            "site": "Abilene geographic resource envelope; generic grid-access scenario, no project capacity input",
            "assessment_year": 2025,
            "period_note": "2025-01-29 local hourly solar/wind design cycle repeated; static 24 h cycle",
            "service_level": "normal operation, constant rated IT load; no N-1",
            "P_grid_mw": grid_mw,
            "k_factor": 1.41,
            "water": {
                "basis": "withdrawal",
                "source_m3_h": water_m3_h,
                "wue_l_per_kwh_it": 0.5,
            },
            "land": {
                "effective_ha": gross_ha,
                "fixed_it_ha": fixed_ha,
                "ha_per_mw_it": a_site,
                "generation_land_ha": 0,
            },
            "scenarios": json.loads(json.dumps(scenarios)),
        }

    base_grid_mw = 100.0  # illustrative firm grid-import level; no local interconnection rating is asserted
    config = build_config(base_grid_mw)
    result = assess_site(config)
    (OUT / "01_q1_inputs.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (OUT / "02_q1_optimized_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    candidate_rows = []
    for row in result["scenarios"]:
        battery = row["method"].get("battery") or {}
        candidate_rows.append({
            "candidate": row["name"],
            "technology": row["power_type"],
            "generation_land_ha": row["generation_land_ha"],
            "installed_generation_MW": row["method"].get(
                "installed_mw", row["method"].get("units", 0) * row["method"].get("unit_net_mw", 0)
            ),
            "battery_usable_MWh": battery.get("E_usable_mwh", 0.0),
            "P_self_reliable_MW": row["self_generation_used_mw"],
            "P_E_MW_IT": row["P_E_mw_it"],
            "P_W_MW_IT": row["P_W_mw_it"],
            "P_L_MW_IT": row["P_L_mw_it"],
            "P_joint_MW_IT": row["P_mw_it"],
            "binding": ";".join(row["binding"]),
            "optimizer": row["method"].get("status", "not applicable"),
        })
    write_csv(OUT / "03_candidate_allocation_results.csv", candidate_rows)

    weather_rows = []
    for time, ghi, temp, wind, ratio in zip(
        hourly["time"], hourly["shortwave_radiation"], hourly["temperature_2m"],
        hourly["wind_speed_10m"], supply_ratio,
    ):
        hub_speed = (wind / 3.6) * (100 / 10) ** (1 / 7)
        weather_rows.append({
            "local_time": time,
            "shortwave_W_m2": ghi,
            "temperature_C": temp,
            "wind_speed_10m_km_h": wind,
            "wind_speed_100m_estimate_m_s": hub_speed,
            "wind_turbine_power_ratio_assumed": wind_power_ratio[len(weather_rows)],
            "PV_AC_supply_ratio_PR_0_85_temp_adjusted": ratio,
        })
    write_csv(OUT / "04_design_day_weather_to_PV.csv", weather_rows)

    # Sensitivity varies global/reference design parameters without target calibration.
    sensitivity_rows = []
    for k in (1.20, 1.41, 1.54):
        for land_factor in (0.5, 1.0, 2.0):
            candidate = json.loads(json.dumps(config))
            candidate["k_factor"] = k
            candidate["land"]["ha_per_mw_it"] = a_site * land_factor
            report = assess_site(candidate)
            winner = max(report["scenarios"], key=lambda item: item["P_mw_it"])
            sensitivity_rows.append({
                "k_factor": k,
                "a_site_multiple": land_factor,
                "optimal_candidate": winner["name"],
                "P_E_MW_IT": winner["P_E_mw_it"],
                "P_W_MW_IT": winner["P_W_mw_it"],
                "P_L_MW_IT": winner["P_L_mw_it"],
                "P_joint_MW_IT": report["P_max_mw_it"],
                "binding": ";".join(winner["binding"]),
            })
    write_csv(OUT / "05_reference_sensitivity.csv", sensitivity_rows)

    grid_rows = []
    for grid_mw in (0, 25, 50, 100, 250):
        report = assess_site(build_config(float(grid_mw)))
        best = max(report["scenarios"], key=lambda item: item["P_mw_it"])
        grid_only = next(item for item in report["scenarios"] if item["power_type"] == "grid_only")
        pv_best = max((item for item in report["scenarios"] if item["name"].startswith("电网+光伏")),
                      key=lambda item: item["P_mw_it"])
        wind_best = max((item for item in report["scenarios"] if item["name"].startswith("电网+风电")),
                        key=lambda item: item["P_mw_it"])
        gas_best = max((item for item in report["scenarios"] if item["power_type"] == "gas"),
                       key=lambda item: item["P_mw_it"])
        coal_best = max((item for item in report["scenarios"] if item["power_type"] == "coal"),
                        key=lambda item: item["P_mw_it"])
        grid_rows.append({
            "assumed_firm_grid_MW": grid_mw,
            "grid_only_MW_IT": grid_only["P_mw_it"],
            "best_grid_PV_MW_IT": pv_best["P_mw_it"],
            "best_grid_wind_MW_IT": wind_best["P_mw_it"],
            "best_grid_gas_MW_IT": gas_best["P_mw_it"],
            "best_grid_coal_MW_IT": coal_best["P_mw_it"],
            "best_portfolio": best["name"],
            "best_joint_MW_IT": report["P_max_mw_it"],
            "binding": ";".join(best["binding"]),
            "classification": "illustrative grid-delivery sensitivity; not a local utility commitment",
        })
    write_csv(OUT / "11_grid_access_sensitivity.csv", grid_rows)

    sources = [
        {"source_id": "OPEN_METEO_ERA5", "local_file": "raw/open_meteo_abilene_2025-01_month.json; raw/open_meteo_abilene_2025-01-29.json", "source_url": "https://archive-api.open-meteo.com/v1/archive?latitude=32.442883&longitude=-99.7327&start_date=2025-01-01&end_date=2025-01-31&hourly=shortwave_radiation,temperature_2m,wind_speed_10m&timezone=America%2FChicago", "publisher": "Open-Meteo Historical Weather API; ERA5 reanalysis grid", "used_for": "Abilene location, January hourly series for design-day selection, and selected day radiation/temperature/wind", "boundary_or_caveat": "gridded reanalysis, not a ground pyranometer; selected one design cycle only"},
        {"source_id": "IEA_2025_PUE", "local_file": "research/A题模型/电力子模型_全量文献审阅.md; ref/24_IEA2025_Energy_and_AI.pdf", "source_url": "https://www.iea.org/reports/energy-and-ai", "publisher": "International Energy Agency", "used_for": "2024 global average PUE=1.41, used as k proxy", "boundary_or_caveat": "annual average is not local full-load design PUE"},
        {"source_id": "NREL_SOLAR_LAND", "local_file": "ref/17_NREL2013_Solar_Land_Use.pdf", "source_url": "https://www.nrel.gov/docs/fy13osti/56290.pdf", "publisher": "National Renewable Energy Laboratory", "used_for": "total solar plant land benchmark 8.9 acres/MWac", "boundary_or_caveat": "total site area, not direct module footprint"},
        {"source_id": "NREL_WIND_LAND", "local_file": "ref/18_NREL2009_Wind_Land_Use.pdf; research/A题模型/电力子模型_全量文献审阅.md", "source_url": "https://www.nrel.gov/docs/fy09osti/45834.pdf", "publisher": "National Renewable Energy Laboratory", "used_for": "wind farm spacing reference range 9-100 ha/MW; use 30 ha/MW scenario", "boundary_or_caveat": "30 ha/MW is an illustrative mid-range assumption, not Abilene project layout"},
        {"source_id": "WUE_REFERENCE", "local_file": "research/A题模型/参数资料/参数汇总表.md; ref/12_Siddik2021_US_Data_Center_Footprints.pdf", "source_url": "https://doi.org/10.1016/j.resconrec.2020.105226", "publisher": "Siddik et al., Resources, Conservation & Recycling, 2021; local parameter review", "used_for": "closed-loop/liquid cooling WUE reference range; choose 0.5 L/kWh", "boundary_or_caveat": "reference range, not global sample mean nor Abilene design WUE"},
        {"source_id": "ABILENE_GEOMETRY", "local_file": "data/primary_20261121/inputs/01_abilene_observations.csv; raw/01_oracle_abilene_fact_sheet.pdf", "source_url": "https://arrington.house.gov/uploadedfiles/final_oracle_oai_data_center_fact_sheet_092225b.pdf", "publisher": "Oracle project fact sheet", "used_for": "candidate geography boundary 1100 acres and approx. 4 million sqft total floor area only", "boundary_or_caveat": "no IT MW, building count or campus power is input to this experiment"},
        {"source_id": "REGION_G_WATER", "local_file": "data/primary_20261121/raw/03_region_g_2026_water_plan.pdf", "source_url": "https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/G/RegionG_2026_RWP_VolumeI.pdf", "publisher": "Texas Water Development Board / Region G", "used_for": "DB27 2030 projected surplus 4496 acre-ft/year, annualized for Q1 water budget", "boundary_or_caveat": "hypothetical full allocation to this case; not a site contract or hourly guarantee"},
        {"source_id": "LAYOUT_REFERENCE", "local_file": "research/A题模型/参数资料/参数汇总表.md", "source_url": "https://www.iea.org/reports/energy-and-ai", "publisher": "Engineering scenario based on 100 kW/rack reference and declared layout fractions", "used_for": "a_site=0.143748 ha/MW_IT calculation", "boundary_or_caveat": "hybrid geometry/layout proxy, not a global mean; rack cell=6 m2 and IT hall fraction=0.5 are explicit assumptions"},
        {"source_id": "PV_BATTERY_DESIGN", "local_file": "run_case.py", "source_url": "analyst-declared scenario; no local design record", "publisher": "Engineering scenario assumption", "used_for": "PR=0.85, NOCT=45 C, temperature coefficient=-0.0035/C, charge/discharge efficiency=0.90, 4 h battery duration", "boundary_or_caveat": "not a measured or global mean value; vary in sensitivity analysis"},
        {"source_id": "GRID_ACCESS_SCENARIO", "local_file": "run_case.py; outputs/11_grid_access_sensitivity.csv", "source_url": "illustrative grid import levels 0, 25, 50, 100, 250 MW", "publisher": "Analyst-declared scenario axis", "used_for": "compare grid-only, grid+PV storage and grid+wind storage at identical firm grid import", "boundary_or_caveat": "not a measured Abilene utility deliverability or project interconnection rating"},
        {"source_id": "WIND_POWER_CURVE_SCENARIO", "local_file": "run_case.py", "source_url": "generic power-curve and 1/7 wind shear assumptions", "publisher": "Engineering scenario assumption", "used_for": "10 m wind speed extrapolated to 100 m; cut-in 3, rated 12, cut-out 25 m/s", "boundary_or_caveat": "not a selected manufacturer's turbine curve; one reanalysis design day only"},
        {"source_id": "THERMAL_SCENARIOS", "local_file": "run_case.py", "source_url": "analyst-declared generic 100 MW blocks; Macknick et al. water factors in local reference table", "publisher": "Generic engineering scenarios plus literature water reference", "used_for": "gas dry-cooling and coal wet-cooling comparison under the model's fuel-sufficient upper-bound assumption", "boundary_or_caveat": "block ratings and land areas are scenario values; fuel delivery is not a model input; coal withdrawal factor is a high reference value"},
    ]
    write_csv(OUT / "06_source_registry.csv", sources)

    pv_rows = [row for row in candidate_rows if row["candidate"].startswith("电网+光伏储能")]
    areas = [float(row["generation_land_ha"]) for row in pv_rows]
    electric = [float(row["P_E_MW_IT"]) for row in pv_rows]
    land = [float(row["P_L_MW_IT"]) for row in pv_rows]
    joint = [float(row["P_joint_MW_IT"]) for row in pv_rows]
    best_index = max(range(len(joint)), key=joint.__getitem__)
    grid_only_row = next(row for row in candidate_rows if row["candidate"] == "电网供电")
    pv_best_area = areas[best_index]
    pv_best_electric = electric[best_index]
    pv_best_land = land[best_index]
    pv_best_joint = joint[best_index]
    close_rows = [(area, pe, pl, capacity) for area, pe, pl, capacity in zip(areas, electric, land, joint)
                  if pv_best_area - 10 <= area <= pv_best_area + 10]
    plt.rcParams.update({
        "font.family": "Microsoft YaHei",
        "font.size": 9,
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
    })
    fig, (left, right) = plt.subplots(1, 2, figsize=(10.6, 4.0), constrained_layout=True)
    fig.suptitle(
        f"Abilene 地理资源案例：假设电网 {base_grid_mw:.0f} MW；全组合最优 {result['winners'][0]}",
        fontsize=11,
    )
    left.plot(areas, electric, color="#376d9a", linewidth=1.8, label="电网+光储电力上限 $P_E$")
    left.axhline(float(grid_only_row["P_E_MW_IT"]), color="#59636b", linestyle="--",
                 linewidth=1.2, label="纯电网上限")
    left.set(xlabel="发电用地 $A_e$（ha）", ylabel="电力上限 $P_E$（MW IT）",
             title="（a）电网基准与光储增量")
    left.set_xlim(0, 440)
    left.set_ylim(float(grid_only_row["P_E_MW_IT"]) - 0.5, max(electric) + 0.5)
    left.grid(alpha=0.22)
    left.legend(frameon=False, fontsize=8)
    left.text(0.03, 0.96, f"水上限 $P_W$ = {water_m3_h / 0.5:.0f} MW IT",
              transform=left.transAxes, va="top", color="#328a79", fontsize=8)
    close_areas, close_electric, close_land, close_joint = map(list, zip(*close_rows))
    right.plot(close_areas, close_electric, color="#376d9a", linewidth=1.8, label="电力上限 $P_E$")
    right.plot(close_areas, close_land, color="#cc7d36", linewidth=1.8, label="土地上限 $P_L$")
    right.plot(close_areas, close_joint, color="#36434c", linewidth=1.8, label="联合容量 $P$")
    right.axhline(float(grid_only_row["P_E_MW_IT"]), color="#59636b", linestyle="--",
                  linewidth=1.0, label="纯电网容量")
    right.axvline(pv_best_area, color="#59636b", linestyle=":", linewidth=1.1)
    right.scatter([pv_best_area], [pv_best_joint], color="#bd4938", zorder=3,
                  label=f"光储候选最优 {pv_best_joint:.3f} MW IT")
    right.set(xlabel="发电用地 $A_e$（ha）", ylabel="容量上限（MW IT）",
              title="（b）光储候选附近的瓶颈切换")
    right.set_xlim(min(close_areas), max(close_areas))
    right.set_ylim(0, max(close_electric) * 1.15)
    right.grid(alpha=0.22)
    right.legend(frameon=False, fontsize=7.5, ncol=2)
    fig.savefig(OUT / "07_allocation_optimization.png", dpi=240)
    fig.savefig(OUT / "07_allocation_optimization.svg")
    plt.close(fig)

    # Sensitivity heatmaps optimize the PV branch only so conditional thermal
    # blocks do not dominate the geographic resource interaction.
    grid_levels = [0, 25, 50, 75, 100, 150, 200, 250]
    land_fractions = [0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 1.00]
    effective_land_levels_ha = [gross_ha * fraction for fraction in land_fractions]
    land_edges_ha = np.array([
        max(0.0, effective_land_levels_ha[0] -
            (effective_land_levels_ha[1] - effective_land_levels_ha[0]) / 2),
        *[(effective_land_levels_ha[i] + effective_land_levels_ha[i + 1]) / 2
          for i in range(len(effective_land_levels_ha) - 1)],
        effective_land_levels_ha[-1] +
        (effective_land_levels_ha[-1] - effective_land_levels_ha[-2]) / 2,
    ])
    k_levels = [1.20, 1.41, 1.54]
    pv_shares = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]
    heatmap_rows = []
    heatmap_lookup = {}
    for k_value in k_levels:
        for land_fraction in land_fractions:
            effective_ha = gross_ha * land_fraction
            generation_budget_ha = max(0.0, effective_ha - fixed_ha)
            heatmap_scenarios = [{
                "name": "电网供电",
                "type": "grid",
                "online_year": 2025,
                "generation_land_ha": 0,
            }]
            for share in pv_shares:
                pv_area_ha = generation_budget_ha * share
                if pv_area_ha <= 0:
                    continue
                installed_mw = pv_area_ha / pv_ha_per_mwac
                battery_power_mw = installed_mw / 4
                heatmap_scenarios.append({
                    "name": f"电网+光储 {share:.0%} 可分配地",
                    "type": "solar",
                    "online_year": 2025,
                    "area_km2": pv_area_ha / 100,
                    "density_mw_per_km2": pv_density,
                    "supply_ratios": supply_ratio,
                    "dt_hours": 1,
                    "generation_land_ha": pv_area_ha,
                    "battery": {
                        "C_max_mw": battery_power_mw,
                        "D_max_mw": battery_power_mw,
                        "E_usable_mwh": 4 * battery_power_mw,
                        "charge_efficiency": 0.90,
                        "discharge_efficiency": 0.90,
                    },
                })
            for grid_mw in grid_levels:
                hm_config = {
                    "model": "q1",
                    "site": "Abilene geography heatmap; grid+PV branch only",
                    "assessment_year": 2025,
                    "period_note": "2025-01-29 static repeated design cycle",
                    "service_level": "normal operation, constant rated IT load; no N-1",
                    "P_grid_mw": grid_mw,
                    "k_factor": k_value,
                    "water": config["water"],
                    "land": {
                        "effective_ha": effective_ha,
                        "fixed_it_ha": fixed_ha,
                        "ha_per_mw_it": a_site,
                        "generation_land_ha": 0,
                    },
                    "scenarios": heatmap_scenarios,
                }
                hm_report = assess_site(hm_config)
                hm_winner = max(hm_report["scenarios"], key=lambda item: item["P_mw_it"])
                pv_selected = hm_winner["generation_land_ha"] if hm_winner["power_type"] != "grid_only" else 0.0
                first_binding = hm_winner["binding"][0]
                record = {
                    "k_factor": k_value,
                    "assumed_firm_grid_MW": grid_mw,
                    "effective_land_share": land_fraction,
                    "effective_land_ha": effective_ha,
                    "optimal_candidate": hm_winner["name"],
                    "optimal_PV_land_ha": pv_selected,
                    "P_E_MW_IT": hm_winner["P_E_mw_it"],
                    "P_W_MW_IT": hm_winner["P_W_mw_it"],
                    "P_L_MW_IT": hm_winner["P_L_mw_it"],
                    "P_joint_MW_IT": hm_report["P_max_mw_it"],
                    "binding": ";".join(hm_winner["binding"]),
                }
                heatmap_rows.append(record)
                heatmap_lookup[(k_value, land_fraction, grid_mw)] = record
    write_csv(OUT / "12_geography_heatmap_data.csv", heatmap_rows)

    grid_edges = np.array([-12.5, 12.5, 37.5, 62.5, 87.5, 125, 175, 225, 275])
    base_k = 1.41
    values = np.array([
        [heatmap_lookup[(base_k, land_fraction, grid_mw)]["P_joint_MW_IT"]
         for grid_mw in grid_levels]
        for land_fraction in land_fractions
    ])
    fig, ax = plt.subplots(figsize=(8.3, 5.0), constrained_layout=True)
    image = ax.pcolormesh(grid_edges, land_edges_ha, values, cmap="YlGnBu", shading="flat")
    levels = [level for level in (25, 50, 75, 100, 150)
              if values.min() < level < values.max()]
    if levels:
        contours = ax.contour(grid_levels, effective_land_levels_ha, values, levels=levels,
                               colors="#28343d", linewidths=0.8)
        ax.clabel(contours, inline=True, fontsize=8, fmt="%.0f MW")
    ax.set_title("电网与有效土地对光储可持续容量的影响（k=1.41）")
    ax.set_xlabel("电网可持续功率 P电网（MW）")
    ax.set_ylabel("有效可用土地 A_eff（ha）")
    ax.set_xticks(grid_levels)
    ax.set_yticks(effective_land_levels_ha, [f"{area:.0f}" for area in effective_land_levels_ha])
    fig.colorbar(image, ax=ax, label="最优联合容量（MW IT）", shrink=0.88)
    fig.savefig(OUT / "13_grid_land_capacity_heatmap.png", dpi=240)
    fig.savefig(OUT / "13_grid_land_capacity_heatmap.svg")
    plt.close(fig)

    selected_area = np.array([
        [heatmap_lookup[(base_k, land_fraction, grid_mw)]["optimal_PV_land_ha"]
         for grid_mw in grid_levels]
        for land_fraction in land_fractions
    ])
    capacity_gain = np.array([
        [heatmap_lookup[(base_k, land_fraction, grid_mw)]["P_joint_MW_IT"] - grid_mw / base_k
         for grid_mw in grid_levels]
        for land_fraction in land_fractions
    ])
    fig, (allocation_ax, binding_ax) = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    allocation_image = allocation_ax.pcolormesh(grid_edges, land_edges_ha, selected_area,
                                                  cmap="magma", shading="flat")
    allocation_ax.set_title("最优发电用地 A_e（ha）")
    allocation_ax.set_xlabel("电网可持续功率 P电网（MW）")
    allocation_ax.set_ylabel("有效可用土地 A_eff（ha）")
    allocation_ax.set_xticks(grid_levels)
    allocation_ax.set_yticks(effective_land_levels_ha, [f"{area:.0f}" for area in effective_land_levels_ha])
    fig.colorbar(allocation_image, ax=allocation_ax, label="PV 用地（ha）", shrink=0.86)
    gain_image = binding_ax.pcolormesh(grid_edges, land_edges_ha, capacity_gain,
                                       cmap="YlGnBu", shading="flat")
    binding_ax.set_title("光储相对纯电网的容量增益，k=1.41")
    binding_ax.set_xlabel("电网可持续功率 P电网（MW）")
    binding_ax.set_xticks(grid_levels)
    binding_ax.set_yticks(effective_land_levels_ha, [f"{area:.0f}" for area in effective_land_levels_ha])
    fig.colorbar(gain_image, ax=binding_ax, label="较纯电网增加的联合容量（MW IT）", shrink=0.86)
    fig.suptitle("电网与土地情景下的光伏配置和瓶颈分布", fontsize=12)
    fig.savefig(OUT / "14_optimal_pv_gain_heatmap.png", dpi=240, bbox_inches="tight")
    fig.savefig(OUT / "14_optimal_pv_gain_heatmap.svg", bbox_inches="tight")
    plt.close(fig)

    # Q1 explicitly compares how different generation technologies change
    # water and land constraints under locally varying grid access.
    water_levels = [0, 100, 300, 633.0747, 1000, 1500, 2000]
    water_edges = [0, 50, 200, 466.5, (633.0747 + 1000) / 2,
                   1250, 1750, 2250]
    technology_names = ["网电+光储", "网电+风储", "网电+燃气", "网电+燃煤"]
    water_lookup = {}
    water_rows = []
    for technology in technology_names:
        for q_source in water_levels:
            for grid_mw in grid_levels:
                water_scenarios = [{
                    "name": "电网供电",
                    "type": "grid",
                    "online_year": 2025,
                    "generation_land_ha": 0,
                }]
                if technology == "网电+光储":
                    available_generation_land = max(0, gross_ha - fixed_ha)
                    for share in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
                        pv_area_ha = available_generation_land * share
                        installed_mw = pv_area_ha / pv_ha_per_mwac
                        battery_power_mw = installed_mw / 4
                        water_scenarios.append({
                            "name": f"光储 {share:.0%} 发电用地",
                            "type": "solar",
                            "online_year": 2025,
                            "area_km2": pv_area_ha / 100,
                            "density_mw_per_km2": pv_density,
                            "supply_ratios": supply_ratio,
                            "dt_hours": 1,
                            "generation_land_ha": pv_area_ha,
                            "battery": {
                                "C_max_mw": battery_power_mw,
                                "D_max_mw": battery_power_mw,
                                "E_usable_mwh": 4 * battery_power_mw,
                                "charge_efficiency": 0.90,
                                "discharge_efficiency": 0.90,
                            },
                        })
                elif technology == "网电+风储":
                    for area_ha in wind_area_options_ha:
                        installed_mw = area_ha / wind_ha_per_mw
                        battery_power_mw = installed_mw / 4
                        water_scenarios.append({
                            "name": f"风储 {area_ha} ha",
                            "type": "combined_battery",
                            "online_year": 2025,
                            "installed_mw": installed_mw,
                            "supply_series_mw": [installed_mw * ratio for ratio in wind_power_ratio],
                            "dt_hours": 1,
                            "generation_land_ha": area_ha,
                            "generation_land_required_ha": area_ha,
                            "battery": {
                                "C_max_mw": battery_power_mw,
                                "D_max_mw": battery_power_mw,
                                "E_usable_mwh": 4 * battery_power_mw,
                                "charge_efficiency": 0.90,
                                "discharge_efficiency": 0.90,
                            },
                        })
                else:
                    source_type = "gas" if technology == "网电+燃气" else "coal"
                    source_row = max(
                        (row for row in result["scenarios"] if row["power_type"] == source_type),
                        key=lambda row: row["P_mw_it"],
                    )
                    source_name = source_row["name"]
                    thermal_spec = next(spec for spec in config["scenarios"]
                                        if spec["name"] == source_name)
                    water_scenarios.append(json.loads(json.dumps(thermal_spec)))

                hm_config = {
                    "model": "q1",
                    "site": f"Abilene geography water-grid heatmap: {technology}",
                    "assessment_year": 2025,
                    "period_note": "2025-01-29 static repeated design cycle; water allowance varied as a scenario",
                    "service_level": "normal operation, constant rated IT load; no N-1",
                    "P_grid_mw": grid_mw,
                    "k_factor": 1.41,
                    "water": {
                        "basis": "withdrawal",
                        "source_m3_h": q_source,
                        "wue_l_per_kwh_it": 0.5,
                    },
                    "land": {
                        "effective_ha": gross_ha,
                        "fixed_it_ha": fixed_ha,
                        "ha_per_mw_it": a_site,
                        "generation_land_ha": 0,
                    },
                    "scenarios": water_scenarios,
                }
                water_report = assess_site(hm_config)
                water_winner = max(water_report["scenarios"], key=lambda item: item["P_mw_it"])
                record = {
                    "technology_branch": technology,
                    "assumed_firm_grid_MW": grid_mw,
                    "source_water_allowance_m3_h": q_source,
                    "optimal_candidate": water_winner["name"],
                    "P_E_MW_IT": water_winner["P_E_mw_it"],
                    "P_W_MW_IT": water_winner["P_W_mw_it"],
                    "P_L_MW_IT": water_winner["P_L_mw_it"],
                    "P_joint_MW_IT": water_report["P_max_mw_it"],
                    "binding": ";".join(water_winner["binding"]),
                }
                water_rows.append(record)
                water_lookup[(technology, q_source, grid_mw)] = record
    write_csv(OUT / "15_grid_water_technology.csv", water_rows)

    water_fig, water_axes = plt.subplots(2, 2, figsize=(10.5, 7.0), constrained_layout=True)
    water_fig.suptitle("电网交付与水量补给对不同发电方案的联合约束", fontsize=13)
    water_values = np.array([
        water_lookup[(technology, q_source, grid_mw)]["P_joint_MW_IT"]
        for technology in technology_names
        for q_source in water_levels for grid_mw in grid_levels
    ])
    water_vmax = float(np.max(water_values))
    water_grid_edges = grid_edges
    for ax, technology in zip(water_axes.flat, technology_names):
        values = np.array([
            [water_lookup[(technology, q_source, grid_mw)]["P_joint_MW_IT"]
             for grid_mw in grid_levels]
            for q_source in water_levels
        ])
        mesh = ax.pcolormesh(water_grid_edges, water_edges, values, cmap="YlGnBu",
                             vmin=0, vmax=water_vmax, shading="flat")
        ax.axhline(633.0747, color="#c34c36", linestyle="--", linewidth=1.0)
        ax.set_title(technology)
        ax.set_xlabel("电网可持续功率 P电网（MW）")
        ax.set_xticks(grid_levels)
        ax.set_yticks(water_levels, [f"{value:.0f}" if value != 633.0747 else "633" for value in water_levels])
    water_axes[0, 0].set_ylabel("水源可供量 Q_DC,max（m³/h）")
    water_axes[1, 0].set_ylabel("水源可供量 Q_DC,max（m³/h）")
    water_fig.colorbar(mesh, ax=water_axes.ravel().tolist(), label="最优联合容量（MW IT）", shrink=0.88)
    water_fig.savefig(OUT / "16_grid_water_technology_heatmap.png", dpi=240)
    water_fig.savefig(OUT / "16_grid_water_technology_heatmap.svg")
    plt.close(water_fig)

    # Isolate the competition lead-time mechanism specified in the task.
    # Grid, PV, wind and coal candidates are held available; only gas modules
    # receive the problem's illustrative seven-year wait from a 2025 start.
    timeline_source_names = [
        "电网供电",
        max((row for row in result["scenarios"] if row["power_type"] == "solar_storage"),
            key=lambda row: row["P_mw_it"])["name"],
        max((row for row in result["scenarios"] if row["power_type"] == "combined_renewables"),
            key=lambda row: row["P_mw_it"])["name"],
        max((row for row in result["scenarios"] if row["power_type"] == "coal"),
            key=lambda row: row["P_mw_it"])["name"],
        max((row for row in result["scenarios"] if row["power_type"] == "gas"),
            key=lambda row: row["P_mw_it"])["name"],
    ]
    timeline_scenarios = []
    for name in timeline_source_names:
        spec = next(spec for spec in config["scenarios"] if spec["name"] == name)
        spec = json.loads(json.dumps(spec))
        spec["online_year"] = 2032 if spec["type"] == "gas" else 2025
        timeline_scenarios.append(spec)
    timeline_rows = []
    for year in (2025, 2027, 2029, 2030, 2031, 2032, 2033, 2035):
        timeline_config = json.loads(json.dumps(config))
        timeline_config["assessment_year"] = year
        timeline_config["scenarios"] = json.loads(json.dumps(timeline_scenarios))
        timeline_report = assess_site(timeline_config)
        timeline_winner = max(timeline_report["scenarios"], key=lambda item: item["P_mw_it"])
        timeline_rows.append({
            "assessment_year": year,
            "P_max_MW_IT": timeline_report["P_max_mw_it"],
            "winner": timeline_winner["name"],
            "binding": ";".join(timeline_winner["binding"]),
            "gas_online_year_assumed": 2032,
            "assumption": "only gas availability is time-gated; other candidates held available",
        })
    write_csv(OUT / "17_generation_leadtime.csv", timeline_rows)
    timeline_years = [row["assessment_year"] for row in timeline_rows]
    timeline_capacity = [row["P_max_MW_IT"] for row in timeline_rows]
    fig, ax = plt.subplots(figsize=(8.0, 4.4), constrained_layout=True)
    ax.step(timeline_years, timeline_capacity, where="post", color="#346f9d", linewidth=2.2)
    ax.scatter(timeline_years, timeline_capacity, color="#c54e3e", zorder=3)
    ax.axvline(2032, color="#707b83", linestyle="--", linewidth=1.1)
    ax.annotate("燃气方案投运年份 y_x=2032\n（评估年份 y 从 2025 起算，等待 7 年）",
                xy=(2032, max(timeline_capacity)), xytext=(2028.8, max(timeline_capacity) * 0.78),
                arrowprops={"arrowstyle": "->", "color": "#707b83"}, fontsize=9)
    ax.set(title="只改变候选设施投运状态的静态可用性情景",
           xlabel="评估年份 y",
           ylabel="当年最大容量 P_max(y)（MW IT）")
    ax.set_xticks(timeline_years)
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(OUT / "18_generation_leadtime.png", dpi=240)
    fig.savefig(OUT / "18_generation_leadtime.svg")
    plt.close(fig)

    index_rows = [
        {"编号": "00", "文件": "00_output_index.csv", "输入": "全部输出", "意义": "输出索引", "条件": "Abilene 单一地理情景", "用途": "追溯输入与输出"},
        {"编号": "01", "文件": "01_q1_inputs.yaml", "输入": "气象、地块几何、全球参考值、区域水计划", "意义": "可执行 Q1 输入", "条件": "P_grid 基准 100 MW；2025-01-29 重复日循环", "用途": "复算模型"},
        {"编号": "02", "文件": "02_q1_optimized_result.json", "输入": "输出 01、Q1 核心代码、SciPy 线性规划", "意义": "电网、光储、风储、燃气和燃煤的最优候选", "条件": "条件性地理筛查，不代表实际项目；火电按模型燃料充分上界", "用途": "读取容量与瓶颈"},
        {"编号": "03", "文件": "03_candidate_allocation_results.csv", "输入": "输出 01；PV 20–380 ha 粗网格及 400–440 ha 的 0.1 ha 网格，并含风电/火电候选", "意义": "各候选方案的 Q1 求解结果", "条件": "电网+风光储能及条件性火电模块", "用途": "检查能源组合的优化选择"},
        {"编号": "04", "文件": "04_design_day_weather_to_PV.csv", "输入": "Open-Meteo 设计日逐小时 JSON", "意义": "气象到光伏/风电出力的换算", "条件": "24 h；PV 温度修正与 10→100 m 风速外推均为情景参数", "用途": "核查可再生能源时序输入"},
        {"编号": "05", "文件": "05_reference_sensitivity.csv", "输入": "同一设计日；改变 k 与 a_site", "意义": "全球参考值与布局系数敏感性", "条件": "未进行反向标定", "用途": "检查参数影响"},
        {"编号": "06", "文件": "06_source_registry.csv", "输入": "保存的数据源及出版资料", "意义": "输入来源与限制", "条件": "地理资料加明示全球/工程参考假设", "用途": "审核参数依据"},
        {"编号": "07", "文件": "../raw/open_meteo_abilene_2025-01-29.json", "输入": "Open-Meteo Archive API", "意义": "逐小时辐射、温度与风速原始响应", "条件": "Abilene 网格点；2025-01-29 当地时间", "用途": "追溯地理气象数据"},
        {"编号": "08", "文件": "08_design_day_selection.csv", "输入": "raw/open_meteo_abilene_2025-01_month.json", "意义": "每日辐射总量及选择 1 月 29 日的依据", "条件": "2025 年 1 月；按当地时间汇总", "用途": "复核设计日选择"},
        {"编号": "09", "文件": "07_allocation_optimization.png; 07_allocation_optimization.svg", "输入": "输出 03 与各候选约束上限", "意义": "电网基准、光储电力增量及容量曲线", "条件": "假设电网可持续交付 100 MW；其他电网值见输出 11", "用途": "解释电力曲线斜率与约束切换"},
        {"编号": "10", "文件": "10_geographic_case_report.md", "输入": "输出 01–09、11 与来源表", "意义": "地理结果、图解、合理性和模型评估", "条件": "Abilene 静态情景；不反向标定", "用途": "解释计算结果及局限"},
        {"编号": "11", "文件": "11_grid_access_sensitivity.csv", "输入": "同一地理资源；网电 0、25、50、100、250 MW 情景", "意义": "电网、光储、风储、燃气与燃煤组合对比", "条件": "电网值为参考情景，不是当地接入承诺；燃料充分按模型上界", "用途": "检查不同供电途径与接入水平"},
        {"编号": "12", "文件": "12_geography_heatmap_data.csv", "输入": "Abilene 气象循环、土地比例、k 与电网水平网格", "意义": "网电+光储分支每个参数格点的最优配置和容量", "条件": "PV 子分支；每格枚举光伏用地份额", "用途": "复核热力图底层数据"},
        {"编号": "13", "文件": "13_grid_land_capacity_heatmap.png; 13_grid_land_capacity_heatmap.svg", "输入": "网电可持续供电、有效可用土地情景；输出 12", "意义": "光储方案容量对电力与土地条件的响应面", "条件": "基准 k=1.41；等值线为联合 IT 容量", "用途": "比较两项地理资源约束"},
        {"编号": "14", "文件": "14_optimal_pv_gain_heatmap.png; 14_optimal_pv_gain_heatmap.svg", "输入": "网电可持续供电、有效可用土地情景；输出 12", "意义": "最优发电用地分配及相对纯电网的容量增益", "条件": "k=1.41；网电+光储方案", "用途": "观察配置变化与光储增量"},
        {"编号": "15", "文件": "15_grid_water_technology.csv", "输入": "同一设计日、技术方案、电网与供水情景", "意义": "网电/水量二维网格下各技术的最优容量和瓶颈", "条件": "PV、风、燃气、燃煤分支；水量为情景值", "用途": "复核水-电热力图底层数据"},
        {"编号": "16", "文件": "16_grid_water_technology_heatmap.png; 16_grid_water_technology_heatmap.svg", "输入": "输出 15", "意义": "网电交付和补水量对四类能源组合容量的影响", "条件": "k=1.41；红虚线为 Region G 规划水量折算值", "用途": "对比能源技术的水-电瓶颈"},
        {"编号": "17", "文件": "17_generation_leadtime.csv", "输入": "纯电网及已选光储、风储、燃气、燃煤候选", "意义": "按发电设施投运年份筛选候选方案", "条件": "2025 起算，燃气按题面 7 年示例于 2032 可用", "用途": "解释建成等待期如何筛选候选集"},
        {"编号": "18", "文件": "18_generation_leadtime.png; 18_generation_leadtime.svg", "输入": "输出 17", "意义": "候选集容量随投运年份的阶梯图", "条件": "其他资源固定；不是逐年资源仿真", "用途": "可视化建设等待期影响"},
    ]
    write_csv(OUT / "00_output_index.csv", index_rows)
    print(json.dumps({
        "design_day": "2025-01-29",
        "ghi_Wh_m2": sum(hourly["shortwave_radiation"]),
        "global_water_reference_m3_h": water_m3_h,
        "a_site_ha_per_mw_it": a_site,
        "P_max_MW_IT": result["P_max_mw_it"],
        "winner": result["winners"],
        "optimizer": max(result["scenarios"], key=lambda item: item["P_mw_it"])
        ["method"].get("status", "not applicable"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
