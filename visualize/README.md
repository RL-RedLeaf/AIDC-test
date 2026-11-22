# Q1 模型性质图组：图像索引

> **Abilene 图 fig06 已撤回，不可引用。** 它把 1 GW 变电站工程容量当作园区持续可交付功率，并用假设的机柜布局系数推算土地上限。历史图文件为追溯保留；`data/primary_20261121/outputs/15_validity_audit.csv` 记录原因。`fig01`–`fig05` 是合成模型诊断图，不受这次 Abilene 输入错误影响。

> Scope update: the synthetic-input statement below applies to `fig01` through `fig05` only. `fig06` is a separate, conditional Abilene site screening. It is not a verified three-resource limit. The numbered file inventory is `00_output_index.csv`.

本图组只研究 [Q1-v2 正稿](../正稿/q1-v2/IMMC2027-Q1/IMMC2027-Q1.md) 中的静态单场址模型：每套已投运方案的联合容量为
`P(x) = min(P_E, P_W, P_L)`，最终 `P_max(y)` 为当年可选方案的最大值。**所有输入都是为观察模型行为而设的合成情景**，没有使用特定地区的电网合同、可用水权、GIS 地块或实际 PUE/WUE。因此图中 MW 数字不能写成真实数据中心的容量预测，也不能据此推断 950 MW、2263 MW 或 5 GW 项目是否可建。

## 生成与排版

在仓库根目录运行 `python visualize/plot_q1.py`。脚本导入 `code/immc_power_capacity/core.py` 的 `assess_site` 和 `solar`，逐点调用现有模型计算；不复写容量公式。需要 `code/requirements.txt` 中的依赖，以及 `matplotlib>=3.10`。用到的文件都在本目录。每张图有英文文件 `figXX_*.{pdf,svg,png}` 和中文文件 `figXX_*_zh.{pdf,svg,png}`，两版数值一致，CSV 各一份。PDF 用于论文排版，SVG 用于矢量编辑，PNG 为 300 dpi 预览；CSV 为带 BOM 的 UTF-8，可在 Windows Excel 中直接显示中文瓶颈名称。重新运行会覆盖同名生成文件。

版式：单图宽约 7.25 英寸，多面板宽约 7.4 英寸；白底、0.7 pt 轴线、0.55 pt 网格线，主要结果约 2.3 pt。英文为 Times New Roman，中文为 Noto Serif SC，公式用 STIX。蓝色表示电力约束，青绿色表示水量约束，橙色表示土地约束，深灰色表示三者取最小后的联合容量；紫色仅用于电池电量或方案标识。中文、英文两版保留同一坐标范围和图例。论文正文建议优先放图 1、图 2、图 3；图 4、图 5 作为方法或情景补充。多面板图 2、图 4 应作为整幅插入，避免拆散共享的轴和参数说明。

## 共用合成情景

图 1、2、5 以同一假想场址为基础：电网可持续交付 `108 MW`、满载设施倍率 `k=1.20`、现场耗水强度 `WUE=1.50 L/kWh IT`、可分配**耗水**预算 `150 m³/h`、有效园区面积 `160 ha`、IT 侧固定用地 `10 ha`、边际用地强度 `1 ha/MW IT`。这些参数只是实验坐标，**不是全球中位数，也不是规范或许可值**。燃机假设可按实际需求连续调节，发电耗水与实际调用出力相乘；电网优先供电。计算期内保持额定 IT 负荷，无故障、无 N-1 或概率可靠性约束。

六种供能方案及其不同输入（未列字段沿用上述公共值）：

| 方案 | 自建电源、用地和运行输入 | 冷却与发电耗水系数 |
|---|---|---|
| 纯电网 | `A_e=0` | 公共 WUE |
| 风电 | `A_e=30 ha`，`0.3 km² × 100 MW/km²`，两时段净出力 `[12,4] MW` | 发电耗水 0 |
| 光储 | `A_e=20 ha`，`0.2 km² × 100 MW/km²`，两时段 `[20,0] MW`，每时段 1 h；电池充／放电功率各 10 MW、可用电量 10 MWh、效率均为 1 | 发电耗水 0 |
| 湿冷燃气 | `A_e=20 ha`，1 台 60 MW、单台需地 5 ha | WUE 1.50；发电耗水 0.78 L/kWh |
| 干冷燃气 | 电源与用地同上 | WUE 0.75；发电耗水 0.0076 L/kWh |
| 煤电 | `A_e=30 ha`，2 台各 80 MW、单台需地 15 ha | WUE 1.50；发电耗水 2.60 L/kWh |

系数和设备配置是**为了展示约束切换而设定**，不能从图 1 排列推出任何技术在真实地区的普遍优劣。风光的两时段序列也是合成的短周期，仅保障所给周期；不代表年度容量因子或 ELCC。水项采用耗水口径，现场 WUE 与发电系数在同一预算下相加。

## 逐图索引

| 图及文件 | 绘制条件、读法与论文用途 | 数值表 |
|---|---|---|
| **图 1 三约束与方案排序**：[中文 PNG](fig01_joint_limits_zh.png) · [中文 PDF](fig01_joint_limits_zh.pdf) · [英文 PDF](fig01_joint_limits.pdf) | 共用情景的六套技术；每行蓝／青／橙点分别是 `P_E`、`P_W`、`P_L`，深灰菱形是联合容量 `P`，其右下方的“电／水／地”是触顶约束。纯电网 90.0、湿冷燃气 96.2、干冷燃气 130.0 MW IT；煤电虽有 223.3 MW IT 电力上限，却因水约束降到 93.2。说明不能只比较装机或单一资源上限。 | [CSV](fig01_joint_limits.csv) |
| **图 2 瓶颈相图**：[中文 PNG](fig02_binding_map_zh.png) · [中文 PDF](fig02_binding_map_zh.pdf) · [英文 PDF](fig02_binding_map.pdf) | 固定湿冷燃气配置 1 台 60 MW、`A_e=20 ha`、`k=1.2`、`WUE=1.5`、发电耗水 `0.78 L/kWh`、土地上限 `130 MW IT`；只改变电网 `40–180 MW` 与耗水预算 `60–260 m³/h`。左图色标是联合 MW IT，白线为 60／90／110／125 MW IT 等值线；右图颜色指最先触顶的资源。两图同一点一一对应；高水预算下可能由电力转为土地瓶颈，低水预算由水量控制。仅代表这套设备的二维情景切片。 | [CSV](fig02_binding_map.csv) |
| **图 3 发电用地权衡**：[中文 PNG](fig03_land_tradeoff_zh.png) · [中文 PDF](fig03_land_tradeoff_zh.pdf) · [英文 PDF](fig03_land_tradeoff.pdf) | 另一组完全合成的燃气示例：电网 80 MW、`k=1.2`、耗水预算 130 m³/h、WUE 1.0、发电耗水 0.4 L/kWh、有效用地 180 ha、固定 IT 用地 10 ha、`a_site=1 ha/MW IT`；最多 3 台，每台 40 MW 且需地 10 ha。横轴枚举 `A_e=10–90 ha`（步长 1 ha），模型将机组数按整台下调。预留地增大使供电上限分段上升，却让 IT 用地上限下降；最大联合容量约 109.5 MW IT，首次达到最大值时 `A_e=20 ha`。平坦段表示多给地不能解除水瓶颈。 | [CSV](fig03_land_tradeoff.csv) |
| **图 4 储能的功率／电量双重限制**：[中文 PNG](fig04_storage_cycle_zh.png) · [中文 PDF](fig04_storage_cycle_zh.pdf) · [英文 PDF](fig04_storage_cycle.pdf) | **仅绘电力子模型的自发电可靠增量，不是三资源联合容量。** 50 MW 光伏使用人为构造的 24 个一小时时段：`r_t=max(0,50 sin(pi(t-6)/12)) MW`；电池充放电上限各 30 MW、充放电效率各 0.9，周期首尾电量相同。左侧绘可用发电、可靠恒定增量、充放电和 `E=100 MWh` 的期初电量；右侧把电池可用电量从 0 扫至 240 MWh。100 MWh 时可靠增量约 6.9 MW，200 MWh 后约 13.4 MW 不再提高；高能量不等于无限容量，仍受可用日照与损耗约束。只解释这个合成昼夜周期。 | [容量 CSV](fig04_storage_sweep.csv) · [调度 CSV](fig04_storage_dispatch.csv) |
| **图 5 投运年份与候选集**：[中文 PNG](fig05_commissioning_zh.png) · [中文 PDF](fig05_commissioning_zh.pdf) · [英文 PDF](fig05_commissioning.pdf) | 图 1 的纯电网、光储、湿冷燃气、干冷燃气和煤电依次设为 2026／2028／2029／2030／2032 年投运；评估年 2026–2033，其他资源、设备和服务假设固定。虚线为当年之后可选的单方案容量，深灰阶梯是 `P_max(y)`：90.0 → 98.3 → 130.0 MW IT。2029 年增加湿冷燃气、2032 年增加煤电均未提高最佳值。年份只筛选候选，不自动改气象、水文或单方案容量；投运年纯属情景设定。 | [CSV](fig05_commissioning.csv) |

图 1 的 `P_W` 是模型在独立水预算下计算的单项上限，可能高于 `P_E`，此时不意味着超出电力上限后仍能运行。图 4 的 `L` 是光储稳定**附加设施功率**，换算成 IT 功率须与电网一起除以设施倍率 `k`；不能将图 4 的 MW 直接与其他图的 MW IT 混用。图 2 的分类在两约束精确并列时采用模型返回的第一项，精确并列仍会完整写入 CSV 的 `binding` 列。

## 每张图能说明什么，不能说明什么

1. **图 1：资源上限不能跨方案拼接。** 同样的电网和土地总量下，煤电电力上限最高，联合结果却因耗水降至约 93.2 MW IT；湿冷与干冷燃气使用相同机组，在所设 WUE 与耗水系数下分别由水和土地触顶。这是 `min` 的直接结果，能说明技术选择改变**瓶颈**，并且“各技术中最好的电力值、最好的水值和最好的土地值”不能拼成一套不存在的配置。图中所有方案的实际燃料、水源交付、用地许可和电源排放都未校验；尤其干冷可能增加风机／压缩机功率，使设计倍率 `k` 上升，而本图把 `k=1.2` 固定，因此干冷方案的 130 MW IT 不能解读为现实中必然优于湿冷。煤、气耗水系数与风光两时段数据都是刻意选取的情景数，不是跨国技术均值。

2. **图 2：投入更多资源是否有效，取决于当前瓶颈。** 在右图青绿色区域，增加电网交付功率通常不能等比例增加额定 IT 容量，因为耗水预算先触顶；在右上橙色区域继续增加水和电也无法越过 130 MW IT 的土地上限。右图三块区域的形状来自模型的分段供电与水量关系：电网优先供电，只有设施负荷超过电网时才调用燃机并计算其耗水。作为双参数敏感性图是合理的；但 `40–180 MW` 与 `60–260 m³/h` 是探查网格，不是某地区资源概率分布，颜色面积**不代表**出现该瓶颈的概率。某些网格点可能无法获得实际并网或取水许可。

3. **图 3：发电用地是共同约束下的设计变量。** 在 10 ha 时只能布置一台燃机，20 ha 时可以布置两台，故蓝线和联合容量出现整机台阶；20–约 60 ha 的平坦段由水量控制，继续预留用地对 IT 容量没有收益；之后土地上限下降，容量随之下降。这个结果与补充稿的 `A_e` 约束和“并列最优取较小用地”规则一致。模型把未用完的预留地仍从 IT 用地中扣除，这是**规划预留**而非实际占满面积的口径。现实中机组与园区布局未必能按每台固定 10 ha 和每 MW 固定 1 ha 整齐扩建，另有接线、退距、成本及生态敏感性；因此 20 ha 不是某地的推荐方案。

4. **图 4：装机功率与可连续供电功率不同。** 合成光伏在夜间为零；无电池时可以增加白天电量，却无法独自提高全天恒定供电增量。增大可用电量后，模型将白天余电充入、夜间放出；达到约 200 MWh 后，发电时序、效率及固定的 30 MW 充放电功率使收益饱和。图示满足模型附录 A 的周期首尾电量相等，因而不会靠一次性放空电池“创造”持续容量。太阳辐照是光滑的单个合成日，假定此日无限重复、没有连续阴天、温度联动、退化或故障；13.4 MW 仅是这条序列的设施侧稳定增量，绝不是装机 50 MW 的实际场址可靠容量，更不能直接作为 MW IT。

5. **图 5：建设时点只改变可选集合。** 2028 年光储投运使最佳值从 90.0 升到 98.3 MW IT；2029 年湿冷燃气虽已投运，但其约 96.2 MW IT 低于光储，所以最优值不动；2030 年干冷燃气使其升到 130.0；2032 年煤电投运同样没有改善。这验证了 `max_{x in X_y} P(x)` 的筛选逻辑，不能被理解成设施随年份自然扩容。该图人为固定电网、气象、水文、土地和设备效率到 2033 年，现实中这些量会变化；投运日期也是情景输入，不能作为燃机交付期预测。若要做真实的逐年预测，应为每年重新取得同口径数据并单独运行。

**论文写法建议：** 主文把图 1 作为“联合判据与技术差异”，图 2 作为“触顶条件的参数区域”，图 3 作为“发电用地的资源权衡”；图 4 说明时序约束的物理含义，图 5 说明交付期如何进入候选集。正文只能称这些数值为“合成情景计算示例”。若要回答题目要求的真实量级以及与 950／2263 MW、5 GW 的差异，还必须换入同一场址、同一设计期的可交付电力、可分配水、可建设用地和设计效率；本图组本身不提供这种校准。

## Abilene site supplement

`fig06_abilene_binding_zh.png` and its English counterpart show twelve static Abilene scenarios from `data/primary_20261121/outputs/04_design_sensitivity.csv`. The left panel is the conditional electricity-land ceiling `min(P_E,P_L)` in MW IT; the right panel labels the binding electricity or land constraint. The star marks the 1.30 multiplier and 100% gross-site baseline. Water WUE and the project design-hour deliverable amount remain unresolved, so this is not a verified three-resource `P_max`. The 1 GW station engineering rating is also treated as fully deliverable only by assumption. Do not combine this figure with the synthetic figures' numerical settings or treat colored cell area as a probability.

Run `python visualize/plot_abilene.py` after `python data/primary_20261121/scripts/build_abilene.py` to regenerate the bilingual PNG/SVG and CSV. The script also refreshes `00_output_index.csv`, recording each figure file's input, meaning, conditions and use. It leaves `plot_q1.py` and the five existing synthetic figures unchanged.
