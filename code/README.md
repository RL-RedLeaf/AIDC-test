# IMMC 2027 A 题第一问：给定场址的电、水、土地容量

本目录实现 [权威稿 IMMC2027-Q1](../正稿/Q1-v2/IMMC2027-Q1/IMMC2027-Q1.md) 的电力式（1）–（6）、水模型和土地模型。程序先排除评估年份尚未投运的方案，再对每套方案计算电力、水和土地三个上限，取三者最小值，最后在当年候选集中取最大值。

评估年份、候选集和最终最大容量的补充公式见
[补充_评估年份与候选方案集合.md](../正稿/Q1-v2/IMMC2027-Q1/补充_评估年份与候选方案集合.md)。

## 快速开始

在仓库根目录运行最小示例：

```powershell
python code/run.py code/examples/q1_minimal.yaml
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

YAML 保存场址和方案输入。省略 `--json` 时，结果自动写入
`正稿/Q1-v2/output/<配置文件名>_result.json`：

```powershell
python code/run.py code/examples/q1_site.yaml
```

不指定 `--json` 时，CLI 默认将结果写入
`正稿/Q1-v2/output/<配置文件名>_result.json`。完整 CSV 示例见
[q1_site.csv](examples/q1_site.csv)：

```powershell
python code/run.py code/examples/q1_site.csv
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
```

`online_year` 可以省略；省略时按 `assessment_year` 视为已投运。字段单位和填写规则见下文“YAML 输入详解”。每套方案必须使用同一场址、同一设计期和同一服务水平，否则 \(P_{\max}\) 的取最小没有意义。

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
3. 水量口径、WUE 和至少一项水量上限（\(Q_{\mathrm{DC,水源}},Q_{\mathrm{DC,压力上限}},Q_{\mathrm{DC,政策上限}}\)），至少一项不能为空。
4. 有效用地 \(A_{\mathrm{eff}}\)、IT 侧固定用地 \(A_0^{\mathrm{IT}}\)、园区内自建发电站用地 \(A_e\) 和边际用地强度 \(a_{\mathrm{site}}\)。
5. 方案类型和设备参数。风电、光伏的逐时序列 \(r_t\) 用逗号或空格分隔，例如 `20, 0`。
6. 是否继续添加方案。可以一次输入多套方案。
7. JSON 输出路径。留空只在终端输出结果；填写路径则同时写出 JSON。

数值格式错误会重新询问。模型校验失败时会在终端给出中文错误信息。

### 3. Python 函数入口

`run.py` 现在是可导入模块。`calculate()` 和 `run()` 都接受配置字典或 YAML 路径。下面的示例省略 `online_year`，程序按 `assessment_year` 处理：

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
    "scenarios": [{"type": "grid", "name": "纯电网"}],
})
print(report["P_max_mw_it"])  # 100.0
```

第二个参数可以指定 JSON 路径，父目录不存在时会自动创建：

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
        "scenarios": [{"type": "grid", "name": "纯电网"}],
    },
    "result.json",
)
```

## CSV 输入

CSV 适合把每套候选方案写成一行，尤其是同时比较多个电源、冷却和电池配置时。示例：

- 固定 \(A_e\)：[q1_site.csv](examples/q1_site.csv)
- \(A_e\) 候选优化：[q1_site_ae_options.csv](examples/q1_site_ae_options.csv)

```text
site,assessment_year,period_note,service_level,P_grid_mw,k_factor,...
演示场址,2028,枯水期设计工况,正常运营且持续满载,108,1.2,...
```

CSV 规则：

- 第 1 行必须是表头，列名固定。
- 公共场址、水量、土地和电网字段可以在任意一行填写，但同一列只能有一个非空值；不同行写入不同公共值会报错。
- `scenario_name`、`scenario_type` 是每行必填字段；`online_year` 可留空，留空时按 `assessment_year` 视作已投运。
- `scenario_k_factor`、`scenario_wue_l_per_kwh_it`、`scenario_generation_water_l_per_kwh`、`scenario_generation_land_ha`、`scenario_generation_land_options_ha` 是方案级覆盖值。
- 电池字段使用 `battery_C_max_mw`、`battery_D_max_mw`、`battery_E_usable_mwh`、`battery_charge_efficiency`、`battery_discharge_efficiency`。
- 火电单机用地用 `unit_land_ha`，风光资源面积用 `area_km2`；需要显式覆盖发电设施用地时用 `generation_land_required_ha`。
- 发电设施是否位于园区边界内用 `generation_land_in_site` 标记，默认 `true`。
- 时间序列用分号、竖线或逗号分隔，例如 `net_output_mw = 20;0`。
- 直接覆盖结果的可选字段为 `direct_P_E_mw_it`、`direct_P_W_mw_it`、`direct_P_L_mw_it`；对应结果会记录 `value_source: direct`。

CSV 中的字段名与 YAML 字段一一对应，字段单位和必填规则见下文“输入/输出总览”。

## 输入/输出总览

### 输入分类

| 类别 | 字段 | 正稿符号 | 具体含义 |
|---|---|---|---|
| 场址与评估条件 | `site`、`assessment_year`、`period_note`、`service_level` | \(y\) 对应 `assessment_year`；其余无符号 | 场址标识、评估年份、设计期和服务水平；定义比较边界 |
| 电网接入条件 | `P_grid_mw` 或 `P_grid_mva + power_factor` | \(P_{\mathrm{grid}}\) 或 \(S_{\mathrm{grid}},\cos\varphi\) | 接入点可持续交付容量；MVA 口径是初筛换算 |
| 地理条件：水域 | `source_m3_h`、`river_m3_h`、`eco_m3_h`、`other_m3_h`、`policy_m3_h` | \(Q_{\mathrm{DC,水源}},Q_{\mathrm{河流}},Q_{\mathrm{生态}},Q_{\mathrm{其他取水}},Q_{\mathrm{DC,政策上限}}\) | 水源余量、河段流量、生态保留、既有取水、政策上限 |
| 地理条件：土地 | `effective_ha` | \(A_{\mathrm{eff}}\) | GIS、规划和生态筛选后的连续有效用地 |
| 气象与资源 | `net_output_mw`、`supply_series_mw`、`flow_m3_per_s`、`net_head_m`、`area_km2` | \(r_t\)、\(Q\)、\(H\)、\(A_{\mathrm{风}}\)、\(A_{\mathrm{光}}\) | 风光逐时净功率、水电可用流量和落差、风光合格面积 |
| 经验或情景参数 | `stress_fraction`、`wue_l_per_kwh_it`、`generation_water_l_per_kwh`、`alpha`、`k_factor`、`net_efficiency` | \(S_{\max}\)、\(WUE\)、\(c_i\)、\(\alpha_{\mathrm{风}}\)、\(k(x)\)、\(\eta_j^{\mathrm{net}}\) | 取水压力阈值、WUE、发电耗水系数、风电保障比例、设施倍率、机组净效率 |
| 厂房/园区设施 | `fixed_it_ha`、`generation_land_ha`、`ha_per_mw_it`、`density_mw_per_km2` | \(A_0^{\mathrm{IT}}\)、\(A_e\)、\(a_{\mathrm{site}}\)、\(\rho_{\mathrm{风}},\rho_{\mathrm{光}}\) | IT 固定用地、园区内发电站用地、边际用地强度、风光装机密度 |
| 机组/电源设备 | `units`、`unit_net_mw`、`installed_mw` | \(N_j\)、\(p_j^{\mathrm{net}}\)、\(X_{\mathrm{风}},X_{\mathrm{水}},X_{\mathrm{光}}\) | 火电台数和单机净功率、风电/水电/合计装机 |
| 储能设备 | `C_max_mw`、`D_max_mw`、`E_usable_mwh`、`charge_efficiency`、`discharge_efficiency` | \(C_{\max}\)、\(D_{\max}\)、\(E_{\mathrm{可用}}\)、\(\eta_c\)、\(\eta_d\) | 电池最大充放电功率、可用电量、充放电效率 |
| 方案控制 | `name`、`type`、`online_year`（可选） | \(x\) 对应 `name`；\(y_x\) 对应 `online_year` | 候选配置名称、电源类型、投运年份；省略 `online_year` 时按 \(y\) 处理 |

`site` 只是场址标识，真实地理信息必须通过上面的有效用地、河段流量、生态保留、风光面积和逐时序列等数值传入。程序不直接读取 GIS 地图、气象文件或流域模型；这些预处理应在外部完成。

### 必填与缺省

| 字段 | 正稿符号 | 必填性 | 缺省值或规则 |
|---|---|---|---|
| `model` | — | 必填 | 必须为 `q1` 才进入联合模型 |
| `site`、`assessment_year`、`period_note`、`service_level` | \(y\) 对应 `assessment_year` | 必填 | 无缺省；三个资源上限必须使用同一场址、设计期和服务水平 |
| `P_grid_mw`、`P_grid_mva` | \(P_{\mathrm{grid}}\)、\(S_{\mathrm{grid}}\) | 二选一 | 必须提供一个；`P_grid_mva` 还必须提供 `power_factor` \(\cos\varphi\) |
| `k_factor` | \(k(x)\) | 必填 | 无缺省；方案内可覆盖，要求 \(k(x)\ge 1\) |
| `water.basis` | — | 必填 | 只能为 `consumption` 或 `withdrawal` |
| `wue_l_per_kwh_it` | \(WUE\) | 直接口径时必填 | 可按方案覆盖；填 0 表示没有该类现场用水需求 |
| `wue_summer_l_per_kwh_it`、`wue_winter_l_per_kwh_it`、`summer_hours`、`winter_hours` | \(WUE_{\mathrm{夏}},WUE_{\mathrm{冬}},t_{\mathrm{夏}},t_{\mathrm{冬}}\) | 季节口径时必填 | 四个字段必须同时提供，按运行小时加权 |
| `source_m3_h`、`stress_m3_h`、`policy_m3_h` | \(Q_{\mathrm{DC,水源}},Q_{\mathrm{DC,压力上限}},Q_{\mathrm{DC,政策上限}}\) | 至少一项 | 作为独立水量上限；未提供项列入 `omitted`，不能当作无穷大 |
| `river_m3_h`、`eco_m3_h`、`other_m3_h` | \(Q_{\mathrm{河流}},Q_{\mathrm{生态}},Q_{\mathrm{其他取水}}\) | 可选但成组 | 用于水源余量公式；只有河流和生态流量时只能得到未核实水文余量，程序会报错 |
| `stress_fraction` | \(S_{\max}\) | 可选 | 不提供则不计算水压力上限 |
| `generation_water_l_per_kwh` | \(c_{\mathrm{煤}},c_{\mathrm{气}},c_{\mathrm{风}},c_{\mathrm{光}}\) | 可选 | 缺省视为空映射，即 \(Q_{\mathrm{发电耗水}}=0\)；实际使用时应显式填写 |
| `effective_ha` | \(A_{\mathrm{eff}}\) | 必填 | 无缺省；用于 \(P_L=(A_{\mathrm{eff}}-A_0-A_e)/a_{\mathrm{site}}\) |
| `fixed_it_ha` | \(A_0^{\mathrm{IT}}\) | 可选 | 默认 0，表示忽略 IT 侧固定用地，属于乐观上界 |
| `generation_land_ha` | \(A_e\) | 可选 | 园区内自建发电站及专属配套用地，默认 0；仅使用电网时填 0 |
| `generation_land_options_ha` | \(A_e^{(k)}\) | 可选 | 发电站用地候选列表；与固定 `generation_land_ha` 二选一，程序选择联合容量最大的候选 |
| `generation_land_in_site` | — | 可选 | 发电设施是否位于园区边界内，默认 `true`；为 `false` 时不计入园区的 \(A_e\)，也不受园区发电用地预算限制 |
| `unit_land_ha` | \(a_{\mathrm{unit},j}\) | 火电可选 | 单台火电机组的厂区用地，ha/台；与 `units` 一起用于校核 \(A_e\) |
| `generation_land_required_ha` | \(A_{\mathrm{gen}}\) | 可选 | 方案实际需要的发电设施用地；可用于风电、光伏、电池或显式覆盖 |
| `ha_per_mw_it` | \(a_{\mathrm{site}}\) | 必填 | 单位 ha/MW IT，必须为正数 |
| `scenarios` | \(x\in\mathcal X\) | 必填 | 至少一项 |
| `name`、`type` | \(x\) | 每方案必填 | `type` 取 `grid`、`coal`、`gas`、`wind`、`hydro`、`solar` 或 `combined_battery` |
| `online_year` | \(y_x\) | 可选 | 方案投运年份；缺省取 `assessment_year` \(y\)，即视为已投运。只有 \(y_x\le y\) 的方案进入比较 |
| 方案内 `k_factor`、`wue_l_per_kwh_it`、`generation_water_l_per_kwh` | \(k(x),WUE(x),c_i(x)\) | 可选 | 分别覆盖该方案的设施倍率、WUE、发电耗水系数 |
| `units`、`unit_net_mw` | \(N_j,p_j^{\mathrm{net}}\) | 火电必填 | `units` 为正整数，`unit_net_mw` 为正数 |
| `net_efficiency` | \(\eta_j^{\mathrm{net}}\) | 可选 | 只用于报告燃料热功率，不改变电力容量 |
| `gas_supply_adequate` | — | 可选 | `false` 拒绝燃气容量上界；未填写按设计供气充足处理，但应在论文中声明 |
| `installed_mw` 或 `area_km2 + density_mw_per_km2` | \(X_i\)、\(A_i,\rho_i\) | 风光设备必填 | 至少提供装机，或面积与装机密度 |
| `alpha`、`power_ratios`、`net_output_mw` | \(\alpha_{\mathrm{风}}\)、\(r_t/X_{\mathrm{风}}\)、\(r_t\) | 风电三选一 | 并网风电必须使用同期 `net_output_mw` 或 `power_ratios` |
| `flow_m3_per_s`、`net_head_m`、`efficiency` | \(Q,H,\eta_{\mathrm{水}}\) | 水电必填 | 采用同一约束期的流量、落差和综合效率 |
| `dt_hours` | \(\Delta t\) | 光储/共用电池必填 | 附录 A 逐时校核的时段长度，单位 h |
| `supply_ratios` 或 `net_output_mw` | \(r_t/X_{\mathrm{光}}\)、\(r_t\) | 光伏二选一 | `net_output_mw` 是逐时净功率；`supply_ratios` 是逐时净功率/装机 |
| `battery` | \(C_{\max},D_{\max},E_{\mathrm{可用}}\) | 光伏可选、共用电池必填 | 光伏省略按无电池处理；共用电池必须提供 |
| 电池 `charge_efficiency`、`discharge_efficiency` | \(\eta_c,\eta_d\) | 电池内可选 | 默认 1.0 |
| `direct_P_E_mw_it`、`direct_P_W_mw_it`、`direct_P_L_mw_it` | \(P_E,P_W,P_L\) | 可选 | 已拿到最终上限时直接覆盖对应推导值，并在结果中标记 `value_source: direct` |
| `C_PCC_mw`、`generation_share`、`period_budget`、`sensitivity` | — | 不接受 | 会明确报错；不属于当前 Q1-v2 口径 |

### 输出分类

| 输出 | 正稿符号 | 单位 | 含义 |
|---|---|---|---|
| `P_E_mw_it` | \(P_E(x)\) | MW IT | 电力子模型上限 \(P_E=P_{\mathrm{total}}/k\) |
| `P_W_mw_it` | \(P_W(x)\) | MW IT 或 null | 水子模型上限 `P_W=Qnet/WUE`；WUE 为 0 时为 null |
| `P_L_mw_it` | \(P_{\mathrm{land}}(x)\) | MW IT | 土地子模型上限 \(P_L=(A_{\mathrm{eff}}-A_0-A_e)/a_{\mathrm{site}}\) |
| `P_mw_it` | \(P(x)\) | MW IT | \(P=\min(P_E,P_W,P_L)\) |
| `binding` | — | 字符串数组 | 达到该方案最小值的约束；可并列 |
| `P_max_mw_it` | \(P_{\max}\) | MW IT | 所有当年可行方案中的最大 \(P\) |
| `winners` | — | 字符串数组 | 达到 `P_max_mw_it` 的方案，可并列 |
| `excluded` | — | 数组 | 因未投运而未进入比较的方案 |
| `breakdown.grid_mw` | \(P_{\mathrm{grid}}\) | MW | 电网净有功 |
| `breakdown.self_generation_mw` | \(P_{\mathrm{self}}(x)\) | MW | 自建电源可靠净增量 |
| `breakdown.facility_mw` | \(P_{\mathrm{total}}(x)\) | MW | \(P_{\mathrm{total}}=P_{\mathrm{grid}}+P_{\mathrm{self}}\) |
| `breakdown.k` | \(k(x)\) | 无量纲 | 该方案使用的设施倍率 |
| `breakdown.it_mw` | \(P_E(x)\) | MW IT | 与 `P_E_mw_it` 对应的电力结果 |
| `generation_water_m3_h` | \(Q_{\mathrm{发电耗水}}\) | m³/h | 自发电耗水流量 |
| `Q_net_m3_h` | \(Q_{\mathrm{net}}\) | m³/h | 扣除发电耗水后的净可用流量 |
| `water.Q_max_m3_h` | \(Q_{\mathrm{DC,max}}\) | m³/h | 三项水量上限的最小值 |
| `water.limits_m3_h` | \(Q_{\mathrm{DC,水源}},Q_{\mathrm{DC,压力上限}},Q_{\mathrm{DC,政策上限}}\) | m³/h | 实际参与最小值的各项独立上限 |
| `water.omitted` | — | 字符串数组 | 未提供的水量上限项 |
| `land.site_ha` | \(A_{\mathrm{eff}}\) | ha | 参与土地计算的有效用地 |
| `land.fixed_it_ha` | \(A_0^{\mathrm{IT}}\) | ha | IT 侧固定用地 |
| `land.generation_land_ha` | \(A_e\) | ha | 园区内自建发电站及专属配套用地 |
| `land.P_L_mw_it` | \(P_{\mathrm{land}}(x)\) | MW IT | 土地上限 |
| `generation_land_source` | — | 字符串 | \(A_e\) 来自 `fixed`、`options`、`external` 或直接覆盖 |
| `generation_land_candidates` | — | 数组 | \(A_e\) 候选值对应的 \(P_L\)、\(P\) 和 binding |
| `generation_land_required_ha` | \(A_{\mathrm{gen}}\) | ha | 方案实际需要的发电设施用地 |
| `generation_land_capacity_capped` | — | 布尔 | 设备容量是否因 \(A_e\) 不足而被缩减 |
| `value_source` | — | 对象 | 分别记录 \(P_E\)、\(P_W\)、\(P_L\) 是 `derived`、`direct` 还是候选优化结果 |
| `method.charge_mw` 等 | \(L,c_t,d_t,e_t\) | MW/MWh | 光储逐时负荷、充电、放电、荷电量和弃电调度 |

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
| \(Q_{\mathrm{DC,水源}}\)、\(Q_{\mathrm{DC,压力上限}}\)、\(Q_{\mathrm{DC,政策上限}}\) | `source_m3_h`、`stress_m3_h`、`policy_m3_h` | 三项独立水量上限，m³/h |
| \(Q_{\mathrm{河流}}\)、\(Q_{\mathrm{生态}}\)、\(Q_{\mathrm{其他取水}}\) | `river_m3_h`、`eco_m3_h`、`other_m3_h` | 河段流量、生态保留、既有取水，m³/h |
| \(S_{\max}\) | `stress_fraction` | 本地水压力情景比例 |
| \(WUE\) | `wue_l_per_kwh_it` | 现场取水或耗水强度，L/kWh IT |
| \(A_{\mathrm{eff}}\) | `effective_ha` | 场址筛选后的总有效用地，ha |
| \(A_0^{\mathrm{IT}}\)、\(A_e\)、\(a_{\mathrm{site}}\) | `fixed_it_ha`、`generation_land_ha`、`ha_per_mw_it` | IT 侧固定用地 ha、园区内自发电站用地 ha、边际用地强度 ha/MW IT |
| \(a_{\mathrm{unit},j}\)、\(A_{\mathrm{gen}}\) | `unit_land_ha`、`generation_land_required_ha` | 火电单机用地 ha/台、方案实际发电设施用地 ha |
| \(P_{\max}\) | `P_max_mw_it` | 场址最大联合额定 IT 容量，MW IT |

YAML 字段名是程序接口，正稿符号用于论文和结果解释；两者在下表中逐项对应。方案内部的 \(P_{\mathrm{self}}(x)\)、\(P_{\mathrm{total}}(x)\)、\(P_E(x)\)、\(P_W(x)\) 和 \(P_L(x)\) 是计算结果，不是额外的 YAML 输入。

### 顶层字段

| 字段 | 正稿符号 | 是否必填 | 单位或取值 | 说明 |
|---|---|---|---|---|
| `model` | — | 必填 | 字符串 `q1` | 选择 Q1 联合容量模型。 |
| `site` | — | 必填 | 字符串 | 场址标识。 |
| `assessment_year` | \(y\) | 必填 | 整数年份 | 可行方案集合为 \(\mathcal X_y\)；`online_year` 省略时按该年处理。 |
| `period_note` | — | 必填 | 字符串 | 设计期和结果适用范围。 |
| `service_level` | — | 必填 | 字符串 | 服务水平，例如“正常运营，持续满载”。 |
| `P_grid_mw` | \(P_{\mathrm{grid}}\) | 与 MVA 二选一 | MW | 接入点可持续交付的净有功。 |
| `P_grid_mva`、`power_factor` | \(S_{\mathrm{grid}},\cos\varphi\) | 与 MW 二选一 | MVA、无量纲 | 按 \(P_{\mathrm{grid}}=S_{\mathrm{grid}}\cos\varphi\) 换算，结果标为初筛上界。 |
| `k_factor` | \(k(x)\) | 必填 | 无量纲，\(\ge 1\) | 设计满载设施总功率除以同一工况 IT 功率。方案内可覆盖。 |
| `water` | \(Q_{\mathrm{DC,max}},WUE,Q_{\mathrm{发电耗水}}\) | 必填 | 对象 | 水量上限、同口径 WUE 和自发电耗水系数。 |
| `land` | \(A_{\mathrm{eff}},A_0^{\mathrm{IT}},A_e,a_{\mathrm{site}}\) | 必填 | 对象 | 有效用地、固定设施用地、园区内发电站用地和 IT 侧边际用地关系。 |
| `scenarios` | \(x\in\mathcal X\) | 必填 | 非空列表 | 至少一套供电与冷却配置，每项必须有 `name` 和 `type`。 |

`P_grid_mva` 和 `power_factor` 是电力子模型的初筛输入。所有数值按园区进线处计量。

`assessment_year`（\(y\)）和 `online_year`（\(y_x\)）是程序接口字段；正稿式（1）–（6）
不含这两个符号，它们只用于定义候选集 \(\mathcal X_y=\{x:y_x\le y\}\)。
`online_year` 可省略；如果所有方案都已经建成，只填 `assessment_year` 即可。

### `water` 字段

`water.basis` 必须是 `consumption`（耗水）或 `withdrawal`（取水）。水量上限和 WUE 必须使用同一口径。

| 字段 | 正稿符号 | 是否必填 | 单位 | 说明 |
|---|---|---|---|---|
| `basis` | — | 必填 | 枚举 | `consumption`（耗水）或 `withdrawal`（取水）。 |
| `wue_l_per_kwh_it` | \(WUE\) | 直接 WUE 时必填 | L/kWh IT | 可按方案覆盖。填 0 表示现场没有该类用水需求，JSON 的 \(P_W\) 为 `null`。 |
| `source_m3_h` | \(Q_{\mathrm{DC,水源}}\) | 至少一项水量上限 | m³/h | 水源扣除生态保留和既有取水后的新增可用上限。 |
| `stress_m3_h` | \(Q_{\mathrm{DC,压力上限}}\) | 至少一项水量上限 | m³/h | 按本地水压力阈值允许的新增取水上限。 |
| `policy_m3_h` | \(Q_{\mathrm{DC,政策上限}}\) | 至少一项水量上限 | m³/h | 许可、合同或政策允许的上限。 |
| `river_m3_h`、`eco_m3_h`、`other_m3_h` | \(Q_{\mathrm{河流}},Q_{\mathrm{生态}},Q_{\mathrm{其他取水}}\) | 可选 | m³/h | 仅用于按水模型的水源余量公式推算 \(Q_{\mathrm{DC,水源}}\)，三项需一起提供。 |
| `stress_fraction` | \(S_{\max}\) | 可选 | [0,1] | 仅用于按水模型的压力阈值公式推算 \(Q_{\mathrm{DC,压力上限}}\)。 |
| `wue_summer_l_per_kwh_it`、`wue_winter_l_per_kwh_it` | \(WUE_{\mathrm{夏}},WUE_{\mathrm{冬}}\) | 季节 WUE 时必填 | L/kWh IT | 与夏季、冬季运行小时数一起按小时加权。 |
| `summer_hours`、`winter_hours` | \(t_{\mathrm{夏}},t_{\mathrm{冬}}\) | 季节 WUE 时必填 | h | 两个代表时段的运行时长。 |
| `generation_water_l_per_kwh` | \(c_{\mathrm{煤}},c_{\mathrm{气}},c_{\mathrm{风}},c_{\mathrm{光}}\) | 可选 | L/kWh | 对象，可填 `coal`、`gas`、`wind`、`solar` 的运行期耗水系数。 |

至少填写一个独立水量上限。没有资料的项会出现在 JSON 的 `omitted` 中，不能把缺失项当成无穷大。

`source_m3_h` 也可以直接填入流域部门发布的剩余可分配水量，或供水单位对项目确认的新增可交付量；此时不要再同时用河流、生态和其他取水字段重复扣减。

如果只有 `river_m3_h` 和 `eco_m3_h`，程序会报错：这只能得到尚未核实其他取水的
`Q_水文余量`，不能当作 \(Q_{\mathrm{DC,水源}}\)。请补充 `other_m3_h`，或改用
`source_m3_h` 填入供水单位/WAM/WRAP 的剩余水量。

水源简化估计为：

\[
Q_{\mathrm{DC,水源}}=\max\{0,Q_{\mathrm{河流}}-Q_{\mathrm{生态}}-Q_{\mathrm{其他取水}}\}.
\]

水压力上限为：

\[
Q_{\mathrm{DC,压力上限}}=\max\{0,S_{\max}(Q_{\mathrm{河流}}-Q_{\mathrm{生态}})-Q_{\mathrm{其他取水}}\}.
\]

若提供夏、冬两季的 WUE，程序按权威稿的时长加权式计算：

\[
WUE_{\mathrm{全年}}
=\frac{t_{\mathrm{夏}}WUE_{\mathrm{夏}}+t_{\mathrm{冬}}WUE_{\mathrm{冬}}}
{t_{\mathrm{夏}}+t_{\mathrm{冬}}}.
\]

自发电耗水流量为：

\[
Q_{\mathrm{发电耗水}}=P_{\mathrm{煤}}c_{\mathrm{煤}}
+P_{\mathrm{气}}c_{\mathrm{气}}
+P_{\mathrm{风}}c_{\mathrm{风}}
+P_{\mathrm{光}}c_{\mathrm{光}}.
\]

这里功率用 MW、系数用 L/kWh 时，计算结果的数值直接对应 m³/h。程序在当前方案内先计算
\(Q_{\mathrm{DC,max}}\)，再令

\[
Q_{\mathrm{net}}=\max\{0,Q_{\mathrm{DC,max}}-Q_{\mathrm{发电耗水}}\},
\qquad
P_W=\frac{Q_{\mathrm{net}}}{WUE}.
\]

当前实现用方案设计工况下的可靠自发电功率 `self_generation_mw` 作为 \(P_i\)。如果后续有完整的逐时发电曲线，应将 \(P_i\) 的时间序列代入同一耗水公式，而不是只用单点可靠容量。

### `land` 字段

| 字段 | 正稿符号 | 是否必填 | 单位 | 说明 |
|---|---|---|---|---|
| `effective_ha` | \(A_{\mathrm{eff}}\) | 必填 | ha | 场址筛选后的总有效用地。 |
| `fixed_it_ha` | \(A_0^{\mathrm{IT}}\) | 可选 | ha | IT 侧固定用地，默认 0。填 0 是乐观上界。 |
| `generation_land_ha` | \(A_e\) | 可选 | ha | 园区内自建发电站及专属配套用地，默认 0；仅使用电网时为 0。 |
| `generation_land_options_ha` | \(A_e^{(k)}\) | 可选 | ha | 发电站用地候选列表，与固定 `generation_land_ha` 二选一。 |
| `generation_land_in_site` | — | 可选 | 布尔 | 发电设施是否在园区边界内，默认 `true`；外部设施不扣园区土地。 |
| `unit_land_ha` | \(a_{\mathrm{unit},j}\) | 火电可选 | ha/台 | 单台火电机组厂区用地，用于按 \(A_e\) 限制机组台数。 |
| `generation_land_required_ha` | \(A_{\mathrm{gen}}\) | 可选 | ha | 显式给出方案实际需要的发电设施用地。 |
| `ha_per_mw_it` | \(a_{\mathrm{site}}\) | 必填 | ha/MW IT | 园区本体、变配电和冷却设施的边际用地强度。 |

土地上限按权威稿的土地一次函数模型计算：

\[
P_L=
\frac{
A_{\mathrm{eff}}-A_0^{\mathrm{IT}}-A_e
}{
a_{\mathrm{site}}
}.
\]

分子小于等于 0 时返回 0 MW IT，表示在当前设计下没有可建设的正容量。

#### A_e 候选优化

如果暂时没有确定的 \(A_e\)，可以给出一个可行候选集合：

```yaml
land:
  effective_ha: 160
  fixed_it_ha: 10
  generation_land_options_ha: [10, 20]
  ha_per_mw_it: 1.0
```

也可以在单个方案内用 `generation_land_options_ha` 覆盖。程序对每个候选
\(A_e^{(k)}\) 计算

\[
P_L^{(k)}
=
\frac{
A_{\mathrm{eff}}-A_0^{\mathrm{IT}}-A_e^{(k)}
}{
a_{\mathrm{site}}
},
\qquad
P^{(k)}=\min(P_E,P_W,P_L^{(k)}),
\]

然后选择 \(P^{(k)}\) 最大的候选；若并列，选择较小的 \(A_e\)。结果会保存：

- `generation_land_ha`：选中的 \(A_e\)；
- `generation_land_source`：`fixed`、`options`、`external` 或 `direct`；
- `generation_land_candidates`：每个候选的 \(A_e\)、\(P_L\)、\(P\) 和 binding；
- `value_source.P_L = "optimized"`。

这个选项只做**离散候选枚举**，不把 \(A_e\) 作为无约束连续变量。没有工程下限、成本或最低用地约束时，连续优化会退化为选择最小 \(A_e\)。

发电设施用地需求与设备规模相连：

```text
A_gen = A_coal + A_gas + A_wind + A_PV
A_coal = N_coal * a_unit,coal
A_gas  = N_gas  * a_unit,gas
A_wind = 100 * A_wind_km2
A_PV   = 100 * A_PV_km2
A_gen <= A_e
```

对应的 YAML 字段为 `unit_land_ha`（火电单机用地）、`area_km2`（风光资源面积）和
`generation_land_required_ha`（显式覆盖发电设施用地）。水电占地按要求不纳入
当前土地约束，水电容量仍由 \(X_{\mathrm{hydro}}\) 和 \(Q,H\) 决定。

在候选枚举时，如果某个 \(A_e^{(k)}\) 小于设备配置所需面积，程序会按土地预算缩减设备规模：

- 火电按 \(N_j^{\max}=\lfloor A_e^{(k)}/a_{\mathrm{unit},j}\rfloor\) 向下取整；
- 风电、光伏按可用面积等比例缩减 \(A_{\mathrm{wind}}\)、\(A_{\mathrm{PV}}\)，并重新计算 \(P_{\mathrm{self}}\)；
- 缩减后的实际用地和容量会写入 `generation_land_required_ha`、`generation_land_capacity_capped` 和各候选结果。

`generation_land_in_site` 用来处理边界归属：

- `true`：风电、光伏资源面积、火电厂区或电池区位于园区内，计入 \(A_e\)，并可能受发电用地预算限制；
- `false`：发电设施位于园区外，不扣园区 \(A_e\)，其资源面积仍用于计算 \(P_{\mathrm{self}}\)。

边界外的风电和光伏不能通过 `generation_land_in_site: false` 逃避其自身的资源面积约束，只是这块面积不计入园区土地上限。

### `scenarios` 字段

所有方案共有的字段：

| 字段 | 正稿符号 | 是否必填 | 说明 |
|---|---|---|---|
| `name` | \(x\) | 必填 | 方案名称，必须唯一。 |
| `type` | — | 必填 | `grid`、`coal`、`gas`、`wind`、`hydro`、`solar`、`combined_battery` 之一。 |
| `online_year` | \(y_x\) | 可选 | 方案投运年份；省略时取 `assessment_year`，即视为已投运。大于 \(y\) 时进入 `excluded`。 |
| `k_factor` | \(k(x)\) | 可选 | 覆盖该方案的设施倍率。 |
| `wue_l_per_kwh_it` | \(WUE(x)\) | 可选 | 覆盖该方案的现场 WUE。 |
| `generation_water_l_per_kwh` | \(c_i(x)\) | 可选 | 覆盖该方案自发电耗水系数，L/kWh。 |
| `generation_land_ha` | \(A_e\) | 可选 | 覆盖园区内发电站用地。 |
| `generation_land_options_ha` | \(A_e^{(k)}\) | 可选 | 覆盖发电站用地候选列表。 |
| `generation_land_in_site` | — | 可选 | 发电设施是否位于园区边界内。 |
| `unit_land_ha` | \(a_{\mathrm{unit},j}\) | 火电可选 | 单台机组厂区用地。 |
| `generation_land_required_ha` | \(A_{\mathrm{gen}}\) | 可选 | 显式覆盖发电设施用地需求。 |

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
| 未填 `online_year` | 不报错。程序按 `assessment_year` 视作已投运。 |
| `online_year` 晚于 `assessment_year` | 不报错，方案进入 `excluded`。 |
| 旧版 `C_PCC_mw`、`generation_share`、`period_budget` 或 `sensitivity` | 报错。这些字段不属于当前权威稿口径，删除后重算。 |

## JSON 输出详解

### 写出 JSON

`--json` 参数是输出文件路径，不是输入配置路径：

```powershell
python code/run.py code/examples/q1_site.yaml --json code/examples/q1_site_result.json
```

程序只在计算成功后写文件，并自动创建缺失的父目录；重复运行会覆盖同名文件。

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
| `limits_m3_h` | \(Q_{\mathrm{DC,水源}},Q_{\mathrm{DC,压力上限}},Q_{\mathrm{DC,政策上限}}\) | m³/h | 实际参与最小值的各项独立上限。 |
| `Q_max_m3_h` | \(Q_{\mathrm{DC,max}}\) | m³/h | 各项上限的最小值。 |
| `wue_l_per_kwh_it` | \(WUE\) | L/kWh IT | 直接值或按季节运行时长加权后的 WUE。 |
| `generation_water_l_per_kwh` | \(c_i\) | L/kWh | 该场址可用的自发电耗水系数。 |
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
| `generation_water_m3_h` | m³/h | 该方案自发电耗水流量 \(Q_{\mathrm{发电耗水}}\)。 |
| `Q_net_m3_h` | m³/h | 扣除发电耗水后的净可用流量 \(Q_{\mathrm{net}}\)。 |

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
| `generation_land_ha` | ha | 选中的发电设施用地 \(A_e\)。 |
| `generation_land_source` | 字符串 | `fixed`、`options`、`external` 或 `direct`。 |
| `generation_land_required_ha` | ha | 方案实际需要的发电设施用地 \(A_{\mathrm{gen}}\)。 |
| `generation_land_capacity_capped` | 布尔 | 设备容量是否因 \(A_e\) 不足而缩减。 |
| `generation_land_candidates` | 数组 | 各 \(A_e\) 候选的 \(P_L\)、\(P\) 和 binding。 |
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
