# 第一问 · 五个场址与公开规划的对照

模型先从几何、可建机柜、接入电压、可用电流和逐时光储调度推算 IT 负载，再读取项目参照量。正常运行由当地供水系统补水。缺少旱季保供合同的场址按所需流量给出条件判断。各站结果可在各自目录的 plan_comparison.csv 和 normal_supply_scenarios.csv 查看。综合表 comparison.csv 保留未舍入值。运行 `python3 data/q1_plan_comparison/compare.py` 可用已入库的逐时模型结果复算并生成中英文图；若要重建气象输入至可靠光储出力的计算，先运行 [前级脚本](../q1_geography_rebuild/rebuild.py)。

## 对照的共同条件

令 I 表示一个回路退出后仍可分给研究负荷的净相电流，可把多条投运回路折算到同一电压层级。取三相功率因数 0.95。300 A 为统一工程情景；120 A 和 600 A 检查结论对净余量的敏感性。各地上游约束、合同、其他用户和设备限额会改变 I。电力上限为 (√3 VI × 0.95/1000 + 可靠自发电)/k，V 用 kV，I 用 A。机柜每柜按 6 m²、100 kW 算，柜数向下取整。满载取水强度 w 用 L/kWh IT，其数值乘 MW IT 即 m³/h，因此在项目获配的可靠流量为 Q 时，最终上限为 min(电力上限，布局上限，Q/w)。采用年均 PUE 和 WUE 作连续运行代理，设计日冷却峰值需另核。表中的供水需求全由正常水源承担。

| 场址和比较阶段 | 120 / 300 / 600 A 对应 MW IT（供水充足） | 公开参照，MW IT | 规划所需净电流 | 规划所需正常补水 |
|---|---:|---:|---:|---:|
| Golden ESIF 终态 | 2.46 / 6.15 / 12.30 | 10 | 488 A | 7.0 m³/h |
| Keflavík VDC04 三期终态 | 21.72 / 54.30 / 100.00 | 120 | 663 A | 2.4 m³/h |
| Tanjong Kling 园区设计 | 10.97 / 27.39 / 54.77 | 约 126.05，市场报告总功率换算 | 1,381 A | 302.5 m³/h |
| Quilicura，2025 年电网需求情景 | 20.13 / 50.29 / 100.57 | 约 60.19，电网研究需求换算 | 359 A | 30.1 m³/h（低用水冷却方案） |
| Huntingwood SYD3 九期终态 | 22.70 / 56.69 / 113.35 | 320+，按下限比较 | 至少 1,694 A | 按 320 MW 和 1.2 L/kWh 计为 384 m³/h |

## 哪些差别能够解释

**戈尔登。** NREL 同一报告给出典型运行约 2 MW、当时系统容量 5 MW、终态设计 10 MW IT。终态与 300 A 情景相差 3.85 MW。930 m² 机房可布 155 个假设机柜，达到 10 MW 只需其中 100 个。13.2 kV 取自 ESIF 园区研究设施的电压等级，未取得 HPC 实际配电单线图。按此电压，持续净电流从 300 A 提到约 488 A，且正常补水可达 7 m³/h，即可在模型内达到设计值。[NREL 同址技术报告](https://docs.nlr.gov/docs/fy21osti/79712.pdf) · [DOE 场址电压资料](https://www.energy.gov/sites/prod/files/2014/03/f12/nrel_esif.pdf)

**凯夫拉维克。** 冰岛环境文件给出 2.4 ha、三期各 40 MW IT，冷却辅机另计。单层、半幅地块建房、一半楼面排柜的推算给出 6,000 m² 机房；达到终态需要 7,200 m²，或把每柜功率从 100 提升到 120 kW。只提升供电至 600 A 已使布局先触顶，必须同时改两项才能达标。按历史冰岛业务 PUE 1.20 和闭路冷却补水假设 0.02 L/kWh，目标需 144 MW 设施功率、2.4 m³/h 补水。这里的 132 kV 为园区接入升级电压，新增模块的实际分配份额未披露。[官方环境文件](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) · [Landsnet 接入规划](https://www.landsnet.is/library/?itemid=9547d9a6-735e-4a4e-8640-6e294b72d1ce)

**丹戎吉岭。** Meta 披露 11 层建筑、17 万 m² 和预期 PUE 1.19。Cushman & Wakefield 的项目表给出总功率 150 MW，等效 IT 负载 126.05 MW。按此目标反推，所需机房约 7,566 m²，约占总楼面 4.5%；模型假设的一半楼面排柜已有余量。66 kV 是附近数据中心区的电压层级，其在单回路只剩 300 A 时解释了模型低值。按地区行业取水强度 2.4，需约 303 m³/h。地区普遍使用 NEWater，缺项目枯季供水合同和现场 WUE；若实际 WUE 为 2.0，水量变为约 252 m³/h。市场报告可用于量级对照；仍缺运营商发布的终态 MW IT。[Meta 设计说明](https://engineering.fb.com/2019/01/14/data-center-engineering/singapore-data-center/) · [市场调查原表](https://assets.cushmanwakefield.com/-/media/cw/apac/singapore/insights/data-centre-update_apac_spring2021.pdf?rev=17045adf56ad442fab83b2ad90e74aaf) · [新加坡供水说明](https://www.mse.gov.sg/latest-news/written-reply-to-parliamentary-question-on-data-centres--use-of-fresh-water-supply/)

**基利库拉。** 智利电网运营机构 2021 年潮流研究第 15 页把 Data Luna 在 2025 年的需求按 65 MW 设施功率计；用园区 PUE 1.08 得 60.19 MW IT。300 A 情景在 110 kV 下给出 50.29 MW IT。359 A 可补足供电差额。已知二期机房投影的一半用于排柜就能容纳目标，整个园区一期楼面未计入。目标是电网预测，同期持续 IT 额定值未披露。

Google 确认园区使用 Aguas Andinas 供水。按低用水冷却假设 0.5 L/kWh，支持 60.19 MW IT 需 30.1 m³/h；按 Google 2025 年披露的全址取水 278.2 百万美制加仑，实际全年平均取水约 120.2 m³/h。若假定 65 MW 确为该年设施负载上限且年度 PUE 为 1.08，则实际全址取水强度至少约 2.0 L/kWh IT。此项独立核查说明低用水设计情景会明显低估既有园区全址取水，不能据 30.1 m³/h 判断现实供水富余。年度平均取水也无法代替旱季合同保供量。[电网研究第 15 页](https://www.coordinador.cl/wp-content/uploads/2021/08/Minuta_Solicitud_Nueva_Subestacion_COLINA_24_08_2021.pdf) · [Google 供水来源](https://blog.google/intl/es-419/noticias-de-la-empresa/10-datos-sobre-el-centro-de-datos-de-google-en-quilicura-chile/) · [Google 环境数据](https://storage.googleapis.com/gweb-mobius-cdn/sustainability/uploads/21455428735c7305f2cb5c0038fc14bb0803abb8.pdf)

**悉尼西部。** 运营商 2021 年方案给出九期合计 320+ MW IT、132 kV、设计 PUE 1.15。按 320 MW 求得 3,200 个机柜和 19,200 m² 有效机房；后续规格页披露的技术机房面积为 70,000 m²，取其中一半排柜也能容纳，但规格页与首版方案的阶段不同。按下限计算，需要至少 368 MW 设施用电，相当于 132 kV 时故障后仍保留约 1,694 A 净电流。可由多个回路共同提供。与基准相比，差距主要来自基准只允许 300 A，运营商未披露与该设定相同的接线条件。按运营商所属组用水强度控制值 0.7–1.2 计算，320 MW 需 224–384 m³/h。原工程列出的既有管网最大 240 L/s（864 m³/h）涵盖更广的管网，工程仍提出峰时扩容需求；项目配额及高温日峰值决定水量是否足够。[AirTrunk 分期公告](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) · [园区规格](https://airtrunk.com/location/syd3-sydney-west/) · [原供水工程第 7 节](https://majorprojects.planningportal.nsw.gov.au/prweb/PRRestService/mp/01/getContent?AttachRef=SSD-41589232%2120220916T041049.122+GMT)

本次计算比较了给定接线与建筑条件能支持的负载，以及各项目公开规模要求的条件。情景与规划之间的差额不能当作独立预测误差；公开电流、配水合同与同期实际满载数据不足以支持这种精度评价。
