# Quilicura · Google 第一问
2030 条件情景：**60.200 MW IT**，限制资源为**电力**。纯电网 60.185 MW IT；全年光储可靠增供 0.01621 MW（设施侧）。获胜候选：Roof PV + storage。
## 三项上限（MW IT）
| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |
|---|---:|---:|---:|---:|
| Grid | 60.1852 | 67.5861 | 96.4883 | 60.1852 |
| Roof PV + storage | 60.2002 | 67.5861 | 96.4883 | 60.2002 |

## 输入、依据与不确定性

| 参数 | 数值 | 证据身份 | 口径与来源 |
|---|---:|---|---|
| grid | 65 MW | 设计代理 | 智利电网运营机构2021潮流研究对Data Luna自身取2025年需求65 MW。另有75 MVA二号变压器记录；基准用需求预测代理持续交付。 [来源](https://www.coordinador.cl/wp-content/uploads/2021/08/Minuta_Solicitud_Nueva_Subestacion_COLINA_24_08_2021.pdf) |
| k | 1.08 — | 运行统计代理 | 2025园区年度PUE作满载代理。 [来源](https://storage.googleapis.com/gweb-mobius-cdn/sustainability/uploads/21455428735c7305f2cb5c0038fc14bb0803abb8.pdf) |
| Q | 180 m³/h | 设计代理 | 历史环评两井合计50 L/s即180 m³/h。假定权利仍可用且井产量足以支撑；全站需求由该边界承担，不另加市政水。 [来源](https://infofirma.sea.gob.cl/DocumentosSEA/MostrarDocumento?docId=ac%2Ff2%2Fd1e1a5ee1a9628acc781bdf1b58f4f6e66b8) |
| wue | 2.6633 L/kWh IT | 情景假设 | 2025地点取水278.2百万美制加仑。假设同年设施平均负荷为65 MW规划值的75%，用PUE换算IT年电量，得取水强度；联合核查50%及100%负荷率。 [来源](https://storage.googleapis.com/gweb-mobius-cdn/sustainability/uploads/21455428735c7305f2cb5c0038fc14bb0803abb8.pdf) |
| A | 15.9 ha | 设计代理 | 一期与相邻二期合计15.9 ha，占地口径；假设可按既有工业布局使用。 [来源](https://infofirma.sea.gob.cl/DocumentosSEA/MostrarDocumento?docId=ac%2Ff2%2Fd1e1a5ee1a9628acc781bdf1b58f4f6e66b8) |
| A0 | 2.03 ha | 情景假设 | 二期明确的变电站0.45 ha与道路1.58 ha单列为固定设施；一期固定面积缺测。 [来源](https://infofirma.sea.gob.cl/DocumentosSEA/MostrarDocumento?docId=ac%2Ff2%2Fd1e1a5ee1a9628acc781bdf1b58f4f6e66b8) |
| a | 0.14375 ha/MW IT | 情景假设 | 无同址扩建分期的IT MW，转用原仓库Abilene机柜—楼面—地块参考强度；配套与固定设施口径有误差。 [来源](../geographic_case_abilene_20261122/10_geographic_case_report.md) |
| roof_m2 | 2720 m² | 情景假设 | 二期机房建筑地面面积1.36 ha作屋面代理，取20%。 [来源](https://infofirma.sea.gob.cl/DocumentosSEA/MostrarDocumento?docId=ac%2Ff2%2Fd1e1a5ee1a9628acc781bdf1b58f4f6e66b8) |

## 什么变化会改变结论
保持其余参数不变，要达到另外两项中较低的上限：电网需 72.98 MW，取水需 160.33 m³/h，有效用地需 10.684 ha。这三个阈值分别单独计算。

| 专项情景 | 容量 MW IT | 限制资源 |
|---|---:|---|
| Wells at planned average 15 L/s | 20.276 | 取水 |
| 2025 actual withdrawal as fixed budget | 45.139 | 取水 |
| 2025 mean facility load at 50% of 65 MW | 45.057 | 取水 |
| 2025 mean facility load at 100% of 65 MW | 60.200 | 电力 |

十年最低连续七天光伏总出力窗口从 2023-06-20T20 UTC 起；独立循环复算得 60.1973 MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。

## 图与复算
图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。

在仓库根目录执行 `python code/run.py data/q1_cl_quilicura/q1.yaml --json /tmp/q1_cl_quilicura_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。
