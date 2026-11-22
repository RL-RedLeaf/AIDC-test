# 第一问 · 五个场址按各自工程条件与规划对照

运行 `python3 data/q1_plan_comparison/compare.py` 生成双语图表及各站 plan_comparison.csv。主表各行的结果性质见 scope。未知的供电份额保留空值。旧的统一电流比较已按 0.1 版本归档。

模型比较使用各自场址的评估边界。对给定布局，持续 IT 负载受可靠供电除以设施倍率 k、正常水源枯季可供流量 Q 除以取水强度 w、机房可容纳的 IT 负载共同约束。此表报告公开资料能约束的分项。工程额定值、审批总用电和实际可交付功率分别注明。计算以正常网电为主；无现场可靠自发电保证时，目标所需设施总功率按负载乘 k 计算。

|地点与阶段|供电、空间或审批依据|结果及取水边界|
|---|---|---|
|Golden，ESIF 配电改造|DOE 预算第 484 页明确从 4 MW usable 提至 6 MW usable，并同步增加泵、换热器和冷却塔。单线图的计量位置仍待核。|改造后的 6 MW 若含辅机，按 k=1.06 对应 5.66 MW IT；若专指 IT 侧则为 6 MW IT。终态设计 10 MW IT 需要 10.6 MW 设施功率和约 7 m³/h 补水（热虹吸期 w=0.7）。930 m² 机房按 6 m²/柜、100 kW/柜可容纳 15.5 MW。这是容量分期，不宜用改造阶段和终态算误差。|
|Keflavík，VDC04 新增模块|独立新增地块 24,000 m²，园区变电站首期 120 MW、计划终态 240 MW；新模块在园区故障后可用容量中所占份额未知。|沿用单层、建筑覆盖率 50%、机房占楼面 50% 的布局假设，得 6,000 m²、1,000 柜、100 MW IT。规划 120 MW 需 7,200 m² 或 120 kW/柜，以及设施侧 144 MW（k=1.20）；园区终态即使装机能全部交付，其他负荷与预留也必须合计不超过 96 MW 才有此份额。闭路干冷补水按假设 w=0.02 需 2.4 m³/h。100 是布局上限，供电、水源还可进一步限制。|
|Tanjong Kling，整栋建筑|工程供应方 PERI 对 Sunview Drive、11 层、约 17 万 m² 的建筑披露终态需求最高 150 MW。与 Meta 的建筑资料及市场调查一致；PERI 页面未写业主名。当地分配给本项目的可靠接入、变压器冗余和 NEWater 枯季配额仍未知。|预期 k=1.19 得到参考目标 126.05 MW IT；独立的供电预测留空。按本地 w=2.0–2.4 的两个取值目标需 252–303 m³/h，并非行业全范围。若同期连续净供水为 Q，水侧上限为 Q/w。|
|Quilicura，Data Luna|智利国家能源委员会收录的电网企业意见 E07-05 报告某线路段每回路 76 MVA。只对该段设单回路留存，取功率因数 0.95，若该回路全用于本园区，折 72.2 MW 设施负载。另份 CEN 研究对所分析线路采用季节限额和双端潮流，不能将该段名义值视为整站上限。|对应单段情景 66.85 MW IT；2025 电网需求预测是 65 MW 设施功率，即 60.19 MW IT。若仅由该段留存回路供电，为满足预测，其他占用至多约 7.2 MW（同功率因数）。真实网架共享、多路径和分配尚待核。当地常规供水方为 Aguas Andinas，2025 全址平均取水约 120.2 m³/h；缺同期 IT 电量、旱季获配流量，故不给项目 WUE 点估计。|
|Huntingwood，SYD3 九期终态|州规划审批载明设施总用电 400 MW。运营商另公布 320+ MW IT、132 kV 专站、设计 k=1.15。场址审批和接入工程属不同手续。|审批用电包络折 347.83 MW IT。运营商目标下限 320 MW IT 需 368 MW 总用电，较 400 MW 少 32 MW；目标含“+”，不能据此计算确切误差。按运营商同组技术取值 w=0.7–1.2，需 224–384 m³/h；原工程所述管网能力 240 L/s 是系统最大值，项目高温日保供须核连接合同。|

**资料。** [DOE 改造预算](https://www.energy.gov/sites/default/files/2021-06/doe-fy2022-budget-volume-3.1_0.pdf) · [NREL 终态设计](https://docs.nlr.gov/docs/fy21osti/79712.pdf) · [冰岛新增地块环评](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) · [园区变电站](https://www.verne.co/news/news-verne-and-landsnet-launch-high-capacity-substation) · [新加坡工程供应方](https://www.peri.sg/projects/data-center-at-sunview-drive-singapore.html) · [Meta 设计](https://engineering.fb.com/2019/01/14/data-center-engineering/singapore-data-center/) · [智利 CNE 规划意见 E07-05](https://www.cne.cl/wp-content/uploads/2022/03/Respuesta-Observaciones-ITP-Plan-de-Expansion-2021.pdf) · [CEN 需求与分季潮流研究](https://www.coordinador.cl/wp-content/uploads/2021/08/Minuta_Solicitud_Nueva_Subestacion_COLINA_24_08_2021.pdf) · [Google 智利水源](https://blog.google/intl/es-419/noticias-de-la-empresa/10-datos-sobre-el-centro-de-datos-de-google-en-quilicura-chile/) · [悉尼审批](https://www.planningportal.nsw.gov.au/major-projects/projects/51-huntingwood-drive-data-centre) · [九期规划](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/)。

各园区的运行统计、供水强度依据及历史口径另见对应场址的 site_evidence.csv。只有取得同阶段、同范围的可靠供电与配水数据，才能把工程与布局上限收紧为联合容量，并与独立额定 IT 负载作误差检验。
