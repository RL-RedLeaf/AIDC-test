"""Independent bottom-up Q1 test.

Only physical inputs are used for prediction:
    P_E = (grid + normal onsite generation) / k
    P_W = annual water / (8760 * WUE)
    P_L = land area / land intensity
    P = min(P_E, P_W, P_L)

Reported project IT values are read only after the prediction to calculate
the comparison error.
"""

from __future__ import annotations

import csv
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = DATA_ROOT / "outputs"
INPUT_PATH = OUTPUT_DIR / "34_bottom_up_inputs.csv"
RESULT_PATH = OUTPUT_DIR / "35_bottom_up_results.csv"

K_LOW = 1.20
K_BASE = 1.30
K_HIGH = 1.40
LAND_INTENSITY_LOW = 0.15
LAND_INTENSITY_BASE = 0.26
LAND_INTENSITY_HIGH = 0.54


ROWS = [
    {
        "case_id": "fairwater_atlanta_public",
        "site": "Microsoft Fairwater Atlanta",
        "area_ha": 248.8844,
        "grid_mw": 1500,
        "normal_onsite_mw": 0,
        "annual_water_m3": 2763.3,
        "water_basis": "withdrawal",
        "wue_low": 0.00002,
        "wue_base": 0.0005,
        "wue_high": 0.001,
        "actual_current_it_mw": 636,
        "actual_planned_it_mw": "",
        "comparison_note": "1500 MW is campus power, not IT; current 636 MW is compared",
    },
    {
        "case_id": "fairwater_wisconsin_public",
        "site": "Microsoft Fairwater Wisconsin",
        "area_ha": 637.38,
        "grid_mw": 1000,
        "normal_onsite_mw": 0,
        "annual_water_m3": 31797,
        "water_basis": "withdrawal",
        "wue_low": 0.001,
        "wue_base": 0.005,
        "wue_high": 0.1,
        "actual_current_it_mw": 369,
        "actual_planned_it_mw": 2263,
        "comparison_note": "public 1000 MW scope versus Epoch 2263 MW expansion projection",
    },
    {
        "case_id": "new_carlisle_2200",
        "site": "Anthropic-Amazon New Carlisle",
        "area_ha": 485.6228,
        "grid_mw": 2200,
        "normal_onsite_mw": 0,
        "annual_water_m3": 68137,
        "water_basis": "withdrawal",
        "wue_low": 0.001,
        "wue_base": 0.005,
        "wue_high": 0.05,
        "actual_current_it_mw": 1037,
        "actual_planned_it_mw": 1925,
        "comparison_note": "public 2200 MW grid bound",
    },
    {
        "case_id": "abilene_1200",
        "site": "Stargate Abilene",
        "area_ha": 445.1542,
        "grid_mw": 1200,
        "normal_onsite_mw": 0,
        "annual_water_m3": 382.326590184,
        "water_basis": "consumption",
        "wue_low": 0.00001,
        "wue_base": 0.00005,
        "wue_high": 0.001,
        "actual_current_it_mw": 824,
        "actual_planned_it_mw": 824,
        "comparison_note": "1200 MW grid; 360.5 MW backup excluded",
    },
    {
        "case_id": "hyperion_phase_1800",
        "site": "Meta Hyperion first phase",
        "area_ha": 910.54,
        "grid_mw": 1800,
        "normal_onsite_mw": 0,
        "annual_water_m3": 1892706,
        "water_basis": "consumption",
        "wue_low": 0.03,
        "wue_base": 0.1,
        "wue_high": 0.15,
        "actual_current_it_mw": 0,
        "actual_planned_it_mw": 1632,
        "comparison_note": "MISO 1800 MW spot load; backup turbines excluded",
    },
    {
        "case_id": "hyperion_expansion_5278",
        "site": "Meta Hyperion long-term",
        "area_ha": 1294.9941,
        "grid_mw": 0,
        "normal_onsite_mw": 5278,
        "annual_water_m3": 2271247,
        "water_basis": "consumption",
        "wue_low": 0.03,
        "wue_base": 0.052,
        "wue_high": 0.15,
        "actual_current_it_mw": 0,
        "actual_planned_it_mw": "",
        "comparison_note": "seven 754 MW utility gas units; 5 GW is a different planning label",
    },
    {
        "case_id": "colossus1_572",
        "site": "Colossus 1",
        "area_ha": 87.8168,
        "grid_mw": 150,
        "normal_onsite_mw": 422,
        "annual_water_m3": 4145104.36,
        "water_basis": "withdrawal",
        "wue_low": 0.7,
        "wue_base": 1.0,
        "wue_high": 2.0,
        "actual_current_it_mw": 340,
        "actual_planned_it_mw": 340,
        "comparison_note": "150 MW grid plus 422 MW operating gas turbines; 3 MGD design withdrawal",
    },
    {
        "case_id": "colossus2_1200",
        "site": "Colossus 2",
        "area_ha": 40.4686,
        "grid_mw": 0,
        "normal_onsite_mw": 1200,
        "annual_water_m3": 6907979.94,
        "water_basis": "withdrawal",
        "wue_low": 0.7,
        "wue_base": 1.0,
        "wue_high": 2.0,
        "actual_current_it_mw": 946,
        "actual_planned_it_mw": 1531,
        "comparison_note": "1200 MW permitted Southaven turbine plant; land density may not transfer to vertical campus",
    },
]


def capacity_energy(row: dict[str, object], k: float) -> float:
    return (float(row["grid_mw"]) + float(row["normal_onsite_mw"])) / k


def capacity_water(row: dict[str, object], wue: float) -> float:
    return float(row["annual_water_m3"]) / (8760 * wue)


def capacity_land(row: dict[str, object], intensity: float) -> float:
    return float(row["area_ha"]) / intensity


def error_percent(prediction: float, actual: object) -> float | str:
    if actual == "" or actual is None or float(actual) == 0:
        return ""
    return (prediction / float(actual) - 1) * 100


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    input_fields = list(ROWS[0])
    with INPUT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=input_fields)
        writer.writeheader()
        writer.writerows(ROWS)

    results = []
    for row in ROWS:
        p_e_low = capacity_energy(row, K_HIGH)
        p_e_base = capacity_energy(row, K_BASE)
        p_e_high = capacity_energy(row, K_LOW)
        p_w_low = capacity_water(row, float(row["wue_high"]))
        p_w_base = capacity_water(row, float(row["wue_base"]))
        p_w_high = capacity_water(row, float(row["wue_low"]))
        p_l_low = capacity_land(row, LAND_INTENSITY_HIGH)
        p_l_base = capacity_land(row, LAND_INTENSITY_BASE)
        p_l_high = capacity_land(row, LAND_INTENSITY_LOW)
        base_constraints = {
            "energy": p_e_base,
            "water": p_w_base,
            "land": p_l_base,
        }
        envelope_low = min(p_e_low, p_w_low, p_l_low)
        envelope_high = min(p_e_high, p_w_high, p_l_high)
        p_base = min(base_constraints.values())
        binding = [
            name
            for name, value in base_constraints.items()
            if abs(value - p_base) < 1e-9
        ]
        results.append(
            {
                "case_id": row["case_id"],
                "site": row["site"],
                "P_E_low_mw": p_e_low,
                "P_E_base_mw": p_e_base,
                "P_E_high_mw": p_e_high,
                "P_W_low_mw": p_w_low,
                "P_W_base_mw": p_w_base,
                "P_W_high_mw": p_w_high,
                "P_L_low_mw": p_l_low,
                "P_L_base_mw": p_l_base,
                "P_L_high_mw": p_l_high,
                "P_base_mw": p_base,
                "binding_base": "|".join(binding),
                "P_envelope_low_mw": envelope_low,
                "P_envelope_high_mw": envelope_high,
                "actual_current_it_mw": row["actual_current_it_mw"],
                "actual_inside_envelope": (
                    ""
                    if row["actual_current_it_mw"] == ""
                    else envelope_low
                    <= float(row["actual_current_it_mw"])
                    <= envelope_high
                ),
                "error_current_percent": error_percent(
                    p_base, row["actual_current_it_mw"]
                ),
                "actual_planned_it_mw": row["actual_planned_it_mw"],
                "error_planned_percent": error_percent(
                    p_base, row["actual_planned_it_mw"]
                ),
                "comparison_note": row["comparison_note"],
            }
        )

    with RESULT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(ROWS)} independent cases and results")


if __name__ == "__main__":
    main()
