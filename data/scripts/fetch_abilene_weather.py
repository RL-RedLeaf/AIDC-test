"""Fetch site-specific daily climate inputs for the Abilene public-data case."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import requests


DATA_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = DATA_ROOT / "outputs" / "32_abilene_nasa_power_2025.csv"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = {
    "parameters": "T2M,T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,WS2M,PRECTOTCORR",
    "community": "RE",
    "longitude": "-99.784",
    "latitude": "32.5",
    "start": "20250101",
    "end": "20251231",
    "format": "CSV",
}


def main() -> None:
    response = requests.get(URL, params=PARAMETERS, timeout=60)
    response.raise_for_status()
    lines = response.text.splitlines()
    start = next(
        index for index, line in enumerate(lines) if line.startswith("YEAR,MO,DY")
    )
    payload = "\n".join(lines[start:])
    rows = list(csv.DictReader(StringIO(payload)))
    if len(rows) != 365:
        raise ValueError(f"Expected 365 daily rows, received {len(rows)}")
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} daily weather rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
