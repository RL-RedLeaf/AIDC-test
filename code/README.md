# IMMC 2027 A 题第一问：给定场址的电、水、土地容量

依据 [Q1 正文](../正稿/Q1-v0/正文Q1.md) 式 (1)–(16)。从仓库根目录运行：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

## 三种入口

程序有三条等价的入口。YAML 用于保存输入，JSON 用于保存完整输出。JSON 文件不能作为
输入配置重新传入程序。

### 1. YAML 文件入口

适合保存真实场址数据、批量比较和复现实验。最小联合模型见
[q1_minimal.yaml](examples/q1_minimal.yaml)：

```yaml
model: q1
site: 示例场址
assessment_year: 2028
period_note: 单个设计日
service_level: 正常运营，持续满载

P_grid_mw: 120
k_factor: 1.20

water:
  basis: consumption
  policy_m3_h: 180
  wue_l_per_kwh_it: 1.50

land:
  effective_ha: 160
  ha_per_mw_it: 1.0

scenarios:
  - name: 纯电网
    type: grid
    online_year: 2028
```

运行：

```powershell
python code/run.py code/examples/q1_minimal.yaml --json code/examples/q1_minimal_result.json
```

这个例子的水上限为 \(180/1.5=120\) MW IT，土地上限为 \(160/1=160\) MW IT，
电力上限为 \(120/1.2=100\) MW IT，因此联合容量是 100 MW IT，瓶颈为电力。

完整示例见 [q1_site.yaml](examples/q1_site.yaml)，其中包含纯电网、光储、燃气湿冷、
燃气干冷和未来投运的煤电方案。示例数字全部是合成验收数据，不是场址实测值。

### 2. 控制台输入向导

不提供 YAML 时自动进入中文向导。也可以显式指定 `--interactive`：

```powershell
python code/run.py
python code/run.py --interactive
```

向导的顺序如下：

1. 选择联合模型（电、水、土地）或仅电力分项。
2. 输入场址名称、评估年份、设计期说明和服务水平。方括号中的值是默认值，直接回车即可采用。
3. 选择电网输入方式。MW 直接填写有功功率，MVA 会继续询问功率因数。
4. 填写共享关口容量 `C_PCC_mw`。留空表示专用接线，不设置共享关口上限。
5. 填写联合模型时，再填写水量口径、WUE 和至少一个水量上限。水量上限可填 `source_m3_h`、`stress_m3_h`、`policy_m3_h`，至少一项不能为空。
6. 填写有效用地、IT 侧固定用地、边际用地强度和本地发电用地份额。
7. 选择方案类型，并按提示填写该类型的设备参数。风电和光伏的时间序列用逗号或空格分隔，例如 `20, 0`。
8. 选择是否继续添加方案。可以一次输入多套方案进行横向比较。
9. 输入 JSON 输出路径。留空只在终端输出表格；指定路径则同时写出完整 JSON。

数值格式错误会重新询问。配置通过校验后会先计算每个方案的电、水、土地上限，再取每套方案的最小值和候选集的最大值。

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

第二个参数可写 JSON 路径。路径的父目录必须已经存在：

```python
report = calculate(
    {
        "P_grid_mw": 120,
        "k_factor": 1.2,
        "scenarios": [{"type": "grid", "name": "纯电网"}],
    },
    "result.json",
)
```

交互入口也可以传入自定义的输入函数和输出函数，便于嵌入其他程序：

```python
from immc_power_capacity.interactive import run_interactive

run_interactive(asker=input, say=print)
```

## YAML 输入详解

### 顶层字段

| 字段 | 是否必填 | 单位或取值 | 说明 |
|---|---|---|---|
| `model` | 联合模型必填 | 字符串 `q1` | 没有该字段时按仅电力分项解释。 |
| `site` | 联合模型必填 | 字符串 | 场址名称，仅用于标识和输出。 |
| `assessment_year` | 联合模型必填 | 整数年份 | 只比较当年已经投运的配置。 |
| `period_note` | 联合模型必填 | 字符串 | 说明设计期和结果可解释的时间范围。 |
| `service_level` | 联合模型必填 | 字符串 | 说明服务要求，例如“正常运营，持续满载”。 |
| `P_grid_mw` | 与 MVA 二选一 | MW | 接入点可持续交付的净有功。 |
| `P_grid_mva`、`power_factor` | 与 MW 二选一 | MVA、无量纲 | 按 \(P_{\mathrm{grid}}=S_{\mathrm{grid}}\cos\varphi\) 换算，并在结果中标注为初筛上界。 |
| `C_PCC_mw` | 可选 | MW 或 `dedicated` | 园区共享关口容量。省略或写 `dedicated` 表示不设共享关口上限；填数字时总进线不得超过该值。方案内也可覆盖。 |
| `k_factor` | 必填 | 无量纲，\(\ge 1\) | 设计满载设施总功率除以 IT 功率。方案内可覆盖。 |
| `water` | 联合模型必填 | 对象 | 水量上限、WUE 和水口径。详见下表。 |
| `land` | 联合模型必填 | 对象 | 有效用地、固定用地、边际用地强度。详见下表。 |
| `scenarios` | 必填 | 非空列表 | 至少一套供电方案。每项必须有 `name` 和 `type`。 |
| `sensitivity` | 可选 | 对象 | 参数名到取值列表的映射。每项单独替换基准值后重算。 |

`P_grid_mva`、`power_factor`、`water`、`land` 和 `sensitivity` 用于联合模型。
仅电力分项直接填写 `P_grid_mw`，其余字段按后文“电力分项字段与单位”处理。

联合模型的计算顺序是：

1. 读取顶层默认值。
2. 用方案内的 `k_factor`、`wue_l_per_kwh_it` 和 `generation_share` 覆盖对应默认值。
3. 排除 `online_year > assessment_year` 的方案。
4. 对每套方案计算 \(P_E\)、\(P_W\)、\(P_L\)，取三者最小值。
5. 在剩余方案的 \(P\) 中取最大值，输出并列优胜者。

### 水源字段

`water.basis` 必须填 `consumption`（耗水）或 `withdrawal`（取水）。水量上限和 WUE
必须使用同一口径。WUE 的单位是 L/kWh IT。

| 字段 | 是否必填 | 单位 | 说明 |
|---|---|---|---|
| `basis` | 必填 | 枚举 | `consumption` 或 `withdrawal`。 |
| `wue_l_per_kwh_it` | 必填 | L/kWh IT | 可按方案覆盖。填 0 表示现场没有该类用水需求，JSON 的 \(P_W\) 为 `null`。 |
| `source_m3_h` | 至少一项水量上限 | m³/h | 水源扣除生态保留和既有取水后的可用上限。 |
| `stress_m3_h` | 至少一项水量上限 | m³/h | 按本地水压力阈值允许的新增取水上限。 |
| `policy_m3_h` | 至少一项水量上限 | m³/h | 许可、合同或政策允许的上限。 |
| `river_m3_h`、`eco_m3_h`、`other_m3_h` | 可选 | m³/h | 仅用于取水口径推算水源上限，三项需成组提供。已有实测流量时不要再扣一次上游取水。 |
| `stress_fraction` | 可选 | 无量纲，[0,1] | 仅用于取水口径推算压力上限。 |
| `period_budget` | 可选 | 对象 | 总量型水量预算，字段见下。 |

`river_m3_h`、`eco_m3_h`、`other_m3_h` 和 `stress_fraction` 需要一起使用。只填
`stress_fraction` 无法单独推算压力上限，程序会把它当作水源数据不完整。

`period_budget` 的写法：

```yaml
water:
  basis: consumption
  wue_l_per_kwh_it: 1.5
  period_budget:
    limit: policy
    volume_m3: 1200
    hours: 24
    it_load_factor: 0.8
```

`limit` 表示这个总量属于 `source`、`stress` 或 `policy` 中的哪一项。程序先将总量除以
`hours` 换成 m³/h，再除以 `it_load_factor` 得到与额定容量对应的等效设计流量。该字段
适合有“月度/年度总量”许可的场景，不替代瞬时取水能力校核。

至少填写一个独立水量上限。没有资料的项会出现在 JSON 的 `omitted` 中，不能把缺失项当成无穷大。

### 土地字段

| 字段 | 是否必填 | 单位 | 说明 |
|---|---|---|---|
| `effective_ha` | 必填 | ha | 场址筛选后的有效用地。 |
| `fixed_it_ha` | 可选 | ha | 道路、管理区等 IT 侧固定用地，默认 0。填 0 是乐观上界。 |
| `ha_per_mw_it` | 必填 | ha/MW IT | 园区本体、变配电和冷却设施的边际用地强度。 |
| `generation_share` | 可选 | [0,1] | 本地发电及专属配套用地占有效用地的份额，默认 0。可按方案覆盖。 |
| `scenario.local_generation_required_ha` | 可选 | ha | 方案的本地发电地块实际需求。超过预留面积时该方案被排除。 |

土地上限为：

\[
P_L=\frac{A_{\mathrm{eff}}(1-\kappa)-A_0^{\mathrm{IT}}}{a_{\mathrm{site}}}.
\]

分子小于等于零时返回 0 MW IT，表示在该设计下没有可建设的正容量。

### 方案字段

所有方案共有的字段：

| 字段 | 是否必填 | 说明 |
|---|---|---|
| `name` | 必填 | 方案名称，必须唯一。 |
| `type` | 必填 | `grid`、`coal`、`gas`、`wind`、`hydro`、`solar`、`combined_battery` 之一。 |
| `online_year` | 联合模型必填 | 投运年份。大于 `assessment_year` 时进入 `excluded`。 |
| `k_factor` | 可选 | 覆盖该方案的设施倍率。 |
| `wue_l_per_kwh_it` | 可选 | 覆盖该方案的 WUE。 |
| `generation_share` | 可选 | 覆盖该方案的发电用地份额。 |
| `C_PCC_mw` | 可选 | 覆盖共享关口容量。 |

各类型专属字段：

| 类型 | 必填字段 | 可选字段 |
|---|---|---|
| `grid` | 无 | 无 |
| `coal` | `units`、`unit_net_mw` | `net_efficiency` |
| `gas` | `units`、`unit_net_mw` | `net_efficiency`、`gas_supply_adequate` |
| `wind` | `alpha` 或 `power_ratios` 或 `net_output_mw`，以及装机参数 | `installed_mw` 或 `area_km2 + density_mw_per_km2` |
| `hydro` | `installed_mw`、`flow_m3_per_s`、`net_head_m`、`efficiency` | 无 |
| `solar` | `area_km2`、`density_mw_per_km2`、`dt_hours`、`supply_ratios` 或 `net_output_mw` | `battery` |
| `combined_battery` | `installed_mw`、`dt_hours`、`supply_series_mw`、`battery` | 无 |

方案示例：

```yaml
scenarios:
  - name: 纯电网
    type: grid
    online_year: 2028

  - name: 煤电
    type: coal
    online_year: 2028
    units: 2
    unit_net_mw: 80
    net_efficiency: 0.38

  - name: 燃气
    type: gas
    online_year: 2028
    units: 1
    unit_net_mw: 60
    gas_supply_adequate: true

  - name: 水电
    type: hydro
    online_year: 2028
    installed_mw: 80
    flow_m3_per_s: 100
    net_head_m: 100
    efficiency: 0.90

  - name: 光储
    type: solar
    online_year: 2028
    area_km2: 0.2
    density_mw_per_km2: 100
    dt_hours: 1
    net_output_mw: [20, 0]
    battery:
      C_max_mw: 10
      D_max_mw: 10
      E_usable_mwh: 10
      charge_efficiency: 0.95
      discharge_efficiency: 0.95
```

风电和光伏的时间序列表示同一考察期内的逐时段净功率，单位是 MW。序列长度必须一致，
不能包含 `null`、负数或缺失值。光伏还可以用 `supply_ratios` 提供“逐时净功率除以装机”的
无量纲序列。

并网风电请在 `net_output_mw` 或 `power_ratios` 中提供同期序列。当前实现采用恒定可交付
电网加最低风电出力的确定性口径。孤立场址可以把 `P_grid_mw` 设为 0，并直接填写 `alpha`。
年度容量因子不能替代这里的考察期保障比例。

电池字段统一为：

| 字段 | 单位 | 说明 |
|---|---|---|
| `C_max_mw` | MW | 最大充电功率。 |
| `D_max_mw` | MW | 最大放电功率。 |
| `E_usable_mwh` | MWh | 扣除应急预留后的可用电量。 |
| `charge_efficiency` | 无量纲，(0,1] | 充电效率，省略时按 1。 |
| `discharge_efficiency` | 无量纲，(0,1] | 放电效率，省略时按 1。 |

### 敏感性配置

`sensitivity` 的键是字段路径，值是依次尝试的取值列表：

```yaml
sensitivity:
  P_grid_mw: [96, 120]
  k_factor: [1.3, 1.4]
  water.wue_l_per_kwh_it: [1.0, 2.0]
  water.stress_fraction: [0.4, 0.6]
  land.ha_per_mw_it: [0.8, 1.2]
  land.effective_ha: [140, 180]
```

每个取值单独替换基准配置后重算，不把多个参数同时改变。当前支持的路径是
`P_grid_mw`、`C_PCC_mw`、`k_factor`、`water.wue_l_per_kwh_it`、
`water.stress_fraction`、`land.effective_ha`、`land.ha_per_mw_it` 和
`land.generation_share`。方案自身覆盖了某个默认值时，改变顶层默认值不会覆盖该方案。
`water.stress_fraction` 需要基准配置已经提供 `river_m3_h`、`eco_m3_h` 和
`other_m3_h`，否则该敏感性项无法单独计算。

### 常见 YAML 错误

| 写法 | 结果和修改方式 |
|---|---|
| 只写 `P_grid_mva`，没有 `power_factor` | 报错。补充功率因数，或改用 `P_grid_mw`。 |
| 水量没有 `source_m3_h`、`stress_m3_h`、`policy_m3_h` 中任何一项 | 报错。至少填写一项独立上限。 |
| `k_factor: 0.9` | 报错。设计要求 \(k\ge 1\)。 |
| 电池功率字段写成 `C_max_mwh` 或 `D_max_mwh` | 报错。功率用 `_mw`，能量用 `_mwh`。 |
| 光伏只有 `dt_hours`，没有出力序列 | 报错。补充 `net_output_mw` 或 `supply_ratios`。 |
| 并网风电只写 `alpha` | 报错。并网场景需提供同期序列。 |
| `online_year` 晚于 `assessment_year` | 不报错，方案进入 `excluded`，不参与当年比较。 |
| `C_PCC_mw` 省略 | 按专用接线处理，不设置共享关口上限。 |

## JSON 输出详解

### 写出 JSON

命令中的 `--json` 参数指定结果文件。它是输出路径，不是输入配置路径：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

程序只在计算成功后写文件，父目录必须已经存在。相对路径相对于当前工作目录，不是 YAML 文件所在目录。

联合模型的 JSON 顶层结构如下：

```text
{
  "site": "...",
  "assessment_year": 2028,
  "period_note": "...",
  "inputs": { ... 原始输入 ... },
  "service_level": "...",
  "grid_basis": "...",
  "water": {
    "basis": "consumption",
    "limits_m3_h": { ... },
    "Q_max_m3_h": 120.0,
    "design_equivalent_m3_h": 120.0,
    "period_budget": null,
    "omitted": []
  },
  "scenarios": [
    {
      "name": "...",
      "power_type": "...",
      "breakdown": { ... },
      "method": { ... },
      "online_year": 2028,
      "land": { ... },
      "P_E_mw_it": 100.0,
      "P_W_mw_it": 120.0,
      "P_L_mw_it": 160.0,
      "P_mw_it": 100.0,
      "binding": ["电力"]
    }
  ],
  "excluded": [ ... ],
  "P_max_mw_it": 100.0,
  "winners": ["..."],
  "sensitivity": [ ... ]
}
```

### 顶层字段

| JSON 字段 | 单位或类型 | 含义 |
|---|---|---|
| `site`、`assessment_year`、`period_note`、`service_level` | 字符串或整数 | 本次比较采用的场址、年份、设计期和服务水平。 |
| `inputs` | 对象 | 实际传给模型的输入，包含 YAML 中的默认值和方案覆盖值，便于复现。 |
| `grid_basis` | 字符串 | 电网功率口径，例如“接入点持续净有功”或“MVA × 功率因数，初筛上界”。 |
| `water` | 对象 | 水量上限计算后的结果，不只是 YAML 中的原始输入。 |
| `scenarios` | 数组 | 未被工期或发电用地条件排除的方案结果。 |
| `excluded` | 数组 | 未进入比较的方案，含 `name`、`online_year` 和 `reason`。 |
| `P_max_mw_it` | MW IT | 当年可行方案中的最大联合容量。 |
| `winners` | 字符串数组 | 达到 `P_max_mw_it` 的方案，可能有并列。 |
| `sensitivity` | 数组 | 每个敏感性参数替换值对应的重算结果。 |

`water` 中各字段的含义：

| 字段 | 单位 | 说明 |
|---|---|---|
| `limits_m3_h` | m³/h | 实际参与最小值的各项独立水量上限。 |
| `Q_max_m3_h` | m³/h | `limits_m3_h` 的最小值。 |
| `design_equivalent_m3_h` | m³/h | 经过 `period_budget.it_load_factor` 换算后的设计流量。没有总量预算时与 `Q_max_m3_h` 相同。 |
| `omitted` | 字符串数组 | 没有提供的独立上限项，提醒读者不要把它们当成无穷大。 |
| `period_budget` | 对象或 null | 本次是否使用了总量型水量预算。 |

### 单方案结果

每项 `scenarios` 都同时给出电力、水、土地三个上限和联合结果：

| 字段 | 单位 | 说明 |
|---|---|---|
| `P_E_mw_it` | MW IT | 电力子模型上限，已经除以 \(k\)。 |
| `P_W_mw_it` | MW IT 或 null | 水子模型上限。WUE 为 0 时为 null。 |
| `P_L_mw_it` | MW IT | 土地子模型上限。 |
| `P_mw_it` | MW IT | \(\min(P_E,P_W,P_L)\)，即该方案可用于后续比较的容量。 |
| `binding` | 字符串数组 | 达到该方案最小值的约束。多个值表示并列瓶颈。 |

`breakdown` 给出电力链的中间量：

| 字段 | 单位 | 说明 |
|---|---|---|
| `grid_mw` | MW | 计入的电网功率。 |
| `self_generation_mw` | MW | 自建电源持续净增量。 |
| `facility_mw` | MW | 经过 \(C_{\mathrm{PCC}}\) 限制后的园区总功率。 |
| `k` | 无量纲 | 该方案使用的设施倍率。 |
| `it_mw` | MW IT | `facility_mw / k`，与 `P_E_mw_it` 对应。 |
| `C_PCC_mw` | MW 或字符串 | 共享关口容量；专用接线时为 `dedicated`。 |

`land` 给出土地链的中间量：

| 字段 | 单位 | 说明 |
|---|---|---|
| `site_ha` | ha | 扣除发电预留后的园区可用地。 |
| `reserved_generation_ha` | ha | 本地发电及配套预留地。 |
| `fixed_it_ha` | ha | IT 侧固定用地。 |
| `optimistic_zero_fixed` | 布尔 | 固定用地是否按 0 处理。 |
| `P_L_mw_it` | MW IT | 该方案的土地上限。 |

### 光储调度字段

有电池的 `solar` 或 `combined_battery` 方案，`method` 中会有逐时调度，数组长度等于输入序列长度：

| 字段 | 单位 | 说明 |
|---|---|---|
| `L_mw` | MW | 光储模型求出的最大恒定附加负荷。 |
| `charge_mw` | MW | 每个时段的充电功率。 |
| `discharge_mw` | MW | 每个时段的放电功率。 |
| `energy_start_mwh` | MWh | 每个时段开始时的可用电量。 |
| `curtailment_mw` | MW | 每个时段的弃电功率。 |
| `direction` | 0/1 数组 | 1 表示该时段允许充电，0 表示允许放电。 |
| `battery` | 对象 | 求解使用的充电功率、放电功率、电量和效率参数。 |
| `status` | 字符串 | HiGHS 的返回状态。 |

例如两时段 `[20, 0]` MW、电池 10 MW/10 MWh 的结果中，`charge_mw` 为 `[10, 0]`，
`discharge_mw` 为 `[0, 10]`，`energy_start_mwh` 为 `[0, 10]`。这组数组可以直接用于
复核功率平衡、周期电量和充放互斥。

### 敏感性和排除项

`sensitivity` 的每一项都有：

```text
parameter    被替换的字段路径
value        本次替换值
P_max_mw_it  重算后的场址最大值
winners      本次优胜方案
scenarios    每个方案的 P_mw_it 和 binding
```

`excluded` 只记录没有进入当年比较的方案，不等同于“方案不可行”。常见原因是尚未投运，
或者本地发电及配套用地超过预留面积。若所有方案都被排除，程序会直接报错。

### 仅电力分项 JSON

没有 `model: q1` 时，JSON 结构是：

```text
{
  "assumptions": {
    "P_grid_mw": 120,
    "k_factor": 1.2,
    "k_source": "...",
    "period_note": "..."
  },
  "scenarios": [
    {
      "name": "...",
      "power_type": "...",
      "breakdown": { ... },
      "method": { ... }
    }
  ],
  "optimum": { ... }
}
```

此时没有 `P_max_mw_it`、`winners`、`P_W_mw_it` 和 `P_L_mw_it`。`optimum` 是按
`breakdown.it_mw` 取最大值的单套方案。

## 电力分项运行

以下旧版示例采用专用接线，不与联合模型的水、土地字段混用。

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

## 电力分项字段与单位

以下字段用于没有 `model: q1` 的仅电力分项模式。

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

## 电力分项输出与复核

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
