"""Run every numbered Q1 input in outputs and write a compact result table."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATA_ROOT.parent
OUTPUT_DIR = DATA_ROOT / "outputs"
sys.path.insert(0, str(REPO_ROOT / "code"))

from immc_power_capacity.app import calculate  # noqa: E402


CASE_OUTPUT_IDS = {
    "colossus1_2026": 19,
    "fairwater_atlanta_2026": 20,
    "fairwater_wisconsin_2026_public": 21,
    "fairwater_wisconsin_2028_epoch": 22,
    "hyperion_2028": 23,
    "hyperion_2030_5gw": 24,
    "new_carlisle_2028": 25,
    "stargate_abilene_2026": 26,
    "stargate_abilene_independent_2026": 31,
}
CASE_ROLES = {
    "colossus1_2026": "calibrated_consistency",
    "fairwater_atlanta_2026": "partly_calibrated",
    "fairwater_wisconsin_2026_public": "independent_power_with_local_ratio",
    "fairwater_wisconsin_2028_epoch": "circular_consistency",
    "hyperion_2028": "partly_calibrated",
    "hyperion_2030_5gw": "planning_scenario",
    "new_carlisle_2028": "partly_calibrated",
    "stargate_abilene_2026": "circular_consistency",
    "stargate_abilene_independent_2026": "independent_test",
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for config_path in sorted(OUTPUT_DIR.glob("*_input.yaml")):
        case = config_path.stem.split("_", 1)[1].removeprefix("q1_").removesuffix(
            "_input"
        )
        if case not in CASE_OUTPUT_IDS:
            raise ValueError(f"Unregistered Q1 input: {config_path.name}")
        report = calculate(config_path)
        winner_names = set(report["winners"])
        winners = [
            row for row in report["scenarios"] if row["name"] in winner_names
        ]
        winner = winners[0]
        finite_limits = {
            "电力": winner["P_E_mw_it"],
            "水": winner["P_W_mw_it"],
            "土地": winner["P_L_mw_it"],
        }
        near_binding = [
            name
            for name, value in finite_limits.items()
            if value is not None
            and value <= report["P_max_mw_it"] * 1.001 + 1e-9
        ]
        output_id = CASE_OUTPUT_IDS[case]
        output_path = OUTPUT_DIR / f"{output_id:02d}_q1_{case}_result.json"
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
            encoding="utf-8",
        )
        rows.append(
            {
                "case": case,
                "input_file": str(config_path.relative_to(REPO_ROOT)),
                "case_role": CASE_ROLES[case],
                "site": report["site"],
                "assessment_year": report["assessment_year"],
                "P_max_mw_it": report["P_max_mw_it"],
                "winner": " | ".join(report["winners"]),
                "P_E_mw_it": winner["P_E_mw_it"],
                "P_W_mw_it": winner["P_W_mw_it"],
                "P_L_mw_it": winner["P_L_mw_it"],
                "binding": " | ".join(winner["binding"]),
                "near_binding_within_0_1pct": " | ".join(near_binding),
                "k_factor": winner["breakdown"]["k"],
                "P_grid_mw": winner["breakdown"]["grid_mw"],
                "P_self_mw": winner["breakdown"]["self_generation_mw"],
                "A_effective_ha": winner["land"]["site_ha"],
                "A_fixed_it_ha": winner["land"]["fixed_it_ha"],
                "A_generation_ha": winner["land"]["generation_land_ha"],
                "water_limit_m3_h": report["water"]["Q_max_m3_h"],
                "generation_water_m3_h": winner["generation_water_m3_h"],
                "json_result": str(output_path.relative_to(REPO_ROOT)),
            }
        )

    output = OUTPUT_DIR / "09_q1_case_summary.csv"
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} case summaries to {output}")


if __name__ == "__main__":
    main()
