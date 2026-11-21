"""Exercise hourly generation and storage submodels for the Abilene test site."""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

import requests


DATA_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATA_ROOT.parent
OUTPUT_DIR = DATA_ROOT / "outputs"
HOURLY_PATH = OUTPUT_DIR / "36_abilene_hourly_resources_2025.csv"
RESULT_PATH = OUTPUT_DIR / "37_abilene_generation_submodels.csv"

sys.path.insert(0, str(REPO_ROOT / "code"))
from immc_power_capacity.core import solve_storage_capacity  # noqa: E402


URL = "https://power.larc.nasa.gov/api/temporal/hourly/point"
PARAMS = {
    "parameters": "T2M,ALLSKY_SFC_SW_DWN,WS2M",
    "community": "RE",
    "longitude": "-99.784",
    "latitude": "32.5",
    "start": "20250101",
    "end": "20251231",
    "format": "CSV",
}


def fetch_hourly() -> list[dict[str, str]]:
    response = requests.get(URL, params=PARAMS, timeout=60)
    response.raise_for_status()
    lines = response.text.splitlines()
    start = next(
        index for index, line in enumerate(lines) if line.startswith("YEAR,MO,DY")
    )
    rows = list(csv.DictReader(io.StringIO("\n".join(lines[start:]))))
    if len(rows) != 8760:
        raise ValueError(f"Expected 8760 hourly rows, received {len(rows)}")
    return rows


def pv_capacity_factor(irradiance_wh_m2: float, temperature_c: float) -> float:
    irradiance_kw_m2 = irradiance_wh_m2 / 1000
    cell_temperature = temperature_c + 20 * min(irradiance_kw_m2, 1)
    derated = irradiance_kw_m2 * 0.85 * (
        1 - 0.0035 * (cell_temperature - 25)
    )
    return max(0.0, min(1.0, derated))


def wind_capacity_factor(wind_2m_ms: float) -> float:
    hub_speed = wind_2m_ms * (100 / 2) ** 0.14
    if hub_speed < 3 or hub_speed > 25:
        return 0.0
    if hub_speed >= 12:
        return 0.9
    return 0.9 * (
        (hub_speed**3 - 3**3) / (12**3 - 3**3)
    )


def main() -> None:
    raw_rows = fetch_hourly()
    resource_rows = []
    solar_cf = []
    wind_cf = []
    for row in raw_rows:
        irradiance = float(row["ALLSKY_SFC_SW_DWN"])
        temperature = float(row["T2M"])
        wind = float(row["WS2M"])
        pv_cf = pv_capacity_factor(irradiance, temperature)
        wt_cf = wind_capacity_factor(wind)
        solar_cf.append(pv_cf)
        wind_cf.append(wt_cf)
        resource_rows.append(
            {
                **row,
                "wind_100m_ms": wind * (100 / 2) ** 0.14,
                "pv_capacity_factor": pv_cf,
                "wind_capacity_factor": wt_cf,
            }
        )
    with HOURLY_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(resource_rows[0]))
        writer.writeheader()
        writer.writerows(resource_rows)

    scenarios = [
        ("grid_only", 0, 0, "solar"),
        ("onsite_gas_360_5", 0, 360.5, "gas"),
        ("solar_100_acres", 40.4686, 0, "solar"),
        ("solar_200_acres", 80.9371, 0, "solar"),
        ("solar_400_acres", 161.8743, 0, "solar"),
        ("wind_100_acres", 40.4686, 0, "wind"),
        ("wind_400_acres", 161.8743, 0, "wind"),
    ]
    results = []
    for name, generation_ha, gas_mw, kind in scenarios:
        if kind == "solar" and generation_ha:
            installed_mw = generation_ha / 100 * 27.8
            supply = [installed_mw * value for value in solar_cf]
            firm_mw, _ = solve_storage_capacity(
                supply,
                1,
                0.5 * installed_mw,
                0.5 * installed_mw,
                2 * installed_mw,
                0.95,
                0.95,
            )
        elif kind == "wind" and generation_ha:
            installed_mw = generation_ha / 100 * 8
            supply = [installed_mw * value for value in wind_cf]
            firm_mw, _ = solve_storage_capacity(
                supply,
                1,
                0.5 * installed_mw,
                0.5 * installed_mw,
                2 * installed_mw,
                0.95,
                0.95,
            )
        else:
            installed_mw = gas_mw
            firm_mw = gas_mw

        facility_mw = 1200 + firm_mw
        p_e = facility_mw / 1.30
        available_land = 445.1542 - generation_ha
        p_l = available_land / 0.26
        generation_water = gas_mw * 0.0076
        available_water = 382.326590184 / 8760 - generation_water
        p_w = available_water / 0.00005
        p_max = min(p_e, p_w, p_l)
        results.append(
            {
                "scenario": name,
                "technology": kind,
                "generation_land_ha": generation_ha,
                "installed_mw": installed_mw,
                "firm_self_generation_mw": firm_mw,
                "facility_power_mw": facility_mw,
                "P_E_mw_it": p_e,
                "P_W_mw_it": p_w,
                "P_L_mw_it": p_l,
                "P_mw_it": p_max,
            }
        )

    with RESULT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"Wrote {len(resource_rows)} hourly rows and {len(results)} scenarios")


if __name__ == "__main__":
    main()
