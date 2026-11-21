# IMMC 2027 A 题第一问：给定场址的电、水、土地容量

本目录实现 [权威稿 IMMC2027](../正稿/Q1-v0/IMMC2027/IMMC2027.md) 的电力式（1）–（6）、水模型和土地模型。程序先排除评估年份尚未投运的方案，再对每套方案计算电力、水和土地三个上限，取三者最小值，最后在当年候选集中取最大值。

## 快速开始

在仓库根目录运行最小示例：

```powershell
python code/run.py code/examples/q1_minimal.yaml --json code/examples/q1_minimal_result.json
```

输出应包含：

```text
评估设置
  场址：示例场址
  评估年份 y：2028
...
[1] 纯电网（grid_only）
  电力上限 P_E = 100 MW IT
  水上限 P_W = 120 MW IT
  土地上限 P_L = 160 MW IT
  联合容量 P = 100 MW IT；触顶约束：电力
结论
  P_max = 100 MW IT
  最优配置：纯电网
```

这个结果来自演示数据，不是实际场址数据。完整的合成示例见 [q1_site.yaml](examples/q1_site.yaml)。

## 三条入口

### 1. YAML 文件入口

YAML 保存场址和方案输入。命令中的 `--json` 指定结果文件，路径相对于当前工作目录：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

YAML 顶层采用以下结构：

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

字段单位和填写规则见下文“YAML 输入详解”。每套方案必须使用同一场址、同一设计期和同一服务水平，否则 \(P_{\max}\) 的取最小没有意义。

### 2. 控制台输入向导

不提供 YAML 时自动进入中文向导，也可以显式使用 `--interactive`：

```powershell
python code/run.py
python code/run.py --interactive
```

向导只构建 Q1 联合模型，按以下顺序询问：

每个问题同时给出正稿符号、单位和物理含义，避免把 MVA 当成 MW、把 MWh 当成 MW，或把年度容量因子当成考察期保障比例。

1. 场址名称、评估年份、设计期说明和服务水平。方括号中的值是默认值，直接回车即可采用。
2. 电网输入方式。选择 MW 时填写 `P_grid_mw`（\(P_{\mathrm{grid}}\)）；选择 MVA 时填写 `P_grid_mva`（\(S_{\mathrm{grid}}\)）和功率因数 \(\cos\varphi\)。
3. 水量口径、WUE 和至少一项水量上限（\(Q_{\mathrm{source}},Q_{\mathrm{stress}},Q_{\mathrm{policy}}\)），至少一项不能为空。
4. 有效用地 \(A_{\mathrm{eff}}\)、IT 侧固定用地 \(A_0^{\mathrm{IT}}\) 和边际用地强度 \(a_{\mathrm{site}}\)。
5. 方案类型和设备参数。风电、光伏的逐时序列 \(r_t\) 用逗号或空格分隔，例如 `20, 0`。
6. 是否继续添加方案。可以一次输入多套方案。
7. JSON 输出路径。留空只在终端输出结果；填写路径则同时写出 JSON。

数值格式错误会重新询问。模型校验失败时会在终端给出中文错误信息。

### 3. Python 函数入口

`run.py` 现在是可导入模块。`calculate()` 和 `run()` 都接受配置字典或 YAML 路径：

```python
import sys
sys.path.insert(0, "code")
from run import calculate

report = calculate({
    "model": "q1",
    "site": "示例场址",
    "assessment_year": 2028,
    "period_note": "单个设计日",
    "service_level": "正常运营，持续满载",
    "P_grid_mw": 120,
    "k_factor": 1.2,
    "water": {
        "basis": "consumption",
        "policy_m3_h": 180,
        "wue_l_per_kwh_it": 1.5,
    },
    "land": {
        "effective_ha": 160,
        "ha_per_mw_it": 1.0,
    },
    "scenarios": [{"type": "grid", "name": "纯电网", "online_year": 2028}],
})
print(report["P_max_mw_it"])  # 100.0
```

第二个参数可以指定 JSON 路径，父目录必须已经存在：

```python
report = calculate(
    {
        "model": "q1",
        "site": "示例场址",
        "assessment_year": 2028,
        "period_note": "单个设计日",
        "service_level": "正常运营，持续满载",
        "P_grid_mw": 120,
        "k_factor": 1.2,
        "water": {
            "basis": "consumption",
            "policy_m3_h": 180,
            "wue_l_per_kwh_it": 1.5,
        },
        "land": {
            "effective_ha": 160,
            "ha_per_mw_it": 1.0,
        },
        "scenarios": [{"type": "grid", "name": "纯电网", "online_year": 2028}],
    },
    "result.json",
)
```

## YAML 输入详解

### 符号与代码字段对照

下表按正文符号列出输入字段；YAML 字段名保留英文，是为了稳定配置接口。

| 正稿符号 | YAML/JSON 字段 | 含义与单位 |
|---|---|---|
| \(P_{\mathrm{grid}}\) | `P_grid_mw` | 接入点可持续交付的电网净有功，MW |
| \(S_{\mathrm{grid}}\)、\(\cos\varphi\) | `P_grid_mva`、`power_factor` | 视在功率及功率因数；用于换算 \(P_{\mathrm{grid}}\) |
| \(k(x)\) | `k_factor` | 设计满载设施功率 / 同一工况 IT 功率 |
| \(N_j\)、\(p_j^{\mathrm{net}}\) | `units`、`unit_net_mw` | 可同时运行机组台数、单机持续净功率，MW |
| \(A_{\mathrm{wind}}\)、\(\rho_{\mathrm{wind}}\) | `area_km2`、`density_mw_per_km2` | 风电合格面积 km²、装机密度 MW/km² |
| \(X_{\mathrm{wind}}\)、\(\alpha_{\mathrm{wind}}\) | `installed_mw`、`alpha` | 风电装机 MW、考察期最低净出力/装机 |
| \(Q\)、\(H\)、\(\eta_{\mathrm{hydro}}\)、\(X_{\mathrm{hydro}}\) | `flow_m3_per_s`、`net_head_m`、`efficiency`、`installed_mw` | 水电流量 m³/s、净落差 m、综合效率、装机 MW |
| \(A_{\mathrm{PV}}\)、\(\rho_{\mathrm{PV}}\) | `area_km2`、`density_mw_per_km2` | 光伏合格面积 km²、装机密度 MW/km² |
| \(r_t\) | `net_output_mw` | 同期逐时段交流侧净功率，MW |
| \(C_{\max}\)、\(D_{\max}\) | `C_max_mw`、`D_max_mw` | 电池最大充、放电功率，MW |
| \(E_{\mathrm{usable}}\) | `E_usable_mwh` | 扣除应急预留后的可用电量，MWh |
| \(\eta_c\)、\(\eta_d\) | `charge_efficiency`、`discharge_efficiency` | 充电、放电效率 |
| \(Q_{\mathrm{source}}\)、\(Q_{\mathrm{stress}}\)、\(Q_{\mathrm{policy}}\) | `source_m3_h`、`stress_m3_h`、`policy_m3_h` | 三项独立水量上限，m³/h |
| \(Q_{\mathrm{river}}\)、\(Q_{\mathrm{eco}}\)、\(Q_{\mathrm{other}}\) | `river_m3_h`、`eco_m3_h`、`other_m3_h` | 河段流量、生态保留、既有取水，m³/h |
| \(S_{\max}\) | `stress_fraction` | 本地水压力情景比例 |
| \(WUE\) | `wue_l_per_kwh_it` | 现场取水或耗水强度，L/kWh IT |
| \(A_{\mathrm{eff}}\) | `effective_ha` | 场址筛选后的总有效用地，ha |
| \(A_0^{\mathrm{IT}}\)、\(a_{\mathrm{site}}\) | `fixed_it_ha`、`ha_per_mw_it` | IT 侧固定用地 ha、园区边际用地强度 ha/MW IT |
| \(P_{\max}\) | `P_max_mw_it` | 场址最大联合额定 IT 容量，MW IT |

YAML 字段名是程序接口，正稿符号用于论文和结果解释；两者在下表中逐项对应。方案内部的 \(P_{\mathrm{self}}(x)\)、\(P_{\mathrm{total}}(x)\)、\(P_E(x)\)、\(P_W(x)\) 和 \(P_L(x)\) 是计算结果，不是额外的 YAML 输入。

### 顶层字段

| 字段 | 正稿符号 | 是否必填 | 单位或取值 | 说明 |
|---|---|---|---|---|
| `model` | — | 必填 | 字符串 `q1` | 选择 Q1 联合容量模型。 |
| `site` | — | 必填 | 字符串 | 场址标识。 |
| `assessment_year` | \(y\) | 必填 | 整数年份 | 可行方案集合为 \(\mathcal X_y\)，只有 \(online\_year\le y\) 的方案进入比较。 |
| `period_note` | — | 必填 | 字符串 | 设计期和结果适用范围。 |
| `service_level` | — | 必填 | 字符串 | 服务水平，例如“正常运营，持续满载”。 |
| `P_grid_mw` | \(P_{\mathrm{grid}}\) | 与 MVA 二选一 | MW | 接入点可持续交付的净有功。 |
| `P_grid_mva`、`power_factor` | \(S_{\mathrm{grid}},\cos\varphi\) | 与 MW 二选一 | MVA、无量纲 | 按 \(P_{\mathrm{grid}}=S_{\mathrm{grid}}\cos\varphi\) 换算，结果标为初筛上界。 |
| `k_factor` | \(k(x)\) | 必填 | 无量纲，\(\ge 1\) | 设计满载设施总功率除以同一工况 IT 功率。方案内可覆盖。 |
| `water` | \(Q_{\max},WUE\) | 必填 | 对象 | 水量上限和同口径 WUE。 |
| `land` | \(A_{\mathrm{eff}},A_0^{\mathrm{IT}},a_{\mathrm{site}}\) | 必填 | 对象 | 有效用地和园区 IT 侧边际用地关系。 |
| `scenarios` | \(x\in\mathcal X\) | 必填 | 非空列表 | 至少一套供电与冷却配置，每项必须有 `name` 和 `type`。 |

`P_grid_mva` 和 `power_factor` 是电力子模型的初筛输入。所有数值按园区进线处计量。

### `water` 字段

`water.basis` 必须是 `consumption`（耗水）或 `withdrawal`（取水）。水量上限和 WUE 必须使用同一口径。

| 字段 | 正稿符号 | 是否必填 | 单位 | 说明 |
|---|---|---|---|---|
| `basis` | — | 必填 | 枚举 | `consumption`（耗水）或 `withdrawal`（取水）。 |
| `wue_l_per_kwh_it` | \(WUE\) | 必填 | L/kWh IT | 可按方案覆盖。填 0 表示现场没有该类用水需求，JSON 的 \(P_W\) 为 `null`。 |
| `source_m3_h` | \(Q_{\mathrm{source}}\) | 至少一项水量上限 | m³/h | 水源扣除生态保留和既有取水后的新增可用上限。 |
| `stress_m3_h` | \(Q_{\mathrm{stress}}\) | 至少一项水量上限 | m³/h | 按本地水压力阈值允许的新增取水上限。 |
| `policy_m3_h` | \(Q_{\mathrm{policy}}\) | 至少一项水量上限 | m³/h | 许可、合同或政策允许的上限。 |
| `river_m3_h`、`eco_m3_h`、`other_m3_h` | \(Q_{\mathrm{river}},Q_{\mathrm{eco}},Q_{\mathrm{other}}\) | 可选 | m³/h | 仅用于按水模型的水源余量公式推算 \(Q_{\mathrm{source}}\)，三项需一起提供。 |
| `stress_fraction` | \(S_{\max}\) | 可选 | [0,1] | 仅用于按水模型的压力阈值公式推算 \(Q_{\mathrm{stress}}\)。 |

至少填写一个独立水量上限。没有资料的项会出现在 JSON 的 `omitted` 中，不能把缺失项当成无穷大。

水源简化估计为：

\[
Q_{\mathrm{source}}=\max\{0,Q_{\mathrm{river}}-Q_{\mathrm{eco}}-Q_{\mathrm{other}}\}.
\]

水压力上限为：

\[
Q_{\mathrm{stress}}=\max\{0,S_{\max}(Q_{\mathrm{river}}-Q_{\mathrm{eco}})-Q_{\mathrm{other}}\}.
\]

### `land` 字段

| 字段 | 正稿符号 | 是否必填 | 单位 | 说明 |
|---|---|---|---|---|
| `effective_ha` | \(A_{\mathrm{eff}}\) | 必填 | ha | 场址筛选后的总有效用地。 |
| `fixed_it_ha` | \(A_0^{\mathrm{IT}}\) | 可选 | ha | IT 侧固定用地，默认 0。填 0 是乐观上界。 |
| `ha_per_mw_it` | \(a_{\mathrm{site}}\) | 必填 | ha/MW IT | 园区本体、变配电和冷却设施的边际用地强度。 |

土地上限按权威稿的土地一次函数模型计算：

\[
P_L=\frac{A_{\mathrm{eff}}-A_0^{\mathrm{IT}}}{a_{\mathrm{site}}}.
\]

分子小于等于 0 时返回 0 MW IT，表示在当前设计下没有可建设的正容量。

### `scenarios` 字段

所有方案共有的字段：

| 字段 | 正稿符号 | 是否必填 | 说明 |
|---|---|---|---|
| `name` | \(x\) | 必填 | 方案名称，必须唯一。 |
| `type` | — | 必填 | `grid`、`coal`、`gas`、`wind`、`hydro`、`solar`、`combined_battery` 之一。 |
| `online_year` | — | 必填 | 方案投运年份；大于评估年份 \(y\) 时进入 `excluded`。 |
| `k_factor` | \(k(x)\) | 可选 | 覆盖该方案的设施倍率。 |
| `wue_l_per_kwh_it` | \(WUE(x)\) | 可选 | 覆盖该方案的现场 WUE。 |

各类型的专属字段：

| 类型 | 必填字段 | 正稿符号 | 可选字段 |
|---|---|---|---|
| `grid` | 无 | \(P_{\mathrm{grid}}\) | 无 |
| `coal` | `units`、`unit_net_mw` | \(N_j,p_j^{\mathrm{net}},P_j\) | `net_efficiency` |
| `gas` | `units`、`unit_net_mw` | \(N_j,p_j^{\mathrm{net}},P_j\) | `net_efficiency`、`gas_supply_adequate` |
| `wind` | `alpha` 或 `net_output_mw` 或 `power_ratios`，以及装机参数 | \(A_{\mathrm{wind}},\rho_{\mathrm{wind}},X_{\mathrm{wind}},\alpha_{\mathrm{wind}}\) | `installed_mw` 或 `area_km2 + density_mw_per_km2` |
| `hydro` | `installed_mw`、`flow_m3_per_s`、`net_head_m`、`efficiency` | \(X_{\mathrm{hydro}},Q,H,\eta_{\mathrm{hydro}}\) | 无 |
| `solar` | `area_km2`、`density_mw_per_km2`、`dt_hours`、`net_output_mw` 或 `supply_ratios` | \(A_{\mathrm{PV}},\rho_{\mathrm{PV}},X_{\mathrm{PV}},\Delta t,r_t\) | `battery` |
| `combined_battery` | `installed_mw`、`dt_hours`、`supply_series_mw`、`battery` | \(X_{\mathrm{风+光}},r_t,C_{\max},D_{\max},E_{\mathrm{usable}}\) | 无 |

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

风电和光伏的 `net_output_mw` 是考察期内逐时段的交流侧净功率，单位 MW。序列长度必须一致，不能包含 `null`、负数或缺失值。光伏还可以用 `supply_ratios` 提供逐时净功率除以装机的无量纲序列。

`P_{\mathrm{self}}(x)` 不是单独的配置字段，而是由所选方案内部的电源计算得到的净可靠增量；`P_{\mathrm{total}}(x)` 和 \(P_E(x)\) 也是计算结果，分别对应 JSON 的 `facility_mw` 和 `P_E_mw_it`。

并网风电应提供 `net_output_mw`。当前实现使用恒定可交付电网加最低风电出力的确定性口径。孤立场址可以把 `P_grid_mw` 设为 0 并填写 `alpha`。年度容量因子不能替代考察期的最低出力比例。

电池字段：

| 字段 | 正稿符号 | 单位 | 说明 |
|---|---|---|---|
| `C_max_mw` | \(C_{\max}\) | MW | 最大充电功率。 |
| `D_max_mw` | \(D_{\max}\) | MW | 最大放电功率。 |
| `E_usable_mwh` | \(E_{\mathrm{usable}}\) | MWh | 扣除应急预留后的可用电量。 |
| `charge_efficiency` | \(\eta_c\) | 无量纲，(0,1] | 充电效率，省略时按 1。 |
| `discharge_efficiency` | \(\eta_d\) | 无量纲，(0,1] | 放电效率，省略时按 1。 |

### 常见 YAML 错误

| 写法 | 结果和修改方式 |
|---|---|
| 只写 `P_grid_mva`，没有 `power_factor` | 报错。补充功率因数，或改用 `P_grid_mw`。 |
| 水量没有 `source_m3_h`、`stress_m3_h`、`policy_m3_h` 中任何一项 | 报错。至少填写一项独立上限。 |
| `k_factor: 0.9` | 报错。设计要求 \(k\ge 1\)。 |
| 电池功率写成 `C_max_mwh` 或 `D_max_mwh` | 报错。功率使用 `_mw`，能量使用 `_mwh`。 |
| 光伏没有 `net_output_mw` 或 `supply_ratios` | 报错。补充同期出力序列。 |
| 并网风电只写 `alpha` | 报错。并网场景需提供同期 `net_output_mw`。 |
| `online_year` 晚于 `assessment_year` | 不报错，方案进入 `excluded`。 |

## JSON 输出详解

### 写出 JSON

`--json` 参数是输出文件路径，不是输入配置路径：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

程序只在计算成功后写文件。父目录必须已经存在，重复运行会覆盖同名文件。

### 顶层结构

```text
{
  "site": "...",
  "assessment_year": 2028,
  "period_note": "...",
  "inputs": { ... 原始输入 ... },
  "service_level": "...",
  "grid_basis": "...",
  "water": { ... },
  "scenarios": [ ... ],
  "excluded": [ ... ],
  "P_max_mw_it": 100.0,
  "winners": ["..."]
}
```

| 字段 | 单位或类型 | 含义 |
|---|---|---|
| `site`、`assessment_year`、`period_note`、`service_level` | 字符串或整数 | 本次比较采用的场址、年份、设计期和服务水平。 |
| `inputs` | 对象 | 实际传入模型的输入，便于复现。 |
| `grid_basis` | 字符串 | 电网功率口径，例如“接入点持续净有功”或“MVA × 功率因数，初筛上界”。 |
| `water` | 对象 | 水量上限计算后的结果，不只是 YAML 原始输入。 |
| `scenarios` | 数组 | 进入当年比较的方案结果。 |
| `excluded` | 数组 | 未进入比较的方案，含 `name`、`online_year` 和 `reason`。 |
| `P_max_mw_it` | MW IT | 当年可行方案中的最大联合容量。 |
| `winners` | 字符串数组 | 达到 `P_max_mw_it` 的方案，可能有并列。 |

`water` 中各字段：

| 字段 | 正稿符号 | 单位 | 说明 |
|---|---|---|---|
| `limits_m3_h` | \(Q_{\mathrm{source}},Q_{\mathrm{stress}},Q_{\mathrm{policy}}\) | m³/h | 实际参与最小值的各项独立上限。 |
| `Q_max_m3_h` | \(Q_{\max}\) | m³/h | 各项上限的最小值。 |
| `omitted` | — | 字符串数组 | 没有提供的独立上限项。 |

### 单方案结果

每个方案同时给出三项上限和联合值：

| 字段 | 单位 | 说明 |
|---|---|---|
| `P_E_mw_it` | MW IT | 电力子模型上限，已经除以 \(k\)。 |
| `P_W_mw_it` | MW IT 或 null | 水子模型上限。WUE 为 0 时为 null。 |
| `P_L_mw_it` | MW IT | 土地子模型上限。 |
| `P_mw_it` | MW IT | \(\min(P_E,P_W,P_L)\)。 |
| `binding` | 字符串数组 | 达到最小值的约束，多个值表示并列瓶颈。 |

`breakdown` 保存电力链中间量：

| 字段 | 正稿符号 | 单位 | 说明 |
|---|---|---|---|
| `grid_mw` | \(P_{\mathrm{grid}}\) | MW | 计入的电网净有功。 |
| `self_generation_mw` | \(P_{\mathrm{self}}(x)\) | MW | 自建电源持续净增量。 |
| `facility_mw` | \(P_{\mathrm{total}}(x)\) | MW | 园区总功率，等于 \(P_{\mathrm{grid}}+P_{\mathrm{self}}\)。 |
| `k` | \(k(x)\) | 无量纲 | 该方案使用的设施倍率。 |
| `it_mw` | \(P_E(x)\) | MW IT | \(P_{\mathrm{total}}/k\)，与 `P_E_mw_it` 对应。 |

`land` 保存土地链中间量：

| 字段 | 单位 | 说明 |
|---|---|---|
| `site_ha` | ha | 参与土地容量计算的园区有效用地 \(A_{\mathrm{eff}}\)。 |
| `fixed_it_ha` | ha | IT 侧固定用地。 |
| `optimistic_zero_fixed` | 布尔 | 固定用地是否按 0 处理。 |
| `P_L_mw_it` | MW IT | 该方案的土地上限。 |

### 光储调度

有电池的 `solar` 方案，`method` 中会有与输入序列等长的逐时调度：

| 字段 | 单位 | 说明 |
|---|---|---|
| `L_mw` | MW | 光储模型求出的最大恒定附加负荷。 |
| `charge_mw` | MW | 每个时段的充电功率。 |
| `discharge_mw` | MW | 每个时段的放电功率。 |
| `energy_start_mwh` | MWh | 每个时段开始时的可用电量。 |
| `curtailment_mw` | MW | 每个时段的弃电功率。 |
| `direction` | 0/1 数组 | 1 表示该时段允许充电，0 表示允许放电。 |
| `battery` | 对象 | 求解使用的充放电功率、电量和效率参数。 |
| `status` | 字符串 | HiGHS 返回状态。 |

例如输入 `[20, 0]` MW、电池 10 MW/10 MWh 时，`charge_mw` 为 `[10, 0]`，`discharge_mw` 为 `[0, 10]`，`energy_start_mwh` 为 `[0, 10]`。这组数组可直接复核功率平衡、周期电量和充放互斥。

### 排除项

`excluded` 只记录没有进入当年比较的方案。常见原因是尚未投运。若所有方案都被排除，程序会报错。

## 模型与代码边界

Q1 入口接受 `grid`、`coal`、`gas`、`wind`、`hydro`、`solar` 和
`combined_battery` 七类方案。`combined_battery` 表示风、光共用电池，先将风光同期
净功率 \(r_t\) 相加，再按附录 A 求解一次。旧版仅电力分项接口不属于 Q1 配置入口。

核心公式：

\[
P_{\mathrm{total}}=P_{\mathrm{grid}}+P_{\mathrm{self}},
\qquad
P_E=\frac{P_{\mathrm{total}}}{k}.
\]

\[
P_{\max}=\max_{x\in\mathcal X_y}\min\{P_E(x),P_W(x),P_L(x)\}.
\]

光储方案使用 SciPy `linprog` / HiGHS 求解附录 A 的逐时功率和电量约束。第一次求最大恒定附加负荷，第二次固定该负荷并导出单向充放电调度。调度数组会校核功率平衡、周期首尾电量和充放互斥。

代码位置：

- `code/run.py`：命令和 Python 函数入口。
- `code/immc_power_capacity/app.py`：命令行、YAML/JSON 读写和输入向导。
- `code/immc_power_capacity/core.py`：电源公式、水/土地子模型、Q1 集成和光储 LP。
- `code/immc_power_capacity/__init__.py`：包级函数导出。
- `code/immc_power_capacity/__main__.py`：`python -m immc_power_capacity` 入口。

运行时结构只有：

```text
code/run.py
code/immc_power_capacity/app.py
code/immc_power_capacity/core.py
code/immc_power_capacity/__init__.py
code/immc_power_capacity/__main__.py
```

## 测试

```powershell
python -m pytest -q code/tests
```

测试覆盖最小联合配置、90/100 MW 纯电网算例、水量和土地瓶颈、并网风电、风、光共用电池、光储调度和输入错误。

## 数据分类

- `examples/q1_minimal.yaml` 和 `examples/q1_site.yaml`：合成演示数据。
- `research/A题模型/参数资料/参数汇总表.md`：候选资料，含行业均值和文献算例，使用前需按真实场址核对。
- 程序输出：基于当前配置和考察期的计算结果，不是对所有年份或天气过程的保证。

电力、水、土地三个上限必须来自同一配置、同一设计期和同一服务水平。比较不同场址时，应保持这些口径一致。
