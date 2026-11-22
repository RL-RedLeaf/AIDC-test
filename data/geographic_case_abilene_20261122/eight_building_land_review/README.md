# Abilene 原八栋园区的电、水与用地核查

这份资料用于 IMMC 2027 A 题第一问。原八栋园区公开毛地为 **445.15 ha**。市存工程图给八栋单层建筑标出的基底合计 **36.04 ha**。即使只保留楼，地面光伏最多也只能分到 **409.11 ha**，相对模型中的 429.5 ha **至少缺 20.39 ha**。退界、道路与备用设施都会继续收紧这个上限。[Oracle 场址资料，第 1–2 页](https://arrington.house.gov/uploadedfiles/final_oracle_oai_data_center_fact_sheet_092225b.pdf#page=1) · [八栋工程图 C1.0](https://abilenetx.gov/DocumentCenter/View/43833/SP-2026-77-PDF?bidId=#page=1)

| 文件 | 怎么用 |
| --- | --- |
| [四页中文研究报告](abilene-land-review.pdf) | 第 1 页用建筑基底检验全园面积，第 2 页比较两种保留方式，第 3 页是同阶段资源与四类发电方式对照，第 4 页说明固定用地修正与数据出处。 |
| [可编辑学生研读表 0.4](Abilene%20第一问学生研读表%200.4.xlsx) | 前三张表涵盖同阶段电水地、四类供电和八栋建筑的用地上限。新增“宗地回传与扩建”列出县地籍复核数据，可修改新增 IT 的单位用地，观察单块可支撑的增量。 |
| [宗地回传与 QGIS 复算脚本](parcel_check/) | 县地籍 GeoJSON 和复核四区块面积的两套脚本。与上一行的工作表配套。 |
| [按规划与重配的最新计算](../plan_vs_optimizer/README.md) | 五页中文报告、输入、图表和求解器结果。第 5 页专门展示宗地复核对扩建估计的影响。 |
| [QGIS 数据包](site-land.gpkg) | 单文件 GeoPackage，包含 7 个空间图层和 3 个面积表。 |
| [LaTeX 源码](abilene-land-review.tex) | 两幅地图与面积图均已嵌入。可用带有 ctex、Fandol 和 TikZ 的 TeX Live 运行 `latexmk -xelatex abilene-land-review.tex`。 |

## 在 QGIS 里看什么

把 `site-land.gpkg` 拖入 QGIS，选中需要的图层。先开 `planning_blocks` 和 `zoning_buffer`，再把一个 `pv_grid_` 图层放在上方。在“图层属性 → 符号系统 → 分类”选择 `class_id`，把 1 设为深绿、2 设为浅绿，即可对应报告第 2 页。右键另一情景的图层可切换可见性，两幅图使用同一坐标系与同一格网。

| 图层或表 | 范围、字段与单位 |
| --- | --- |
| `planning_blocks` | 2025-07-01 PDD-181 测绘 Exhibit D 的四个区块，`part` 为 A–D，`area_ha` 为转绘多边形面积。四个区块合并约 330.19 ha。 |
| `zoning_buffer` | 同一测绘图的阴影缓冲带，已裁到四区块，相交约 48.37 ha。光伏筛选情景整带避让，具体许可待核。 |
| `flood_1pct`、`flood_02pct` | 市公开的两档年超越概率洪泛区与四区块的相交结果，均为 0 条。 |
| `flood_context_500m` | 四区块周边 500 m 内可见的市级洪泛图形。此层帮助理解相交为零的空间背景，未增加扣地。 |
| `pv_grid_drawn`、`pv_grid_lots` | 分别按“保留图示运维区”和“保留整宗运营地”筛选。每格 100 m。候选地覆盖整格面积至少一半才显示，最大候选块覆盖整格至少一半时标 1，其余标 2。边界格裁至规划区。 |
| `patch_areas_drawn`、`patch_areas_lots` | 两种情景各块的原多边形面积，单位 ha。筛选 `rank_no = 1` 可读最大块 39.58 与 23.36 ha。网格用于显示，复核面积请读这两张表。 |
| `area_ledger` | 两种情景的统计表。开头为分区面积，中间为每一类用地去重后的新增扣除面积，最后为余地合计与最大连续块。 |

坐标系为 **EPSG:2276，NAD83 / Texas North Central (ftUS)**。图层坐标使用美国测量英尺。若以投影单位算出平方英尺，应乘以 `(1200 / 3937)² / 10000` 才得到公顷。工程图标注的建筑面积按国际英尺换算，1 ft² = 0.09290304 m²。

## 面积、边界与查证程度

| 保留方式 | 四块范围 / ha | 剩余合计 / ha | 最大连续块 / ha |
| --- | ---: | ---: | ---: |
| 图示运维区 | 330.19 | 127.62 | 39.58 |
| 整宗运营地 | 330.19 | 93.10 | 23.36 |

规划附件 A 的四区分项合计 815.86 英亩，附件 D 的矢量边界用四个测绘起点配准。公开分区与 Oracle 披露的 1,100 英亩缺少逐宗对照，两者约 115 ha 的差额仍缺完整界线。增补宗地可能与现有候选地相连。报告给出了全园可判定的面积上限，也保留了全园最大连续地这一数据缺口。[2025 年 7 月 1 日市规划会议原件，第 106–108 页](https://abilenetx.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=4620,plainText=false)#page=106) · [原八栋布局，第 6 页](https://www.esig.energy/wp-content/uploads/2025/05/ESIG_LLTF_PresentationLancium.pdf#page=6)

工程图用于辨认 1–8 栋及同阶段配套。较宽松情景保留图示运维范围，较严格情景保留七宗对应运营地，其中 1、2 栋共宗。计算依次并入变电设施、备用设施、调蓄池、主要道路、规划缓冲带和市级洪泛层，每一项只记新增覆盖。通道取 12 m 宽，并用 8 m、16 m 另算。余地向内收 5 m 后分出连片，各片分别向外扩回 5 m、裁回原余地再量算，以过滤约 10 m 以下的窄连接。两列是情景结果。坡度、具体退界和环境许可仍需核实。[县估价区宗地 GIS](https://gis.taylor-cad.org/server/rest/services/Property_Search_Map/MapServer/0) · [市税务协议](https://abilenetx.gov/DocumentCenter/View/39456/Lancium-LLC-Abilene-Second-Amended-and-Restated-Tax-Abatement-Agreement-PDF#page=4) · [市洪泛图层](https://services6.arcgis.com/iBFmWI3dYPQqS1KF/ArcGIS/rest/services/City_of_Abilene_Flood_Zones/FeatureServer)

12.5 英亩（5.06 ha）是承建商公布的新站面积，旧站约 0.79 ha 为图示外框估算。公开材料支持将新站作为原园区配套，仍缺能把新站逐宗对应到 Oracle 1,100 英亩的法律边界。Longhorn 工程图列出的 25.38 英亩（10.27 ha）为施工整地界。道路、停车和其余硬化合计约 24.05–35.17 ha，端点反映 1、2 栋重复行的两种读法。[Mortenson 项目记录](https://www.mortenson.com/projects/abilene-data-center-development) · [Longhorn 场平图，第 4 页](https://www.abilenetx.gov/DocumentCenter/View/31589/SP-2024-25-Revision-PDF#page=4) · [市存工程图 C1.0](https://abilenetx.gov/DocumentCenter/View/43833/SP-2026-77-PDF?bidId=#page=1)

2026-11-22 回传的 13 宗县地籍并集为 216.6527 ha，其中 211.7812 ha 位于四区块内。区外 4.8715 ha 的原八栋归属仍待核。QGIS 与 GeoPandas 均复核了上述交叠和四区块面积，两种保留方式的余地及最大单块也已按原面积账复算。当天通过市政府不带 www 的地址重新取得 54 页工程 PDF，第 1 页 C1.0 的 1–8 栋逐项标注 484,960 ft²。学生表 0.4 保留了这个可独立核对的面积上界。[回传原文](https://github.com/RL-RedLeaf/AIDC-test/issues/1#issuecomment-7075596106) · [市工程图第 1 页](https://abilenetx.gov/DocumentCenter/View/43833/SP-2026-77-PDF?bidId=#page=1)

电、水、土地对照与四类单项发电结果沿用仓库提交 `e29f173`。输出 03 的光储已包含 100 MW 持续网电。报告同时核查了固定站地和单位用地系数是否分摊了同一块地。研究材料整理于 2026-11-22。[仓库模型与输出](https://github.com/RL-RedLeaf/AIDC-test/tree/e29f173e6fefb8e29455d2b8aea577f6961dfd37/data/geographic_case_abilene_20261122) · [GitHub 议题 #1](https://github.com/RL-RedLeaf/AIDC-test/issues/1)
