# IMMC 2027 A 题第一问：给定场址的电、水、土地容量

依据 [Q1 正文](../正稿/Q1-v0/正文Q1.md) 式 (1)–(16)。从仓库根目录运行：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

## 三种入口

### 1. YAML 文件入口

适合保存场址参数、批量比较和复现实验。示例见 [q1_site.yaml](examples/q1_site.yaml)。

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

### 2. 控制台输入向导

不提供配置文件时自动进入中文向导。也可以显式使用 `--interactive`：

```powershell
python code/run.py
python code/run.py --interactive
```

向导支持联合模型（电、水、土地）和仅电力分项两种模式，会逐步询问场址、电网、
水电土地参数以及一套或多套供电方案。直接回车采用方括号中的默认值。最后的 JSON
路径留空时只在终端显示结果。

### 3. Python 函数入口

`run.py` 现在是可导入模块，`calculate()` 和 `run()` 都同时接受配置字典和 YAML 路径：

```python
import sys
sys.path.insert(0, "code")
from run import calculate

report = calculate({
    "P_grid_mw": 120,
    "k_factor": 1.2,
    "scenarios": [{"type": "grid", "name": "纯电网"}],
})
print(report["scenarios"][0]["breakdown"]["it_mw"])  # 100.0
```

第二个参数可写 JSON 路径：

```python
report = calculate({"P_grid_mw": 120, "k_factor": 1.2,
                    "scenarios": [{"type": "grid", "name": "纯电网"}]},
                   "result.json")
```

交互入口同样可以传入自定义的输入函数，便于在其他程序中复用：

```python
from immc_power_capacity.interactive import run_interactive

run_interactive(asker=input, say=print)
```

[可替换的完整配置](examples/q1_site.yaml) 使用合成数据。每份配置代表一个场址、一个设计期和一种服务要求。
以 `online_year <= assessment_year` 为已投运，先逐配置取电、水、土地容量的最小值，再在当年候选集中选最大值。
输出保留并列瓶颈、并列最优、被工期排除的方案、输入参数和逐时电池调度。演示得到 110 MW IT（燃气配干冷园区，土地先触顶）。

| 配置项 | 单位或填写口径 |
|---|---|
| `site`、`assessment_year`、`period_note`、`service_level` | 场址、评估年份、共同设计期、服务要求。每个方案填投运年 `online_year`。 |
| `P_grid_mw`、`C_PCC_mw` | 接入点可持续交付 MW、共享关口可送 MW；专用接线显式写 `dedicated`。关口可按方案覆盖。也可填 `P_grid_mva` 和 `power_factor`，结果标为初筛上界。 |
| `k_factor`、风光序列、设备参数 | 满载设施/IT 倍率可按配置覆盖。并网风电采用恒定电网加同期净出力的逐时平衡，其最小值等于电网加最低风电出力；孤立场址填零电网，可直接给保障比例。ELCC 需要系统可靠性数据，此入口采用确定性口径。 |
| `water.basis`、`wue_l_per_kwh_it` | `consumption` 为耗水，`withdrawal` 为取水。所有水量和园区 WUE 共用这一口径和设计期。WUE 单位 L/kWh IT，可按冷却方案覆盖；设施侧 WUE 应先乘相应的满载倍率。显式零 WUE 表示现场无此用水需求，JSON 的水上限为 null。 |
| `source_m3_h`、`stress_m3_h`、`policy_m3_h` | 直接提供同口径独立上限（m³/h）；未给项列入 omitted。取水模式也可给 `river_m3_h`、`eco_m3_h`、`other_m3_h` 推算水源上限，给 `stress_fraction` 推算压力上限。既有取水只扣一次。1 m³/h 除以 1 L/kWh IT 对应 1 MW IT。 |
| `water.period_budget` | 可选总量上限，填 `limit`（source/stress/policy）、`volume_m3`、`hours` 和同期 `it_load_factor`。该项等效额定功率为总量除以时长、负载率与 WUE；时段总量只约束时段平均，瞬时设计流量须另有依据。 |
| `land.effective_ha`、`fixed_it_ha`、`ha_per_mw_it`、`generation_share` | 有效用地 ha、IT 侧固定面积 ha、园区边际强度 ha/MW IT、本地发电及专属配套份额。份额可按配置覆盖；异地用地另计。固定面积省略或为零时标注乐观上界。有效余地不足时可建设的正容量为零。 |
| `sensitivity` | 示例对 6 个参数逐个改变，每次从基准配置重算；JSON 保存各方案的新容量、瓶颈与优胜者。场址默认值的变化只作用于采用该默认值的配置。 |

有本地发电地块设计时，方案中填 `local_generation_required_ha`，超过预留面积的建成配置排除。
电力分项仍可独立运行，以下旧版示例采用专用接线。

## 电力分项运行

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

采用 SciPy `linprog` / HiGHS。稀疏矩阵的非零项数与时段数成正比。第一次求最大恒载，第二次固定该恒载并最小化期初电量。
GreenSwitch §5.2 式 (6)–(13) 给出功率和电量关系，式 (17) 要求充放互斥。这里利用允许弃电、效率不超过 1、目标仅取决于恒载的条件，先解连续 LP，再重建单向调度。

令每小时净入库电量率 $b_t=\eta_c c_t-d_t/\eta_d$。取 $c'_t=\max(b_t,0)/\eta_c$、$d'_t=\max(-b_t,0)\eta_d$，
每个时段至少有一项为零，两项分别不超过原充放功率。电池净入库量和逐时荷电状态相同，减少的循环损耗进入弃电，
所以原最优恒载仍可达。程序校核剩余功率与循环电量后导出。原论文含售电、购电与电价目标，采用 Gurobi MILP。

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
| `k_factor` | 无量纲，≥1 | 设计满载设施总功率 / IT 功率。 |
| `scenarios[].k_factor` | 无量纲，≥1 | 可选；覆盖该方案的 `k(x)`，缺省使用顶层值。 |
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
2. **充放互斥与不等式。** v2 附录 A 要求同一时段只采用一种充放方向；GreenSwitch
   原文 §5.2 式（17）也明确写了不能同时充电和放电。若用纯 LP 处理式 (A1) 的不等式，
   可能生成同时充放的等价数学解。本实现按上式重建单向调度。
3. **电池能否使用电网充电。** GreenSwitch 原文式 (8) 设有 `BattBrown`，允许电网给
   电池充电；v2 附录则说明只核算自建电源净增量，但没有用一句话明确禁止使用
   `P_grid`。本实现按 v2 的边界解释为**不允许**，否则电池会把外层电网容量变成额外的
   可调度能量，改变 `P_E`。这是本实现中最需要和论文口径保持一致的一处。
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
