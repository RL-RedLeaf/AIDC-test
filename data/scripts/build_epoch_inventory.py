"""Build a site-level inventory from the raw Epoch AI CSV snapshot.

The Epoch timeline contains both historical observations and future
projections. This script keeps the latest record for every site and keeps
the record date so downstream users can judge whether it is a current
observation or a projection.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DATE = date(2026, 11, 21)
SITES_PATH = DATA_ROOT / "raw" / "epoch_data_centers_2026-11-21.csv"
TIMELINES_PATH = (
    DATA_ROOT / "raw" / "epoch_data_center_timelines_2026-11-21.csv"
)
OUTPUT_DIR = DATA_ROOT / "outputs"
LATEST_OUTPUT = OUTPUT_DIR / "01_epoch_latest_sites.csv"
TOP_OUTPUT = OUTPUT_DIR / "02_epoch_top30_by_it_power.csv"
MASTER_PATH = OUTPUT_DIR / "03_sites_master.csv"
GEOJSON_OUTPUT = OUTPUT_DIR / "10_sites.geojson"


def number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def latest_records(
    rows: list[dict[str, str]], *, cutoff: date | None = None
) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        record_date = date.fromisoformat(row["Date"])
        if cutoff is not None and record_date > cutoff:
            continue
        site = row["Data center"]
        current = latest.get(site)
        key = (
            record_date,
            number(row.get("Buildings operational")) or 0.0,
            number(row.get("IT power (MW)")) or 0.0,
        )
        if current is None:
            latest[site] = row
            continue
        current_key = (
            date.fromisoformat(current["Date"]),
            number(current.get("Buildings operational")) or 0.0,
            number(current.get("IT power (MW)")) or 0.0,
        )
        if key > current_key:
            latest[site] = row
    return latest


def build_rows() -> list[dict[str, object]]:
    sites = {row["Name"]: row for row in load_csv(SITES_PATH)}
    timeline_rows = load_csv(TIMELINES_PATH)
    latest = latest_records(timeline_rows)
    current = latest_records(timeline_rows, cutoff=SNAPSHOT_DATE)
    records: list[dict[str, object]] = []

    for site_name, site in sites.items():
        timeline = latest.get(site_name, {})
        current_timeline = current.get(site_name, {})
        it_mw = number(timeline.get("IT power (MW)"))
        facility_mw = number(timeline.get("Power (MW)"))
        water_mgd = number(timeline.get("Water use (MGD)"))
        current_it_mw = number(current_timeline.get("IT power (MW)"))
        current_facility_mw = number(current_timeline.get("Power (MW)"))
        current_water_mgd = number(current_timeline.get("Water use (MGD)"))
        record_date = timeline.get("Date")
        k_ratio = None
        if it_mw and facility_mw:
            k_ratio = facility_mw / it_mw
        wue = None
        if it_mw and water_mgd is not None:
            # MGD -> L/day; IT MW -> kWh/day.
            wue = water_mgd * 3_785_411.784 / (it_mw * 24_000)
        current_k_ratio = None
        if current_it_mw and current_facility_mw:
            current_k_ratio = current_facility_mw / current_it_mw
        current_wue = None
        if current_it_mw and current_water_mgd is not None:
            current_wue = (
                current_water_mgd
                * 3_785_411.784
                / (current_it_mw * 24_000)
            )

        records.append(
            {
                "site_id": site_name.lower().replace(" ", "_"),
                "site_name": site_name,
                "owner": site.get("Owner", ""),
                "project": site.get("Project", ""),
                "country": site.get("Country", ""),
                "address": site.get("Address", ""),
                "energy_companies": site.get("Energy companies", ""),
                "latest_record_date": record_date or "",
                "record_scope": (
                    "projected"
                    if record_date
                    and date.fromisoformat(record_date) > SNAPSHOT_DATE
                    else "current_or_latest"
                ),
                "current_record_date": current_timeline.get("Date", ""),
                "current_buildings_operational": current_timeline.get(
                    "Buildings operational", ""
                ),
                "current_it_power_mw": (
                    current_it_mw if current_it_mw is not None else ""
                ),
                "current_facility_power_mw": (
                    current_facility_mw
                    if current_facility_mw is not None
                    else ""
                ),
                "current_facility_to_it_ratio": (
                    current_k_ratio if current_k_ratio is not None else ""
                ),
                "current_water_use_mgd": (
                    current_water_mgd
                    if current_water_mgd is not None
                    else ""
                ),
                "current_derived_wue_l_per_kwh_it": (
                    current_wue if current_wue is not None else ""
                ),
                "buildings_operational": timeline.get(
                    "Buildings operational", ""
                ),
                "it_power_mw": it_mw if it_mw is not None else "",
                "facility_power_mw": (
                    facility_mw if facility_mw is not None else ""
                ),
                "facility_to_it_ratio": k_ratio if k_ratio is not None else "",
                "water_use_mgd": (
                    water_mgd if water_mgd is not None else ""
                ),
                "derived_wue_l_per_kwh_it": wue if wue is not None else "",
                "h100_equivalents": timeline.get("H100 equivalents", ""),
                "total_capital_cost_2025_usd_bn": site.get(
                    "Current total capital cost (2025 USD billions)", ""
                ),
                "selected_sources": site.get("Selected Sources", ""),
                "calculations_sheet": site.get("Calculations sheet", ""),
                "timeline_status": timeline.get("Construction status", ""),
            }
        )
    return records


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_site_geojson() -> None:
    sites = load_csv(MASTER_PATH)
    features = []
    for site in sites:
        properties = {
            key: value for key, value in site.items() if key not in {"latitude", "longitude"}
        }
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(site["longitude"]),
                        float(site["latitude"]),
                    ],
                },
            }
        )
    GEOJSON_OUTPUT.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": features},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    rows = build_rows()
    write_csv(LATEST_OUTPUT, rows)
    ordered = sorted(
        rows,
        key=lambda row: float(row["it_power_mw"] or 0),
        reverse=True,
    )
    write_csv(TOP_OUTPUT, ordered[:30])
    write_site_geojson()
    print(f"Wrote {len(rows)} sites to {LATEST_OUTPUT}")
    print(f"Wrote top 30 sites to {TOP_OUTPUT}")
    print(f"Wrote site points to {GEOJSON_OUTPUT}")


if __name__ == "__main__":
    main()
