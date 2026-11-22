"""用 QGIS 的投影和几何运算独立复核宗地面积（ha）。"""

import os
from pathlib import Path

from qgis.core import (
    Qgis, QgsApplication, QgsCoordinateTransform, QgsGeometry, QgsProject,
    QgsVectorLayer,
)

root = Path(__file__).resolve().parent
app = QgsApplication([], False)
app.setPrefixPath(os.environ["QGIS_PREFIX_PATH"], True)
app.initQgis()
blocks = QgsVectorLayer(str(root.parent / "site-land.gpkg") + "|layername=planning_blocks",
                        "planning", "ogr")
parcels = QgsVectorLayer(str(root / "lancium.geojson"), "parcels", "ogr")
assert blocks.isValid() and parcels.isValid() and blocks.crs().authid() == "EPSG:2276"
transform = QgsCoordinateTransform(parcels.crs(), blocks.crs(), QgsProject.instance())
parts = []
for feature in parcels.getFeatures():
    geometry = feature.geometry()
    geometry.transform(transform)
    parts.append(geometry.makeValid())
boundary = QgsGeometry.unaryUnion([feature.geometry() for feature in blocks.getFeatures()])
union = QgsGeometry.unaryUnion(parts)
print(Qgis.QGIS_VERSION, len(parts))
for shape, expected in zip(
    [boundary, union, union.intersection(boundary), union.difference(boundary)],
    [330.1947, 216.6527, 211.7812, 4.8715],
):
    area = shape.area() * (1200 / 3937) ** 2 / 10000
    print(round(area, 4))
    assert abs(area - expected) < 0.005
