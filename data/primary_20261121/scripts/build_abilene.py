"""Legacy Abilene analysis, withdrawn pending primary design inputs.

The former workflow promoted a 1 GW engineering station figure to firm site
delivery and used assumed layout factors to calculate a site capacity. Those
outputs are not valid Q1 results. See outputs/15_validity_audit.csv.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parents[1]
INPUTS = BASE / "inputs"
OUTPUTS = BASE / "outputs"
sys.path.insert(0, str(ROOT / "code"))
from immc_power_capacity.app import calculate  # noqa: E402


ACRE_TO_HA = 0.40468564224
ACRE_FT_TO_M3 = 1233.48183754752
SQFT_TO_M2 = 0.09290304
US_GAL_TO_M3 = 0.003785411784
HOURS_PER_YEAR = 8760


def values(name):
    with (INPUTS / name).open(encoding="utf-8", newline="") as handle:
        return {row["key"]: float(row["value"]) for row in csv.DictReader(handle)}


def write_csv(name, fields, rows):
    with (OUTPUTS / name).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    raise SystemExit(
        "Abilene capacity outputs withdrawn: firm grid delivery and physical "
        "land-use intensity are not identified from primary inputs. See "
        "data/primary_20261121/outputs/15_validity_audit.csv."
    )

    # Retained below as historical implementation only; do not execute or cite.
    observations = values("01_abilene_observations.csv")
    assumptions = values("02_abilene_design_assumptions.csv")
    OUTPUTS.mkdir(parents=True, exist_ok=True)

    gross_ha = observations["campus_acres"] * ACRE_TO_HA
    station_ha = observations["new_substation_acres"] * ACRE_TO_HA
    floor_m2 = observations["total_building_sqft"] * SQFT_TO_M2
    # No reported IT MW enters this area intensity. All terms are geometry and rack design.
    floor_to_site_ratio = floor_m2 / (gross_ha * 10000)
    building_coverage = floor_to_site_ratio / assumptions["building_stories"]
    area_per_it_mw_ha = (
        assumptions["rack_cell_m2"]
        / assumptions["rack_rating_mw"]
        / assumptions["it_hall_fraction"]
        / floor_to_site_ratio
        / 10000
    )
    solar_density_mw_ac_km2 = (
        assumptions["solar_module_mw_dc"]
        / assumptions["solar_module_land_cell_m2"]
        * 1_000_000
        * assumptions["solar_ac_to_dc_ratio"]
    )
    supply_acft = sum(value for key, value in observations.items() if key.startswith("water_source_"))
    demand_acft = sum(value for key, value in observations.items()
                      if key.startswith(("water_demand_", "water_contract_", "water_strategy_")))
    # The two printed totals are audit controls only, never model inputs.
    if supply_acft != 45587 or demand_acft != 34116:
        raise ValueError(f"Region G component sums disagree with printed table: {supply_acft}, {demand_acft}")
    supply_minus_demands_acft = supply_acft - demand_acft
    if supply_minus_demands_acft < 0:
        raise ValueError("No nonnegative municipal planning margin")
    water_margin_m3_year = supply_minus_demands_acft * ACRE_FT_TO_M3
    annual_maintenance_m3 = (
        observations["buildings"]
        * observations["cooling_maintenance_gal_per_building_year"]
        * US_GAL_TO_M3
    )
    derived = [
        ("campus_gross_ha", gross_ha, "ha", "1100 acre * 0.40468564224"),
        ("substation_fixed_ha", station_ha, "ha", "12.5 acre * 0.40468564224"),
        ("planned_building_floor_m2", floor_m2, "m2", "4 million sqft * 0.09290304"),
        ("planned_floor_to_site_ratio", floor_to_site_ratio, "m2_floor/m2_site", "planned total floor area / gross site area"),
        ("building_coverage_if_one_story", building_coverage, "fraction", "floor area / gross site area / stories"),
        ("land_intensity_ha_per_mw_it", area_per_it_mw_ha, "ha/MW_IT", "rack cell / rack rating / IT hall fraction / planned floor-to-site ratio"),
        ("solar_density_mw_ac_km2", solar_density_mw_ac_km2, "MW_ac/km2", "600 W/module / 5 m2/module * 1e6 * 0.8 AC/DC"),
        ("municipal_supply_acft_year", supply_acft, "acre-ft/year", "sum five source rows; Table 5.33-2 control total 45587"),
        ("municipal_demands_acft_year", demand_acft, "acre-ft/year", "sum city, 17 contracts and 8 strategies; control total 34116"),
        ("municipal_supply_minus_demands_acft_year", supply_minus_demands_acft, "acre-ft/year", "source components minus demand components; conditional full-contract access"),
        ("municipal_planning_margin_m3_year", water_margin_m3_year, "m3/year", "supply minus demand * 1233.48183754752"),
        ("municipal_planning_margin_m3_h", water_margin_m3_year / HOURS_PER_YEAR, "m3/h", "annual planning margin / 8760; NOT hourly guarantee"),
        ("cooling_maintenance_m3_year", annual_maintenance_m3, "m3/year", "8 buildings * 12625 US gal/year * 0.003785411784"),
        ("water_fraction_needed_for_maintenance", annual_maintenance_m3 / water_margin_m3_year, "fraction", "fixed maintenance / gross planning margin"),
    ]
    write_csv("01_derived_physical_inputs.csv", ["quantity", "value", "unit", "calculation"], [
        dict(zip(["quantity", "value", "unit", "calculation"], row)) for row in derived
    ])

    config = {
        "model": "q1",
        "site": "Stargate Abilene, Texas - fully built eight-building campus",
        "assessment_year": int(assumptions["assessment_year"]),
        "period_note": "Static 2030 design night; annualized municipal margin assumed deliverable in that design condition",
        "service_level": "Normal operation at rated IT load; no N-1, no backup turbine counted",
        "P_grid_mw": observations["new_substation_mw"] * assumptions["grid_deliverable_fraction"],
        "k_factor": assumptions["k_design"],
        "water": {
            "basis": "withdrawal",
            "source_m3_h": water_margin_m3_year / HOURS_PER_YEAR * assumptions["water_accessible_fraction"],
            "wue_l_per_kwh_it": assumptions["cooling_variable_wue_l_per_kwh"],
        },
        "land": {
            "effective_ha": gross_ha * assumptions["effective_site_fraction"],
            "fixed_it_ha": station_ha,
            "ha_per_mw_it": area_per_it_mw_ha,
            "generation_land_ha": 0,
        },
        "scenarios": [
            {"name": "Grid plus non-evaporative cooling", "type": "grid"},
            {
                "name": "Counterfactual on-site PV without storage",
                "type": "solar", "online_year": 2030,
                "generation_land_ha": assumptions["solar_land_ha"],
                "area_km2": assumptions["solar_land_ha"] / 100,
                "density_mw_per_km2": solar_density_mw_ac_km2,
                "net_output_mw": [0.0],
                "dt_hours": 1,
            },
        ],
    }
    with (OUTPUTS / "02_abilene_static_input.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, allow_unicode=True, sort_keys=False)
    baseline = calculate(config, OUTPUTS / "03_abilene_static_result.json")
    if annual_maintenance_m3 > water_margin_m3_year:
        raise ValueError("Fixed cooling maintenance fails the planning-water screen")

    cases = []
    for k in (1.15, 1.30, 1.40):
        for site_fraction in (0.25, 0.50, 0.75, 1.00):
            candidate = json.loads(json.dumps(config))
            candidate["k_factor"] = k
            candidate["land"]["effective_ha"] = gross_ha * site_fraction
            report = calculate(candidate)
            row = report["scenarios"][0]
            cases.append({
                "k_design": k,
                "effective_site_fraction": site_fraction,
                "P_E_mw_it": round(row["P_E_mw_it"], 6),
                "P_W_mw_it": "" if row["P_W_mw_it"] is None else row["P_W_mw_it"],
                "P_L_mw_it": round(row["P_L_mw_it"], 6),
                "P_max_mw_it": round(report["P_max_mw_it"], 6),
                "binding": ";".join(row["binding"]),
                "classification": "conditional upper screen; no firm grid or site water right verified",
            })
    write_csv("04_design_sensitivity.csv", list(cases[0]), cases)

    land_crossover_rows = []
    for k in (1.15, 1.30, 1.40):
        electric_it_mw = observations["new_substation_mw"] * assumptions["grid_deliverable_fraction"] / k
        crossover_ha = station_ha + area_per_it_mw_ha * electric_it_mw
        crossover_fraction = crossover_ha / gross_ha
        land_crossover_rows.append({
            "k_design": k,
            "P_E_mw_it": electric_it_mw,
            "fixed_substation_land_ha": station_ha,
            "land_intensity_ha_per_mw_it": area_per_it_mw_ha,
            "effective_land_at_E_L_crossover_ha": crossover_ha,
            "effective_land_at_E_L_crossover_acres": crossover_ha / ACRE_TO_HA,
            "share_of_1100_acre_gross_site": crossover_fraction,
            "binding_rule": "land below crossover; electricity above crossover, conditional on grid and k assumptions",
        })
    write_csv("14_electric_land_crossover.csv", list(land_crossover_rows[0]), land_crossover_rows)

    technology_rows = []
    for row in baseline["scenarios"]:
        technology_rows.append({
            "scenario": row["name"],
            "status": "counterfactual design" if row["power_type"] == "solar" else "documented grid station conditional ceiling",
            "onsite_generation_area_ha": row["generation_land_ha"],
            "onsite_reliable_increment_mw": row["breakdown"]["self_generation_mw"],
            "P_E_mw_it": row["P_E_mw_it"],
            "P_L_mw_it": row["P_L_mw_it"],
            "P_mw_it": row["P_mw_it"],
            "interpretation": "zero night output; no firm increment and 50 ha site deduction" if row["power_type"] == "solar" else "base grid screen",
        })
    write_csv("10_pv_night_counterfactual.csv", list(technology_rows[0]), technology_rows)

    epoch_files = list(ROOT.glob("*/Q1-v2/IMMC2027-Q1/*/data_centers.csv"))
    if len(epoch_files) != 1:
        raise ValueError(f"Expected one Epoch snapshot, found {len(epoch_files)}")
    epoch_file = epoch_files[0]
    with epoch_file.open(encoding="utf-8-sig", newline="") as handle:
        epoch_rows = list(csv.DictReader(handle))
    observed = next(row for row in epoch_rows if row["Name"] == "OpenAI Stargate Abilene")
    observed_it = float(observed["Current power (MW)"])
    prediction = baseline["P_max_mw_it"]
    write_csv("05_observation_comparison.csv", [
        "site", "electric_land_screening_ceiling_mw_it", "epoch_current_mw_it", "difference_mw_it",
        "relative_difference_pct", "observed_used_as_input", "water_limit_status", "scope_warning",
    ], [{
        "site": observed["Name"],
        "electric_land_screening_ceiling_mw_it": prediction,
        "epoch_current_mw_it": observed_it,
        "difference_mw_it": prediction - observed_it,
        "relative_difference_pct": (prediction / observed_it - 1) * 100,
        "observed_used_as_input": "no",
        "water_limit_status": "unresolved; do not interpret screening ceiling as three-resource P_max",
        "scope_warning": "2030 completed campus electricity-land screen vs Epoch current estimate; temporal/stage mismatch",
    }])

    water_claims = [
        ("Oracle Abilene fact sheet", 12625, "US_gal/building/year", 8,
         "Abilene project; anticipated closed-loop cooling maintenance and quality water; 2025-09-23"),
        ("Crusoe Abilene project page", 50000, "US_gal/building/year", 8,
         "Abilene project; anticipated cooling-system maintenance; page dated 2025-08-05"),
        ("Crusoe 2026 Impact Report page", 910000, "US_gal/facility/year", "",
         "Generic 200 MW facility total annual water; page dated 2026-05-28; not identified as Abilene"),
        ("Crusoe 200 MW water stewardship diagram", 2000000, "US_gal/facility/year", "",
         "Generic illustrative facility total; diagram itemizes cooling maintenance, employee indoor and custodial use"),
    ]
    water_rows = []
    for source_name, gallons, unit, building_count, scope in water_claims:
        annual_gallons = gallons * building_count if building_count else gallons
        water_rows.append({
            "source": source_name,
            "published_value": gallons,
            "published_unit": unit,
            "building_count_multiplier": building_count,
            "derived_annual_gallons": annual_gallons,
            "derived_annual_m3": annual_gallons * US_GAL_TO_M3,
            "same_site_stage_and_scope_verified": "no",
            "interpretation": scope,
        })
    write_csv("12_water_source_reconciliation.csv", list(water_rows[0]), water_rows)

    equivalent_wue_rows = []
    for annual_water_gal, label in ((910000, "Crusoe 2026 impact page: 910000 gal/y"),
                                    (2000000, "Crusoe 2026 stewardship diagram: 2000000 gal/y")):
        water_m3 = annual_water_gal * US_GAL_TO_M3
        for pue in (1.2, 1.4):
            for load_fraction in (1.0, 0.75):
                it_capacity_mw = 200 / pue
                annual_it_energy_kwh = it_capacity_mw * load_fraction * HOURS_PER_YEAR * 1000
                equivalent_wue_rows.append({
                    "annual_water_source": label,
                    "annual_water_gal": annual_water_gal,
                    "facility_rating_mw": 200,
                    "pue": pue,
                    "assumed_it_load_fraction": load_fraction,
                    "implied_it_capacity_mw": it_capacity_mw,
                    "annual_it_energy_kwh": annual_it_energy_kwh,
                    "equivalent_wue_l_per_kwh": water_m3 * 1000 / annual_it_energy_kwh,
                    "classification": "illustrative Crusoe archetype ratio; not an Abilene parameter or design-hour WUE",
                })
    write_csv("13_crusoe_archetype_wue_sensitivity.csv", list(equivalent_wue_rows[0]), equivalent_wue_rows)

    task_targets = [
        ("950 MW example", 950, "task figure; facility versus IT boundary not specified"),
        ("2263 MW example", 2263, "task figure; site stage and boundary must be verified"),
        ("5 GW example", 5000, "Meta compute-capacity label; cannot assume IT MW"),
    ]
    write_csv("11_task_scale_comparison.csv", [
        "task_label", "stated_number_mw", "abilene_screen_mw_it", "numeric_ratio_only",
        "scope", "same_site_model_validation",
    ], [{
        "task_label": label,
        "stated_number_mw": amount,
        "abilene_screen_mw_it": prediction,
        "numeric_ratio_only": prediction / amount,
        "scope": scope,
        "same_site_model_validation": "no",
    } for label, amount, scope in task_targets])

    largest = sorted((row for row in epoch_rows if row["Current power (MW)"]),
                     key=lambda row: float(row["Current power (MW)"]), reverse=True)[:30]
    write_csv("06_epoch_top30_comparison_only.csv", [
        "rank", "name", "current_it_mw_estimate", "country", "address", "model_input",
    ], [{
        "rank": index, "name": row["Name"],
        "current_it_mw_estimate": row["Current power (MW)"],
        "country": row["Country"], "address": row["Address"], "model_input": "no",
    } for index, row in enumerate(largest, start=1)])

    sources = [
        ("ORACLE_2025", "raw/01_oracle_abilene_fact_sheet.pdf", "https://arrington.house.gov/uploadedfiles/final_oracle_oai_data_center_fact_sheet_092225b.pdf", "operator fact sheet via congressional host", "site geometry, cooling design, backup status"),
        ("MORTENSON_2026", "raw/02_mortenson_abilene.html", "https://www.mortenson.com/projects/abilene-data-center-development", "power delivery EPC contractor", "345 kV station nameplate, land and energization; firm import unknown"),
        ("REGION_G_2026", "raw/03_region_g_2026_water_plan.pdf", "https://www.twdb.texas.gov/waterplanning/rwp/plans/2026/G/RegionG_2026_RWP_VolumeI.pdf", "Texas regional water planning group / TWDB", "Table 5.33-2 supply and demand; annual planning not site entitlement"),
        ("META_RICHLAND", "raw/04_meta_richland.html", "https://datacenters.atmeta.com/richland-parish-data-center/", "operator project page", "cooling method and ambiguous 5 GW compute-capacity label"),
        ("CRUSOE_ABILENE_2025", "raw/07_crusoe_abilene_2025.html", "https://www.crusoe.ai/resources/blog/an-inside-look-at-the-abilene-ai-data-center", "Abilene operator/project developer page, 2025-08-05", "eight-building cooling design, initial fill and 50000 gallons/building/year maintenance estimate"),
        ("CRUSOE_IMPACT_2026", "raw/08_crusoe_impact_2026.html", "https://www.crusoe.ai/resources/blog/crusoes-2025-impact-report", "Crusoe 2025 impact report page, published 2026-05-28", "generic 200 MW archetype, 910000 gallons annual total and PUE range"),
        ("CRUSOE_WATER_2026", "raw/09_crusoe_water_stewardship_2026.html", "https://www.crusoe.ai/resources/blog/water-stewardship-at-our-data-centers", "Crusoe water stewardship page, 2026", "generic 200 MW illustrative water breakdown"),
        ("CRUSOE_200MW_WATER_IMAGE", "raw/10_crusoe_200mw_water_breakdown.png", "https://cdn.prod.website-files.com/6863cc86499b79ce3ab28f8b/6aa960a41ff716f5b57fe7e3_A_200_MW_Data_Center__3_uses_of_water_v2.png", "Crusoe-published illustration", "generic 200 MW annual-use breakdown; not Abilene measured data"),
        ("DAYONE_JOHOR", "raw/05_dayone_johor.html", "https://dayonedc.com/market/johor", "operator market page", "combined two-campus power figures conflict and are not single-site grid access"),
        ("DAYONE_WATER", "raw/06_dayone_water_johor.html", "https://dayonedc.com/headliners/dayone-expands-water-infrastructure-to-advance-johors-sustainable-growth", "operator water treatment announcement 2026-11-05", "Kempas Phase 2 20 million L/day plant expected Q3 2027; not river allocation"),
        ("MLGW_2025", "existing ref/34", "https://www.mlgw.com/images/content/files/pdf/new/5-5-25%20xAI%20Update.pdf", "Memphis utility update", "150 MW energized and second 150 MW contingent; not a full Colossus rating"),
        ("IMMC_TASK_A", "existing task PDF", "local competition problem PDF", "IMMC Greater China Autumn problem", "comparison numbers only; unit boundary not verified"),
        ("EPOCH_SNAPSHOT", "external epoch snapshot", "https://epoch.ai/data/ai-data-centers", "Epoch AI estimate", "comparison only; never supplies model parameters"),
    ]
    source_rows = []
    for identifier, relative_path, url, publisher, use in sources:
        if identifier == "EPOCH_SNAPSHOT":
            local = epoch_file
        elif identifier == "MLGW_2025":
            local = ROOT / "ref" / "34_MLGW2025_xAI_Power_Connection.pdf"
        elif identifier == "IMMC_TASK_A":
            matches = list(ROOT.glob("IMMC2027 Problems*/IMMC2027 Problem A*.pdf"))
            if len(matches) != 1:
                raise ValueError(f"Expected one task PDF, found {len(matches)}")
            local = matches[0]
        else:
            local = (BASE / relative_path).resolve()
        source_rows.append({
            "source_id": identifier, "path": str(local), "url": url,
            "publisher": publisher, "use": use,
            "sha256": hashlib.sha256(local.read_bytes()).hexdigest(),
        })
    write_csv("07_source_registry.csv", list(source_rows[0]), source_rows)

    gaps = [
        ("electricity", "1 GW station engineering rating is not firm import at site", "utility system impact study; transformer nameplates and simultaneous old/new station configuration"),
        ("water WUE", "no matched Abilene total onsite water and IT-energy pair; operator annual claims conflict", "project water-service/design records or same-stage, same-boundary annual water and IT-energy pair"),
        ("water delivery", "annual city planning margin is not a design-hour deliverable amount or project water right", "2030 project water-service contract; seasonal treatment and pumping capacity"),
        ("hydrology", "source-level planned yields do not reproduce reservoir streamflows, environmental flow and WAM allocation", "relevant reservoir safe-yield calculation and water-rights allocation records"),
        ("land", "1100 acres are gross and four million sqft are planned floor space", "parcel polygons, ecological and flood exclusions, floor counts, actual hall fraction"),
        ("efficiency", "full-load k=1.30 is a declared scenario", "same-condition facility and IT design power budget"),
        ("water model", "Abilene design WUE and P_W unresolved; reported 382 m3/year is expected cooling maintenance only", "same-boundary design water intensity and matching deliverable-water condition"),
        ("joint criterion", "769 MW is an electricity-land screening ceiling, not a verified three-resource maximum", "firm grid import, water WUE and allocation, effective parcel, design full-load k"),
        ("comparison", "Epoch current IT estimate is a different stage from 2030 completed campus", "dated matched-stage independently measured IT rating"),
    ]
    write_csv("08_evidence_gaps.csv", ["axis", "current_limit", "next_primary_record"], [
        dict(zip(["axis", "current_limit", "next_primary_record"], row)) for row in gaps
    ])

    inventory = [
        ("Stargate Abilene", "Texas, US", 1100, 8, 4000000, "1 GW 345 kV station engineering rating", "closed-loop non-evaporative; 12625 US gal/building/year maintenance", "ORACLE_2025;MORTENSON_2026;REGION_G_2026", "2030 completed design conditional Q1 case"),
        ("Stargate Shackelford", "Texas, US", 700, 10, 3700000, "behind-the-meter Jenbacher reciprocating gas engines; unit count and ratings undisclosed", "closed-loop chiller; no numerical water allowance", "ORACLE_2025", "missing engine inventory and independent supply and parcel screen"),
        ("Stargate Dona Ana", "New Mexico, US", 1400, 4, "", "independent Siemens/GE gas microgrid; unit count and ratings undisclosed", "closed-loop one-time fill; no available-water figure", "ORACLE_2025", "missing plant equipment and water and parcel screen"),
        ("Meta Hyperion", "Louisiana, US", "", "", "", "Entergy partnership; 5 GW compute-capacity label has no IT/plant boundary", "glycol closed-loop; dry cooling most of year", "META_RICHLAND", "missing physical grid rating, precise plot and water budget"),
        ("xAI Colossus", "Tennessee, US", "", "", "", "150 MW delivered at utility date; another 150 MW contingent", "", "MLGW_2025", "missing individual equipment rating, plant water and plot geometry"),
        ("DayOne Kempas Tech Park", "Johor, Malaysia", "", "", "", "Johor market page reports combined Nusajaya plus Kempas 390 MW in service and over 478 MW operational; no Kempas split", "self-treated river water; Phase 2 total plant 20 million L/day expected Q3 2027; source yield unverified", "DAYONE_JOHOR;DAYONE_WATER", "missing single-site power, river renewability, land and phase-matched water"),
    ]
    write_csv("09_primary_site_inventory.csv", [
        "site", "location", "gross_area_acres", "buildings", "planned_floor_sqft",
        "primary_power_detail", "primary_water_detail", "source_ids", "model_status",
    ], [
        dict(zip(["site", "location", "gross_area_acres", "buildings", "planned_floor_sqft",
                  "primary_power_detail", "primary_water_detail", "source_ids", "model_status"], row))
        for row in inventory
    ])

    entries = [
        ("00_output_index.csv", "script output manifest", "index of every numbered output", "generated with this run", "find inputs, meanings and conditions"),
        ("01_derived_physical_inputs.csv", "observations 01; assumptions 02", "raw geometry and water arithmetic to Q1 inputs", "2030 static completed campus; one-story design", "audit conversions and no target leakage"),
        ("02_abilene_static_input.yaml", "output 01", "Q1-v2 executable baseline configuration", "optimistic station, gross land, conditional municipal water", "rerun with code/run.py"),
        ("03_abilene_static_result.json", "output 02; code/immc_power_capacity", "conditional E/W/L screen", "P_W null because WUE is unidentified; displayed P_max is not a verified three-resource maximum", "inspect electric-land ceiling and unresolved water term"),
        ("04_design_sensitivity.csv", "output 02; independent k and usable land fractions", "nine static design sensitivities", "same year, site, water and service", "see uncertainty before comparison"),
        ("05_observation_comparison.csv", "output 03; Epoch snapshot", "electric-land screening ceiling vs current IT estimate", "water unresolved; different stages; not calibration", "compare scale without calling it a validated maximum"),
        ("06_epoch_top30_comparison_only.csv", "Epoch snapshot", "large-center comparison targets", "not inputs to Q1", "select future sites and benchmark scale"),
        ("07_source_registry.csv", "primary downloads and Epoch snapshot", "URLs and content hashes", "source versions at retrieval", "reproducibility"),
        ("08_evidence_gaps.csv", "outputs 01-05 and source scope", "missing primary evidence by axis", "conditional result", "prioritize next records"),
        ("09_primary_site_inventory.csv", "Oracle; Meta; Mortenson; MLGW; DayOne original publications", "published raw facts for six major campuses", "incomplete sites are not modeled", "investigate further primary records"),
        ("10_pv_night_counterfactual.csv", "output 02; independent module-area layout assumptions", "on-site PV without storage versus grid design-night capacity", "hypothetical PV, not built or permitted", "see renewable variability and land tradeoff"),
        ("11_task_scale_comparison.csv", "output 03; IMMC task examples", "numerical order-of-magnitude comparison only", "different geography/stage and unclear IT boundary", "meet prompt without circular validation"),
        ("12_water_source_reconciliation.csv", "Oracle and Crusoe operator disclosures", "comparison of annual water claims and scopes", "conflicting estimates; none is a matched design-hour Abilene WUE", "primary-source audit, not a model input"),
        ("13_crusoe_archetype_wue_sensitivity.csv", "Crusoe generic 200 MW annual-water and PUE claims", "algebraic equivalent-WUE sensitivity", "assumed PUE and IT load; archetype only, not Abilene", "illustrate denominator sensitivity; not calibration"),
        ("14_electric_land_crossover.csv", "outputs 01 and 02; Q1 electricity and land equations", "effective land share where P_E equals P_L", "conditional on 1 GW station delivery, k, and layout assumptions", "identify when land replaces electricity as the E-L bottleneck"),
    ]
    write_csv("00_output_index.csv", ["number", "file", "inputs", "meaning", "conditions", "use"], [
        dict(zip(["number", "file", "inputs", "meaning", "conditions", "use"],
                 (i, name, inputs, meaning, conditions, use)))
        for i, (name, inputs, meaning, conditions, use) in enumerate(entries)
    ])
    print(json.dumps({
        "P_E_mw_it": baseline["scenarios"][0]["P_E_mw_it"],
        "P_L_mw_it": baseline["scenarios"][0]["P_L_mw_it"],
        "P_W_mw_it": baseline["scenarios"][0]["P_W_mw_it"],
        "electric_land_screening_ceiling_mw_it": prediction,
        "three_resource_P_max_status": "unresolved; Abilene design WUE/site water delivery not established",
        "epoch_current_it_mw": observed_it,
        "annual_water_maintenance_m3": annual_maintenance_m3,
        "conditional_municipal_margin_m3_year": water_margin_m3_year,
        "crusoe_archetype_equivalent_wue_range_l_per_kwh": [
            round(row["equivalent_wue_l_per_kwh"], 6) for row in equivalent_wue_rows
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
