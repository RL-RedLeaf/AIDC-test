"""Write the numbered index for every deliverable in data/outputs."""

from __future__ import annotations

import csv
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = DATA_ROOT / "outputs"
INDEX_PATH = OUTPUT_DIR / "00_output_index.csv"


ROWS = [
    {
        "output_id": "01",
        "filename": "01_epoch_latest_sites.csv",
        "category": "site_inventory",
        "source_inputs": "raw/epoch_data_centers_2026-11-21.csv;raw/epoch_data_center_timelines_2026-11-21.csv",
        "meaning": "96 Epoch sites with current record and latest overall record, IT/facility MW, k ratio, water use, and derived WUE",
        "conditions": "Snapshot 2026-11-21; latest overall record may be a future projection; blanks mean not reported",
        "use": "Site selection, scale screening, timeline comparison, and identification of public-data gaps",
        "confidence_status": "primary dataset plus derived fields",
    },
    {
        "output_id": "02",
        "filename": "02_epoch_top30_by_it_power.csv",
        "category": "ranking",
        "source_inputs": "outputs/01_epoch_latest_sites.csv",
        "meaning": "Top 30 sites sorted by the latest Epoch IT-power record",
        "conditions": "Ranking mixes current observations and future projections; record_scope distinguishes them",
        "use": "Rapid selection of the world's largest announced or operating AI campuses",
        "confidence_status": "derived ranking; not a sustainable-capacity ranking",
    },
    {
        "output_id": "03",
        "filename": "03_sites_master.csv",
        "category": "curated_site_data",
        "source_inputs": "Epoch CSV; Compute Atlas site records; MISO, MLGW, Oracle and municipal sources listed in 04",
        "meaning": "Seven deep-dive sites with coordinates, project phase, capacity scopes, grid context, cooling, water, land, and confidence",
        "conditions": "Values retain their source scope; site acreage is not yet ecologically screened effective land",
        "use": "Q1 model inputs, cross-site comparison, and source-level audit",
        "confidence_status": "mixed; per-site confidence column",
    },
    {
        "output_id": "04",
        "filename": "04_source_registry.csv",
        "category": "provenance",
        "source_inputs": "Public URLs, operator filings, utility filings, datasets, and peer-reviewed papers",
        "meaning": "Twenty-six source records with type, retrieval date, use, and scope notes",
        "conditions": "Source availability and page content can change; local evidence copies cover selected filings",
        "use": "Trace every material site parameter and technology factor",
        "confidence_status": "source index",
    },
    {
        "output_id": "05",
        "filename": "05_generation_technology_factors.csv",
        "category": "technology_parameters",
        "source_inputs": "Macknick 2012; Lovering 2022; NREL 2009/2013; outputs/04_source_registry.csv",
        "meaning": "Operational water and land factors for coal, gas, wind, and solar",
        "conditions": "Water factors depend on cooling; land factors separate direct footprint from project spacing and capacity from generation",
        "use": "Answer how water and land requirements change Q1 capacity across generation technologies",
        "confidence_status": "literature ranges and medians",
    },
    {
        "output_id": "06",
        "filename": "06_technology_tradeoff_summary.csv",
        "category": "derived_comparison",
        "source_inputs": "outputs/05_generation_technology_factors.csv",
        "meaning": "Compact L/kWh water and ha/TWh/year land comparison",
        "conditions": "Units are converted from the cited factors; blank land values mean not used in that row",
        "use": "Direct technology comparison and figure/table input",
        "confidence_status": "derived from 05",
    },
    {
        "output_id": "07",
        "filename": "07_reference_alignment.csv",
        "category": "validation_and_comparison",
        "source_inputs": "outputs/03_sites_master.csv;outputs/09_q1_case_summary.csv;question scale references",
        "meaning": "Scope-aligned comparison between reported scale and Q1 IT-capacity results",
        "conditions": "Reported MW must be interpreted as IT, facility, compute, or grid capacity according to the basis column",
        "use": "Answer whether estimates are higher or lower than 950 MW, 2263 MW, and 5 GW and explain differences",
        "confidence_status": "mixed; consistency cases are labeled",
    },
    {
        "output_id": "08",
        "filename": "08_data_quality_gaps.csv",
        "category": "limitations",
        "source_inputs": "Audit of outputs/03 and 04",
        "meaning": "Missing or ambiguous site inputs and their effects on Q1",
        "conditions": "Reflects public data available through 2026-11-21",
        "use": "Limit claims, design sensitivity analysis, and identify next source to pursue",
        "confidence_status": "audit record",
    },
    {
        "output_id": "09",
        "filename": "09_q1_case_summary.csv",
        "category": "model_summary",
        "source_inputs": "outputs/11-18 Q1 input YAML; code/immc_power_capacity",
        "meaning": "P_E, P_W, P_L, P_max, binding and near-binding constraints plus an explicit case role for nine cases",
        "conditions": "Normal operation, common site/period/service level, no N-1 requirement; source assumptions documented in each input",
        "use": "Main Q1 results table and comparison with real projects",
        "confidence_status": "model output with mixed input confidence",
    },
    {
        "output_id": "10",
        "filename": "10_sites.geojson",
        "category": "gis",
        "source_inputs": "outputs/03_sites_master.csv",
        "meaning": "WGS84 point layer for seven deep-dive sites",
        "conditions": "Points locate projects; they are not parcel or ecological-boundary polygons",
        "use": "Open in QGIS for map inspection and later overlay with parcels, transmission, water, and protected areas",
        "confidence_status": "site-center locator",
    },
    {
        "output_id": "11",
        "filename": "11_q1_colossus1_2026_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;outputs/04_source_registry.csv",
        "meaning": "Colossus 1 grid plus operating gas turbines and evaporative-water case",
        "conditions": "Withdrawal basis, 3 MGD design limit, 0.371 L/kWh WUE scenario, normal operation",
        "use": "Run or modify the Memphis Q1 case",
        "confidence_status": "medium; power/water inputs partly inferred from public reporting",
    },
    {
        "output_id": "12",
        "filename": "12_q1_fairwater_atlanta_2026_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;Microsoft;Georgia Power context in 04",
        "meaning": "Grid-only Fairwater Atlanta case",
        "conditions": "1500 MW planned campus power, almost-zero operating water scenario, no backup generation",
        "use": "Run or modify the Atlanta Q1 case",
        "confidence_status": "medium",
    },
    {
        "output_id": "13",
        "filename": "13_q1_fairwater_wisconsin_2026_public_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;WPR municipal records;Compute Atlas",
        "meaning": "Fairwater Wisconsin public full-campus capacity case",
        "conditions": "1000 MW public capacity; 8.4 million gal/year water budget; initial-site land intensity",
        "use": "Distinguish public campus scope from the Epoch expansion scope",
        "confidence_status": "medium-high",
    },
    {
        "output_id": "14",
        "filename": "14_q1_fairwater_wisconsin_2028_epoch_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;Epoch 11-building projection;WPR water record",
        "meaning": "Epoch 2263 MW IT expansion consistency case",
        "conditions": "2715 MW facility power projection; 8.4 million gal/year water budget",
        "use": "Quantify the Epoch expansion scope and water/electricity interaction",
        "confidence_status": "consistency scenario; not independent interconnection evidence",
    },
    {
        "output_id": "15",
        "filename": "15_q1_hyperion_2028_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;MISO 1800 MW spot load;Meta and Entergy context",
        "meaning": "Hyperion first-phase normal-operation case",
        "conditions": "1800 MW MISO load; backup turbines excluded; 500 million gal/year water scenario",
        "use": "Compare the normal-operation bound with Epoch and operator capacity descriptions",
        "confidence_status": "medium",
    },
    {
        "output_id": "16",
        "filename": "16_q1_hyperion_2030_5gw_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;Meta 5 GW statement;Entergy resource context",
        "meaning": "Hyperion 5 GW compute/campus expansion case",
        "conditions": "5000 MW assumed deliverable at campus; 600 million gal/year water; 3200 acres",
        "use": "Convert the 5 GW public label into a comparable IT-capacity result",
        "confidence_status": "scenario",
    },
    {
        "output_id": "17",
        "filename": "17_q1_new_carlisle_2028_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;Indiana project sources;Epoch expansion",
        "meaning": "Project Rainier full campus case",
        "conditions": "2200 MW public grid upper bound; 18 million gal/year water; 1200 acres",
        "use": "Test the Epoch 1925 MW plan against public grid and water budgets",
        "confidence_status": "medium-high",
    },
    {
        "output_id": "18",
        "filename": "18_q1_stargate_abilene_2026_input.yaml",
        "category": "q1_input",
        "source_inputs": "outputs/03_sites_master.csv;Oracle fact sheet;Epoch",
        "meaning": "Stargate Abilene eight-building grid case",
        "conditions": "1200 MW grid; closed-loop water; 360.5 MW backup gas excluded",
        "use": "Compare model IT capacity with Oracle and Epoch scale statements",
        "confidence_status": "medium-high",
    },
]


YAML_NAMES = [
    "colossus1_2026",
    "fairwater_atlanta_2026",
    "fairwater_wisconsin_2026_public",
    "fairwater_wisconsin_2028_epoch",
    "hyperion_2028",
    "hyperion_2030_5gw",
    "new_carlisle_2028",
    "stargate_abilene_2026",
]

for result_id, case in enumerate(YAML_NAMES, start=19):
    input_id = result_id - 8
    ROWS.append(
        {
            "output_id": f"{result_id:02d}",
            "filename": f"{result_id:02d}_q1_{case}_result.json",
            "category": "q1_result",
            "source_inputs": (
                f"outputs/{input_id:02d}_q1_{case}_input.yaml;"
                "code/immc_power_capacity"
            ),
            "meaning": "Full machine-readable Q1 report for this case",
            "conditions": "Uses the numbered input case and Q1-v2 implementation; normal operation without N-1",
            "use": "Audit P_E/P_W/P_L/P_max, binding constraints, assumptions, and plotting inputs",
            "confidence_status": "model output",
        }
    )

ROWS.extend(
    [
        {
            "output_id": "27",
            "filename": "27_water_stress_exact.csv",
            "category": "geospatial_water_context",
            "source_inputs": "WRI Aqueduct 4.0 ArcGIS FeatureServer; site coordinates in outputs/03",
            "meaning": "Exact point-in-polygon Aqueduct values: withdrawal-to-renewable-supply ratio, groundwater trend, and drought index",
            "conditions": "Basin-level baseline data, not site withdrawals, recharge measurements, or permit limits",
            "use": "Replace subjective low/medium/high wording with the actual basin values used for context",
            "confidence_status": "authoritative public dataset",
        },
        {
            "output_id": "28",
            "filename": "28_calibration_audit.csv",
            "category": "method_audit",
            "source_inputs": "outputs/03;outputs/09;Epoch time-line pairs",
            "meaning": "Explicit audit of which model inputs were reverse-engineered from the same site's reported IT capacity",
            "conditions": "A calibrated case tests arithmetic consistency only; it is not an out-of-sample prediction",
            "use": "Separate model validation from standard-answer reproduction",
            "confidence_status": "critical audit",
        },
        {
            "output_id": "29",
            "filename": "29_hyperion_plan_vs_model.csv",
            "category": "plan_comparison",
            "source_inputs": "MISO spot load; Epoch current and phase records; Meta 5 GW statement",
            "meaning": "Model IT ranges from current status, 1.8 GW grid, 5.278 GW new gas units, 5.7 GW transformer nameplate, and the 5 GW label",
            "conditions": "Ranges use independent 1.30-1.40 ratios; transformer nameplate is not N-1 firm capacity and backup turbines are excluded",
            "use": "Quantify how far the project plan is from normal-operation capacity and where the MW labels differ",
            "confidence_status": "scenario comparison",
        },
        {
            "output_id": "30",
            "filename": "30_q1_stargate_abilene_independent_2026_input.yaml",
            "category": "independent_q1_input",
            "source_inputs": "1200 MW public grid; 1100-acre site; Oracle annual cooling water; common 1.30 ratio; cross-site land intensity",
            "meaning": "Bottom-up Abilene test that does not use Epoch's Abilene IT value",
            "conditions": "Normal operation; backup gas excluded; basin and land inputs remain screening estimates",
            "use": "Out-of-sample test of whether the model can approach the real 824 MW scale",
            "confidence_status": "independent public-parameter scenario",
        },
        {
            "output_id": "31",
            "filename": "31_q1_stargate_abilene_independent_2026_result.json",
            "category": "independent_q1_result",
            "source_inputs": "outputs/30_q1_stargate_abilene_independent_2026_input.yaml;code/immc_power_capacity",
            "meaning": "Full bottom-up Abilene model result",
            "conditions": "Uses no Abilene-specific facility/IT ratio and no site IT target",
            "use": "Validate against the separately reported 824 MW IT estimate",
            "confidence_status": "independent model test",
        },
        {
            "output_id": "32",
            "filename": "32_abilene_nasa_power_2025.csv",
            "category": "site_specific_climate",
            "source_inputs": "NASA POWER API at 32.500 N, 99.784 W for calendar year 2025",
            "meaning": "365 daily site-specific temperature, solar irradiance, wind speed, and precipitation records",
            "conditions": "MERRA-2/CERES gridded reanalysis at approximately 0.5 by 0.625 degrees; not a local weather station",
            "use": "Assess renewable variability, high-temperature derating, and climate-specific assumptions at Abilene",
            "confidence_status": "authoritative gridded public data",
        },
        {
            "output_id": "33",
            "filename": "33_data_manifest.json",
            "category": "dataset_metadata",
            "source_inputs": "raw snapshots; evidence files; outputs/00-35",
            "meaning": "Dataset snapshot date, model positioning, hashes, derived-file list, and licensing notes",
            "conditions": "Hashes correspond to the 2026-11-21 snapshot; upstream content may change later",
            "use": "Verify provenance, reproduce the dataset, and audit immutable raw inputs",
            "confidence_status": "metadata",
        },
    ]
)

ROWS.extend(
    [
        {
            "output_id": "34",
            "filename": "34_bottom_up_inputs.csv",
            "category": "independent_model_inputs",
            "source_inputs": "Site area, public grid/generation capacity, public water budgets, external WUE and land-intensity ranges",
            "meaning": "Eight bottom-up cases containing only physical inputs; reported IT capacity is kept only as a separate comparison column",
            "conditions": "Global facility/IT ratio 1.30 with 1.20-1.40 sensitivity; land intensity 0.26 ha/MW with 0.15-0.54 sensitivity; WUE ranges are cooling-technology scenarios",
            "use": "Recompute every case without using the target IT result as an input",
            "confidence_status": "transparent scenario inputs with documented uncertainty",
        },
        {
            "output_id": "35",
            "filename": "35_bottom_up_results.csv",
            "category": "independent_model_results",
            "source_inputs": "outputs/34_bottom_up_inputs.csv",
            "meaning": "One-layer P_E, P_W, P_L and min result for each bottom-up case, plus envelope and comparison error",
            "conditions": "P_E=(grid+normal onsite)/k; P_W=annual water/(8760*WUE); P_L=area/land intensity; result=min",
            "use": "Model test against actual/planned IT, showing where the model is reliable and where the public inputs are insufficient",
            "confidence_status": "independent recomputation; ranges are scenario envelopes, not confidence intervals",
        },
    ]
)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ROWS[0]))
        writer.writeheader()
        writer.writerows(ROWS)
    missing = [
        row["filename"]
        for row in ROWS
        if not (OUTPUT_DIR / row["filename"]).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Indexed outputs are missing: {missing}")
    print(f"Wrote {len(ROWS)} indexed outputs to {INDEX_PATH}")


if __name__ == "__main__":
    main()
