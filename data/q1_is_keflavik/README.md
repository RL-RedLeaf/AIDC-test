# Keflavík · Verne 第一问
2030 条件情景：**100.002 MW IT**，限制资源为**电力**。纯电网 100.000 MW IT；全年光储可靠增供 0.00223 MW（设施侧）。获胜候选：Roof PV + storage。
## 三项上限（MW IT）
| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |
|---|---:|---:|---:|---:|
| Grid | 100.0000 | 180.0000 | 792.5000 | 100.0000 |
| Roof PV + storage | 100.0019 | 180.0000 | 792.5000 | 100.0019 |

## 输入、依据与不确定性

| 参数 | 数值 | 证据身份 | 口径与来源 |
|---|---:|---|---|
| grid | 120 MW | 设计代理 | 2025年首期变电站120 MW已投运；按铭牌全额可交付。另测60 MW及规划终态240 MW。 [来源](https://www.verne.co/news/news-verne-and-landsnet-launch-high-capacity-substation) |
| k | 1.2 — | 运行统计代理 | 2025冰岛业务PUE作场址满载代理。 [来源](https://www.verne.co/about-us/sustainability) |
| Q | 3.6 m³/h | 情景假设 | 假设为整个园区划拨1 L/s的常态补水服务。扩建答复称已接HS Veitur且闭路散热初充后补水极少；未披露全园区合同流量。 [来源](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) |
| wue | 0.02 L/kWh IT | 情景假设 | 闭路项目环评给出600 m³初装冷却液及每年少量补液，二者均不足以确定全园区WUE。本次预留0.02 L/kWh IT用于辅助补水和杂用，取0.005–0.08检验。 [来源](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) |
| A | 16 ha | 设计代理 | 以运营商16 ha毛地作可用面积的乐观上界，含共享设施。 [来源](https://www.verne.co/hubfs/Datasheets%202025/Iceland_Datasheet%20.pdf) |
| A0 | 0.15 ha | 情景假设 | 1500 m²首期变电站按单层地面占用计入园区；其余设施由综合强度覆盖。 [来源](https://www.verne.co/news/news-verne-and-landsnet-launch-high-capacity-substation) |
| a | 0.02 ha/MW IT | 同阶段标定 | 采用同址新建筑2.4 ha / 120 MW IT；是紧凑模块平均强度，假设可代表既有园区可扩建布局。若新模块已包含共享变电站份额，存在小量重复，另测A0=0。 [来源](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) |
| roof_m2 | 4800 m² | 情景假设 | 取已披露扩建地块面积20%作整个园区可铺屋面情景。 [来源](https://uua.is/urleits/uua2606003-uppbygging-gagnavers/) |

## 什么变化会改变结论
保持其余参数不变，要达到另外两项中较低的上限：电网需 216.00 MW，取水需 2.00 m³/h，有效用地需 2.150 ha。这三个阈值分别单独计算。

| 专项情景 | 容量 MW IT | 限制资源 |
|---|---:|---|
| 240 MW planned station fully deliverable | 180.000 | 取水 |
| Closed-loop water allowance reduced | 45.000 | 取水 |
| Legacy low-density land proxy | 100.002 | 电力 |
| No separate common substation deduction | 100.002 | 电力 |

十年最低连续七天光伏总出力窗口从 2021-12-16T14 UTC 起；独立循环复算得 100.0005 MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。

## 图与复算
图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。

在仓库根目录执行 `python code/run.py data/q1_is_keflavik/q1.yaml --json /tmp/q1_is_keflavik_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。
