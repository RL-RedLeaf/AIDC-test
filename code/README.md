# IMMC 2027 A 题第一问：电力承载上限模型

本目录实现 v2 的式 (1)–(6) 与附录 A，输入一套场址供电配置，输出每种方案的
电网功率、自建电源可靠净功率、设施总功率、满载倍率 `k` 与最大额定 IT 容量。

## 一条命令运行

在仓库根目录执行：

```powershell
python code/run.py code/examples/example_supply.yaml --json code/examples/example_result.json
```

若已进入 `code/` 目录，也可以执行：

```powershell
python -m immc_power_capacity examples/example_supply.yaml --json examples/example_result.json
```

两时段手算验收配置可直接复现：

```powershell
python code/run.py code/examples/acceptance_manual.yaml --json code/examples/acceptance_manual_result.json
```

预期输出为：纯电网 `P_E=100` MW IT；光伏无电池 `P_self=0`；光伏+电池
`P_self=10` MW、`P_total=130` MW、`P_E=108.333` MW IT。其调度为第一小时
充电 10 MW、第二小时放电 10 MW，电量序列为 `[0, 10]` MWh。

依赖见 `requirements.txt`。最低环境为 Python 3.11、NumPy、SciPy（含 HiGHS）、PyYAML；
`pytest` 仅用于运行验收测试。

## 演示结果

下面的数字全部来自 `examples/example_supply.yaml`，是**演示测试数据**，不是项目场址实测值。

| 方案 | P_grid MW | P_self MW | 设施总 MW | k | P_E MW IT |
|---|---:|---:|---:|---:|---:|
| 纯电网 | 120 | 0 | 120 | 1.20 | 100 |
| 煤电 | 120 | 160 | 280 | 1.20 | 233.333 |
| 燃气 | 120 | 150 | 270 | 1.20 | 225 |
| 风电 | 120 | 28 | 148 | 1.20 | 123.333 |
| 水电 | 120 | 80 | 200 | 1.20 | 166.667 |
| 光伏无电池 | 120 | 0 | 120 | 1.20 | 100 |
| 光伏+电池 | 120 | 20.8 | 140.8 | 1.20 | 117.333 |
| 风光共用电池 | 120 | 63.1333 | 183.133 | 1.20 | 152.611 |

演示配置是一个 24 小时代表日。上表只解释该代表日；不能据此直接宣称全年可靠容量。

## 计算模型

对方案 `x`：

```text
P_total(x) = P_grid + P_self(x)
P_E(x)     = P_total(x) / k(x)
```

`P_grid` 只在外层加入一次。`P_self` 是考察期内自建电源持续、净可靠地补充给园区的
功率。`k` 是设计满载时设施总功率与 IT 功率之比；以年度 PUE 代入时是近似，配置中的
`k_source` 必须注明口径。

各电源接口：

- 纯电网：`P_self = 0`。
- 煤电、燃气：`P_self = 可同时运行台数 × 单机持续净功率`。净功率必须已扣厂用电。
  燃气仅在声明供气充足时作为容量上界；可选净效率只用于反推所需燃料热功率。
- 风电：`P_self = A_wind × rho_wind × alpha`。`alpha` 可直接给出来源，也可由同期
  归一化序列或原始 MW 序列取最小值得到。年度容量因子不进入这个式子。
- 水电：`P_self = min(装机 MW, 0.00981 × 综合效率 × 可用流量 m³/s × 净落差 m)`。
- 光伏：无电池时退化为考察期最小净功率；有电池时由附录 A 求全周期最大恒定附加负荷。

## 光储附录与求解方法

严格对应 v2 附录 A：

```text
r_t + d_t = L + c_t + s_t,          s_t >= 0（弃电）
e_(t+1) = e_t + eta_c c_t Δt - d_t Δt / eta_d
0 <= c_t <= C_max
0 <= d_t <= D_max
0 <= e_t <= E_usable
e_(T+1) = e_1
```

程序用 SciPy `milp`（HiGHS）直接求解，并对每个时段加入二进制方向变量 `y_t`：

```text
c_t <= C_max y_t
d_t <= D_max (1 - y_t)
```

因此同一电池在同一时段不会同时充电和放电，不需要线性松弛，也不需要事后重建
互斥调度。目标先最大化 `L`；再固定最优 `L`，以初始电量最小为次级目标导出一组
可复核的充电、放电和荷电量序列。功率与能量平衡式沿用 Goiri 等（ASPLOS 2013）
GreenSwitch §5.2 的关系，目标改为附录 A 的最大恒定附加负荷。

电池只由自建电源的可用余量充电。`P_grid` 已经在式 (1) 外层计入一次，不会再次用于
给附录 A 的电池免费充电。

## 输入字段与单位

输出的 `P_grid`、`P_self` 和设施功率均为园区进线处 MW；`installed_mw` 是电站
装机，`net_output_mw` 是交流侧逐时净功率。`E_usable_mwh` 是能量 MWh；
`C_max_mw`、`D_max_mw` 是功率 MW。程序会明确拒绝 `E_usable_mw`、`C_max_mwh`
等常见错位单位。

| 字段 | 单位 | 说明 |
|---|---|---|
| `P_grid_mw` | MW | 电网正常运行时可持续交付给园区的有功功率。只有 MVA 时先用功率因数换算，并注明是初筛上界。 |
| `k_factor` | 无量纲，>1 | 设计满载设施总功率 / IT 功率。 |
| `scenarios[].k_factor` | 无量纲，>1 | 可选；覆盖该方案的 `k(x)`，缺省使用顶层值。 |
| `coal.units`, `gas.units` | 台（正整数） | 可同时投入正常运行的同型号机组数。 |
| `unit_net_mw` | MW | 当地设计条件下的单机持续净功率，已扣厂用电。 |
| `net_efficiency` | (0,1] | 仅用于报告燃料热功率，不改变净电功率。 |
| `area_km2` | km² | 风/光合格面积，必须是正数。 |
| `density_mw_per_km2` | MW/km² | 装机密度。 |
| `installed_mw` | MW | 可直接给装机；风电也可由面积乘密度求出。 |
| `alpha` | [0,1] | 风电考察期可持续供电比例，需有来源。 |
| `power_ratios` | MWh/MWh，无量纲 | 逐时段净功率 / 装机；风电取最小值作为 alpha。 |
| `net_output_mw` | MW | 逐时段净功率；风电据此除以装机求 alpha，光伏直接作为 `r_t`。 |
| `supply_ratios` | MWh/MWh | 光伏逐时段净功率 / 装机，与原始 MW 序列二选一。 |
| `flow_m3_per_s` | m³/s | 扣除生态下泄及其他用水后的可持续流量。 |
| `net_head_m` | m | 同一约束期的净落差。 |
| `efficiency` | (0,1] | 水电综合转换效率。 |
| `dt_hours` | h | 每个时段长度。 |
| `C_max_mw`, `D_max_mw` | MW | 电池最大充、放功率，配置电池时必须为正。 |
| `E_usable_mwh` | MWh | 已扣除应急预留后的可动用电量，配置电池时必须为正。 |
| `charge_efficiency`, `discharge_efficiency` | (0,1] | 充/放电效率。 |

时间序列中的 `null`、缺失时长、负面积、效率越界和机组台数非整数都会以中文错误信息
退出；无法求解的附录 A 问题也会单独报错。

## 输出与复核

CLI 表格列出每套方案的 `P_grid_mw`、`P_self_mw`、`facility_mw`、`k` 和
`P_E_mw_IT`，并报告候选集中的最大值。`--json` 文件中的光储方案 `method` 额外包含：

- `charge_mw`：逐时段充电功率；
- `discharge_mw`：逐时段放电功率；
- `energy_start_mwh`：逐时段初的可用电量；
- `curtailment_mw`：逐时段弃电功率；
- `direction`：1 表示该时段允许充电，0 表示允许放电；
- `L_mw`：光储方案求得的可靠净增量。

可用以下命令跑验收测试：

```powershell
cd code
pytest -q tests/test_acceptance.py
```

测试覆盖纯电网 100 MW IT、夜间零出力的光伏无储能、`[20,0]` 两时段光储手算例、
非 1 小时步长、风光共用电池、周期能量闭合、充放互斥和常见错误输入。

## 换真实场址时替换什么

1. `P_grid_mw`：接入点核定可交付有功功率；MVA 先换算并标注上界属性。
2. `k_factor`：真实设施同工况满载倍率；若用年度 PUE，记录设施类型和统计周期。
3. 煤/气：`units`、`unit_net_mw`、供气声明、可选 `net_efficiency`。当地高温、冷却水
   或供气约束应已折算到净功率。
4. 风电：`area_km2`、`density_mw_per_km2`、`alpha` 或同期 `power_ratios` /
   `net_output_mw`。
5. 水电：`installed_mw`、`flow_m3_per_s`、`net_head_m`、`efficiency`，并采用要论证的
   枯水期/约束期口径。
6. 光伏与光储：同一组 `net_output_mw` 或 `supply_ratios`、`dt_hours`，以及电池
   `C_max_mw`、`D_max_mw`、`E_usable_mwh` 和效率。

## v2 中影响数值的解释与歧义

1. **初始电量未给定。** 式 (A2) 只给 `0 <= e_t <= E_usable` 和 `e_(T+1)=e_1`，没有
   指定 `e_1`。本实现允许 `e_1` 在整段范围内自由选择，并在所有最优 `L` 中优先取较低
   的初始电量，以便复现调度。若强制某个固定初始电量，结果可能不变，也可能因周期
   边界而下降；这是使用 v2 时需明确的假设。
2. **充放互斥与不等式。** 式 (A1) 的不等式和“同一时段只采用一种方向”若用纯 LP
   处理，可能生成同时充放的等价数学解。本实现用二进制变量严格互斥，不依赖线性松弛。
3. **电池能否使用电网充电。** v2 说明附录只核算自建电源净增量，但没有用一句话明确
   禁止电池从 `P_grid` 取电。本实现解释为**不允许**，否则电池会把外层电网容量变成
   额外的可调度能量，改变 `P_E`。这是本实现中最需要和论文口径保持一致的一处。
4. **风电 alpha 的周期口径。** 式 (3) 的 `alpha` 取考察期最低净出力/装机；它不是
   年度容量因子。若输入代表日，得到的 alpha 只解释该代表日，不能外推全年。
5. **年度 PUE 近似。** 式 (6) 要求设计满载设施倍率 `k`；只有年度 PUE 时属于近似，
   其适用条件是满载辅助用电占比接近全年平均水平，结果应注明为近似。
6. **MVA 到 MW 的功率因数未给定。** v2 允许将变电站开放容量折算为 MW，但没有统一
   功率因数。程序因此只接收 `P_grid_mw`；若只有 MVA，应写明所用功率因数及其上界
   属性，不把 MVA 直接当 MW。
7. **燃气净效率的热值基准未说明。** 净效率按 LHV 还是 HHV 定义会改变燃料热功率
   （通常约差一成），但不改变已给定的净电功率和 `P_E`。本实现原样使用输入比例，
   不做 LHV/HHV 换算；写论文时需与数据来源统一。

## 数据分类

- `examples/example_supply.yaml`：演示假设，不是场址数据。
- `research/A题模型/参数资料/参数汇总表.md`：合作者收集的候选数据，含行业均值和
  文献算例，不能直接当作项目实测。
- 程序输出：基于当前配置和考察期的计算结果，不是对所有年份或所有天气过程的保证。

电力、水、土地三个模块比较时，应让同一套方案共享场址分配口径，再分别取上限并取最小。
