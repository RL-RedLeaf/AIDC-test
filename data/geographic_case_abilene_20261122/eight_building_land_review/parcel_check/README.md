## Abilene 原八栋园区宗地复核（2026-11-22）

本机 QGIS 3.40.0 Bratislava 已运行 `verify_qgis.py`。PyQGIS 从县宗地图形和规划区块重新投影、合并并求交，四项面积与 GeoPandas 复算一致至 0.0001 ha。下载后可用 QGIS 安装目录中的 `bin/python-qgis.bat verify_qgis.py` 重现。

**目前可复算的规划范围为 330.1947 ha。** 从 Taylor 县估价区 GIS 按 `SUBDIV LIKE '%LANCIUM%'` 取回 13 条记录，保留宗地号、图形、编辑日期。宗地几何并集为 **216.6527 ha**，与 PDD-181 四区块相交 **211.7812 ha**，另有 **4.8715 ha** 落在四区块外。仅凭分区名称无法判定这 4.8715 ha 属于原八栋，模型继续采用四区块作为已核界情景。[县地籍图层](https://gis.taylor-cad.org/server/rest/services/Property_Search_Map/MapServer/0) · [2025-07-01 规划附件，第 106–108 页](https://abilenetx.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4620,plainText=false)#page=106)

| 输入 | 面积、功率或系数 | 统计边界与证据 |
|---|---:|---|
| 原八栋毛地、新站 | 445.15 ha、5.06 ha | Oracle 披露 1,100 acre，Mortenson 披露新站 12.5 acre。完整红线及新站入界比例待核。毛地与四区块面积相差约 114.96 ha，仍缺能对齐八栋阶段的逐宗清单。[园区简报](https://arrington.house.gov/uploadedfiles/final_oracle_oai_data_center_fact_sheet_092225b.pdf) · [新站工程](https://www.mortenson.com/projects/abilene-data-center-development) |
| 前两栋 | 租赁 38.43 ha，建筑基底 9.01 ha，206 MW IT | 按附件 94.963 acre 与一期容量，平均用地强度为 **0.18655 ha/MW IT**，含宗内配套与预留。[租赁附件，第 25 页](https://abilenetx.gov/DocumentCenter/View/39456/Lancium-LLC-Abilene-Second-Amended-and-Restated-Tax-Abatement-Agreement-PDF#page=25) · [一期容量](https://www.nmrk.com/insights/press-releases/newmark-advises-on-3-4-billion-joint-venture-on-one-million-square-foot-texas-data-center) |
| 后六栋 | 建筑基底 27.03 ha，按同型设计折算 618 MW IT | 基底按每栋 484,960 ft²，设计容量按每栋 103 MW IT。后六栋同口径租赁面积、分期新增道路和共用固定地分摊待核，因而实测边际系数留缺。[工程图 C1.0](https://abilenetx.gov/DocumentCenter/View/43833/SP-2026-77-PDF?bidId=#page=1) · [案例输入依据](https://github.com/RL-RedLeaf/AIDC-test/blob/0f2383d/data/geographic_case_abilene_20261122/plan_vs_optimizer/input_register.csv) |
| 八栋合计 | 图示运维区 127.07 ha，整宗运营地 179.61 ha | 均在四区块内统计。土地账另列两站共 5.85 ha。两栋租赁面积与七宗裁切并集的统计范围有别，两者相减不能确定后六栋租赁面积。 |
| 保留图示运维区 | **净地 127.62 ha，最大单块 39.58 ha** | 四区块内。按新增覆盖扣除两站、备用设施、调蓄池、道路、规划缓冲带和洪泛限制。 |
| 保留整宗运营地 | **净地 93.10 ha，最大单块 23.36 ha** | 同一规划边界及筛选条件。单块地面光伏模型可取 23.36 ha 作为该情景的面积上界。 |

**复算方法。** 县地籍为本次读取快照，`EDIT_DATE` 保留各宗记录的更新时间。将几何投影至 EPSG:2276 后求并集、求交，平方美国测量英尺乘以 $(1200/3937)^2/10000$ 换成 ha。另用现有 GeoPackage 的去重面积账复算两组净地，再从各块面积表取最大值。沿用原分析的 12 m 道路、整带避让规划缓冲区，以及余地内缩 5 m、分片后外扩 5 m 并裁回的约 10 m 窄颈处理。本轮新增的是县宗地与规划边界的空间叠加，净地和最大块按既有成果复核。市工程图链接本次访问返回 404，建筑基底沿用仓库已摘录的 C1.0 数值。[原分析及依据](https://github.com/RL-RedLeaf/AIDC-test/tree/5374865/data/geographic_case_abilene_20261122/eight_building_land_review)

**QGIS 复查。** 加载本目录的 `lancium.geojson` 与上一级 `site-land.gpkg` 中的 `planning_blocks`，按 `PROP_ID` 查看对应宗地。运行 `python check.py`（依赖 GeoPandas、requests）可从随附快照打印逐宗面积、交叠和两组净地核算结果。[宗地快照与复算脚本](https://github.com/RL-RedLeaf/AIDC-test/tree/main/data/geographic_case_abilene_20261122/eight_building_land_review/parcel_check)
