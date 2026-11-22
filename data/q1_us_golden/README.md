# Golden · ESIF 第一问
2030 条件情景：**5.662 MW IT**，限制资源为**电力**。纯电网 5.660 MW IT；全年光储可靠增供 0.00169 MW（设施侧）。获胜候选：Roof PV + storage。
## 三项上限（MW IT）
| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |
|---|---:|---:|---:|---:|
| Grid | 5.6604 | 9.0714 | 10.0000 | 5.6604 |
| Roof PV + storage | 5.6620 | 9.0714 | 10.0000 | 5.6620 |

## 输入、依据与不确定性

| 参数 | 数值 | 证据身份 | 口径与来源 |
|---|---:|---|---|
| grid | 6 MW | 设计代理 | DOE预算将HPC配电可用功率由4提升至6 MW。基准假定6 MW为持续可用于含辅助设施的设施侧输入；若原值限定为IT侧，6 MW IT另作口径敏感性。 [来源](https://www.energy.gov/sites/default/files/2021-06/doe-fy2022-budget-volume-3.1_0.pdf) |
| k | 1.06 — | 运行统计代理 | 历史滚动年PUE上界作为满载倍率。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) |
| Q | 6.35 m³/h | 情景假设 | 按5 MW设施规模对应旧式热回收冷却塔参考强度1.27，构造已配套的6.35 m³/h取水服务；5 MW取自NREL 2021容量量级。另试改造前年度用水不增长。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) [来源](https://docs.nlr.gov/docs/fy21osti/79712.pdf) |
| wue | 0.7 L/kWh IT | 运行统计代理 | 热虹吸首年现场用水/IT电量，作全年恒定取水强度。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) |
| A | 0.186 ha | 情景假设 | 既有HPC空间视为单层投影：930 m²机房加同等面积配套，折0.186 ha等效用地；仅代表此建筑内HPC模块。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) |
| A0 | 0 ha | 情景假设 | 模块配套全部折入等效强度；不再分别扣减。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) |
| a | 0.0186 ha/MW IT | 同阶段标定 | 0.186 ha等效模块/10 MW IT终态参照。土地上限重现设计容量，无法充当独立验证。 [来源](https://docs.nlr.gov/docs/fy24osti/84492.pdf) |
| roof_m2 | 186 m² | 情景假设 | 以HPC机房面积作等效屋面代理，取20%可用于阵列。 [来源](https://docs.nlr.gov/docs/fy18osti/72196.pdf) |

## 什么变化会改变结论
保持其余参数不变，要达到另外两项中较低的上限：电网需 9.61 MW，取水需 3.96 m³/h，有效用地需 0.105 ha。这三个阈值分别单独计算。

| 专项情景 | 容量 MW IT | 限制资源 |
|---|---:|---|
| Water frozen at historical 9500 m3/year | 1.549 | 取水 |
| 6 MW interpreted as IT-side | 6.002 | 电力 |
| Cooling tower with heat recovery | 5.000 | 取水 |

十年最低连续七天光伏总出力窗口从 2019-11-20T01 UTC 起；独立循环复算得 5.6618 MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。

## 图与复算
图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。

在仓库根目录执行 `python code/run.py data/q1_us_golden/q1.yaml --json /tmp/q1_us_golden_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。
