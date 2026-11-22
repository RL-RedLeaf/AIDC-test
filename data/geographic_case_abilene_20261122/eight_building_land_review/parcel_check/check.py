"""复核县地籍与 PDD 四区块的交集，并核对两组净地面积账。"""

import json
import sqlite3
from pathlib import Path

import geopandas as gpd
import requests

HERE = Path(__file__).resolve().parent
LAND = HERE.parent / "site-land.gpkg"
SNAPSHOT = HERE / "lancium.geojson"
URL = "https://gis.taylor-cad.org/server/rest/services/Property_Search_Map/MapServer/0/query"
HA = (1200 / 3937) ** 2 / 10000


def main():
    if not SNAPSHOT.exists():
        response = requests.get(URL, params={
            "f": "geojson", "where": "SUBDIV LIKE '%LANCIUM%'", "outSR": 4326,
            "outFields": "PROP_ID,SUBDIV,BLOCK,LOT,EDIT_DATE,C_ACRE",
            "returnGeometry": "true", "orderByFields": "PROP_ID",
        }, timeout=60)
        response.raise_for_status()
        data = response.json()
        if not data.get("features") or data.get("exceededTransferLimit"):
            raise ValueError("县宗地查询未返回完整结果")
        SNAPSHOT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    blocks = gpd.read_file(LAND, layer="planning_blocks")
    assert blocks.crs.to_epsg() == 2276
    boundary = blocks.geometry.union_all()
    parcels = gpd.read_file(SNAPSHOT).to_crs(blocks.crs)
    parcels.geometry = parcels.geometry.make_valid()
    parcels["parcel_ha"] = parcels.area * HA
    parcels["in_pdd_ha"] = parcels.intersection(boundary).area * HA
    parcels["outside_ha"] = parcels["parcel_ha"] - parcels["in_pdd_ha"]
    print(parcels[["PROP_ID", "BLOCK", "LOT", "parcel_ha", "in_pdd_ha", "outside_ha"]].round(3).to_string(index=False))
    union = parcels.geometry.union_all()
    print("PDD / parcels / intersection / outside PDD (ha):",
          *(round(area * HA, 4) for area in (
              boundary.area, union.area, union.intersection(boundary).area,
              union.difference(boundary).area)))
    with sqlite3.connect(LAND.as_uri() + "?mode=ro", uri=True) as connection:
        for scenario in ("drawn", "lots"):
            ledger = dict(connection.execute(f"SELECT metric,{scenario} FROM area_ledger"))
            net = ledger["gross"] - sum(ledger[key] for key in (
                "operation", "substations", "backup", "pond", "access", "buffer", "flood100"))
            largest, = connection.execute(
                f"SELECT max(area_ha) FROM patch_areas_{scenario}").fetchone()
            assert abs(net - ledger["raw_free"]) < 1e-5
            assert abs(largest - ledger["largest"]) < 1e-5
            print(scenario, round(net, 4), round(largest, 4))


if __name__ == "__main__":
    main()
