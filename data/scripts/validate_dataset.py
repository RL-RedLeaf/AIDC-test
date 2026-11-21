"""Validate hashes, CSV shapes, source links, GeoJSON, and Q1 outputs."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import yaml


DATA_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = DATA_ROOT / "outputs"
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


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError(f"{path} has no data rows")
    if any(None in row for row in rows):
        raise AssertionError(f"{path} has rows with the wrong column count")
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    manifest = json.loads(
        (OUTPUT_DIR / "33_data_manifest.json").read_text("utf-8")
    )
    for item in manifest["raw_snapshot"].values():
        path = DATA_ROOT / item["path"]
        assert sha256(path) == item["sha256"], f"raw hash mismatch: {path}"
    for relative, expected in manifest["evidence_files"].items():
        assert sha256(DATA_ROOT / relative) == expected, relative
    for relative in manifest["derived_files"]:
        assert (DATA_ROOT / relative).exists(), f"missing derived file: {relative}"

    sites = csv_rows(OUTPUT_DIR / "03_sites_master.csv")
    sources = csv_rows(OUTPUT_DIR / "04_source_registry.csv")
    known_sources = {row["source_id"] for row in sources}
    for row in sites:
        requested = {item for item in row["source_ids"].split(";") if item}
        missing = requested - known_sources
        assert not missing, f"{row['site_id']} has unknown sources: {missing}"

    summary = csv_rows(OUTPUT_DIR / "09_q1_case_summary.csv")
    summary_by_case = {row["case"]: row for row in summary}
    configs = sorted(OUTPUT_DIR.glob("*_input.yaml"))
    assert configs, "no Q1 configurations found"
    for path in configs:
        config = yaml.safe_load(path.read_text("utf-8"))
        assert config["model"] == "q1"
        assert config.get("scenarios")
        case = path.stem.split("_", 1)[1].removeprefix("q1_").removesuffix(
            "_input"
        )
        assert case in CASE_OUTPUT_IDS, f"unregistered case: {case}"
        assert case in summary_by_case, f"missing summary row: {case}"
        result = json.loads(
            (
                OUTPUT_DIR
                / f"{CASE_OUTPUT_IDS[case]:02d}_q1_{case}_result.json"
            ).read_text("utf-8")
        )
        assert float(result["P_max_mw_it"]) == float(
            summary_by_case[case]["P_max_mw_it"]
        )

    geojson = json.loads(
        (OUTPUT_DIR / "10_sites.geojson").read_text("utf-8")
    )
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == len(sites)

    index = csv_rows(OUTPUT_DIR / "00_output_index.csv")
    expected_ids = [f"{value:02d}" for value in range(1, len(index) + 1)]
    assert [row["output_id"] for row in index] == expected_ids
    assert len({row["filename"] for row in index}) == len(index)
    missing_outputs = [
        row["filename"]
        for row in index
        if not (OUTPUT_DIR / row["filename"]).exists()
    ]
    assert not missing_outputs, f"missing indexed outputs: {missing_outputs}"

    print(
        f"Validated {len(sites)} curated sites, "
        f"{len(configs)} Q1 cases, {len(sources)} sources, "
        f"and {len(index)} indexed outputs."
    )


if __name__ == "__main__":
    main()
