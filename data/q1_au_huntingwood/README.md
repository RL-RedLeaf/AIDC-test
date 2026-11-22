# Huntingwood · SYD3 第一问
2030 条件情景：**320.000 MW IT**，限制资源为**土地**。纯电网 320.000 MW IT；全年光储可靠增供 0.03821 MW（设施侧）。获胜候选：Grid, Roof PV + storage。
## 三项上限（MW IT）
| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |
|---|---:|---:|---:|---:|
| Grid | 347.8261 | 720.0000 | 320.0000 | 320.0000 |
| Roof PV + storage | 347.8593 | 720.0000 | 320.0000 | 320.0000 |

## 输入、依据与不确定性

| 参数 | 数值 | 证据身份 | 口径与来源 |
|---|---:|---|---|
| grid | 400 MW | 设计代理 | NSW原审批为设施总用电400 MW；假设届时可同时持续交付。 [来源](https://www.planningportal.nsw.gov.au/major-projects/projects/51-huntingwood-drive-data-centre) |
| k | 1.15 — | 设计代理 | 运营商设计PUE。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| Q | 864 m³/h | 设计代理 | 原工程称既有管网最大240 L/s，基准假设全部可供本项目；未假定升级已投运。 [来源](https://majorprojects.planningportal.nsw.gov.au/prweb/PRRestService/mp/01/getContent?AttachRef=SSD-41589232%2120220916T041049.122+GMT) |
| wue | 1.2 L/kWh IT | 设计代理 | AirTrunk FY23框架给SYD3组最大WUE控制值区间0.7–1.2，取上端作取水代理。 [来源](https://airtrunk.com/wp-content/uploads/2023/10/AirTrunk-FY23-Sustainability-Report-FINAL-Online.pdf) |
| A | 8.3 ha | 设计代理 | 沿用与320+ MW IT同版的8.3 ha园区边界，避免混用9.0582 ha报批地块。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| A0 | 0 ha | 同阶段标定 | 使用整园平均毛地强度时，固定设施已合并。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| a | 0.025938 ha/MW IT | 同阶段标定 | 据同阶段8.3 ha / 320+ MW IT，取320对应的平均强度上界，固定面积设0。320由标定引入。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| roof_m2 | 8300 m² | 情景假设 | 缺屋顶清单，取毛地的10%作可铺屋面情景。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |

## 什么变化会改变结论
保持其余参数不变，要达到另外两项中较低的上限：电网需 367.96 MW，取水需 384.00 m³/h，有效用地需 9.023 ha。这三个阈值分别单独计算。

| 专项情景 | 容量 MW IT | 限制资源 |
|---|---:|---|
| Withdraw 25% of existing main maximum | 180.000 | 取水 |
| Framework WUE 0.7 | 320.000 | 土地 |
| 350 MW IT on same parcel (alternative density) | 347.859 | 电力 |

十年最低连续七天光伏总出力窗口从 2022-06-30T02 UTC 起；独立循环复算得 320.0000 MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。

## 图与复算
图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。

在仓库根目录执行 `python code/run.py data/q1_au_huntingwood/q1.yaml --json /tmp/q1_au_huntingwood_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。
