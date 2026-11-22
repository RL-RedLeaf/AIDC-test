# Tanjong Kling · Meta 第一问
2030 条件情景：**110.447 MW IT**，限制资源为**水**。纯电网 110.447 MW IT；全年光储可靠增供 0.01748 MW（设施侧）。获胜候选：Grid, Roof PV + storage。
## 三项上限（MW IT）
| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |
|---|---:|---:|---:|---:|
| Grid | 126.0504 | 110.4466 | 187.2281 | 110.4466 |
| Roof PV + storage | 126.0651 | 110.4466 | 187.2281 | 110.4466 |

## 输入、依据与不确定性

| 参数 | 数值 | 证据身份 | 口径与来源 |
|---|---:|---|---|
| grid | 150 MW | 设计代理 | Cushman & Wakefield亚太项目原始市场研究将本项目总功率列为150 MW；用作设施输入代理，缺逐时交付协议。 [来源](https://assets.cushmanwakefield.com/-/media/cw/apac/japan/insights/research/2022/08/apac-dc-marketbeats-h1-2022.pdf) |
| k | 1.19 — | 设计代理 | Meta预期年PUE作满载倍率。 [来源](https://datacenters.atmeta.com/2019/01/rethinking-data-center-design-for-singapore/) |
| Q | 265.07 m³/h | 情景假设 | 缺项目获配NEWater流量。以单根内径250 mm、流速1.5 m/s的专用管等效建模；250 mm参照悉尼工程规格，流速为显式设计假设。另算200和300 mm。 [来源](https://majorprojects.planningportal.nsw.gov.au/prweb/PRRestService/mp/01/getContent?AttachRef=SSD-41589232%2120220916T041049.122+GMT) |
| wue | 2.4 L/kWh IT | 运行统计代理 | 当地2021数据中心样本中位，用水/IT电量。作为Meta的取水代理；另试2025年发布的行业WEI 2.1。 [来源](https://www.mas.gov.sg/-/media/mas-media-library/development/sustainable-%EF%AC%81nance/singaporeasia-taxonomy-updated.pdf) |
| A | 4.8562 ha | 设计代理 | 项目12 acre毛地全部作为有效用地上界。 [来源](https://datacenters.atmeta.com/2019/01/rethinking-data-center-design-for-singapore/) |
| A0 | 0 ha | 情景假设 | 采用悉尼整园平均用地强度转移，已内含共用设施。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| a | 0.025938 ha/MW IT | 情景假设 | 同为亚太高密度园区，转用悉尼的整园平均用地强度；新加坡11层，实际密度待核。 [来源](https://airtrunk.com/airtrunk-expands-western-sydney-region-with-new-syd3-hyperscale-data-centre-asia-pacifics-largest/) |
| roof_m2 | 3090.9 m² | 情景假设 | 总楼面/11近似单层，再取20%屋面可用于阵列。 [来源](https://datacenters.atmeta.com/2019/01/rethinking-data-center-design-for-singapore/) |

## 什么变化会改变结论
保持其余参数不变，要达到另外两项中较低的上限：电网需 131.41 MW，取水需 302.56 m³/h，有效用地需 2.865 ha。这三个阈值分别单独计算。

| 专项情景 | 容量 MW IT | 限制资源 |
|---|---:|---|
| Equivalent 200 mm pipe | 70.686 | 取水 |
| Equivalent 300 mm pipe | 126.065 | 电力 |
| PUB sector benchmark | 126.065 | 电力 |

十年最低连续七天光伏总出力窗口从 2023-01-24T07 UTC 起；独立循环复算得 110.4466 MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。

## 图与复算
图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。

在仓库根目录执行 `python code/run.py data/q1_sg_tanjongkling/q1.yaml --json /tmp/q1_sg_tanjongkling_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。
