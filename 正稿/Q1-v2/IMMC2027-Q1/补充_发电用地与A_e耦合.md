# 补充：发电用地 \(A_e\) 与自建电源容量的耦合

> 本文件补全 `IMMC2027-Q1.md` 土地模型中尚未展开的发电用地约束。
> 它说明园区内规划的发电站用地 \(A_e\) 如何限制火电机组台数、
> 风电和光伏的可建面积，并反过来改变 \(P_{\mathrm{self}}\) 与
> \(P_E\)。水电占地按要求不计入；电池占地暂不单独建模。

## 1. 补充目的

Q1-v2 正文已经给出园区需地的一次函数

$$
A_{\mathrm{req}}(P)
=
A_0^{\mathrm{IT}}+A_e+a_{\mathrm{site}}P
\tag{Ae1}
$$

以及土地容量

$$
P_L
=
\max\left\{
0,\
\frac{A_{\mathrm{eff}}-A_0^{\mathrm{IT}}-A_e}{a_{\mathrm{site}}}
\right\}.
\tag{Ae2}
$$

但正文尚未展开：给定 \(A_e\) 后，火电、风电和光伏各自能建多大。
本补充给出这组耦合公式。正文土地段的 \(A_0\) 在本文件中写作
\(A_0^{\mathrm{IT}}\)，表示 IT 侧固定用地，不是发电站用地。

注意：\(A_e\) 是规划时预留的发电站用地预算，不是方案实际占满的
面积。即使式（Ae3）算出的 \(A_{\mathrm{gen}}<A_e\)，式（Ae2）仍
按完整的 \(A_e\) 扣除；未用完的预留地不能自动转给 IT 设备。

## 2. 符号与程序字段

| 符号 | 含义 | 程序字段 | 单位或说明 |
|---|---|---|---|
| \(A_{\mathrm{eff}}\) | 场址有效可用土地 | `effective_ha` | ha |
| \(A_0^{\mathrm{IT}}\) | IT 侧固定用地 | `fixed_it_ha` | ha，可为 0 |
| \(A_e\) | 园区内自建发电站及专属配套用地预算 | `generation_land_ha` | ha |
| \(A_e^{(k)}\) | 第 \(k\) 个发电站用地候选 | `generation_land_options_ha` | ha |
| \(a_{\mathrm{site}}\) | IT 侧边际用地强度 | `ha_per_mw_it` | ha/MW IT |
| \(A_{\mathrm{gen}}\) | 方案实际需要的发电设施用地 | `generation_land_required_ha` | ha |
| \(a_{\mathrm{unit},j}\) | 单台火电机组厂区用地 | `unit_land_ha` | ha/台 |
| \(N_j\) | 可同时运行的火电机组台数 | `units` | 台 |
| \(p_j^{\mathrm{net}}\) | 单机持续净功率 | `unit_net_mw` | MW |
| \(A_{\mathrm{wind,km^2}}\) | 风电合格面积 | `area_km2` | km² |
| \(A_{\mathrm{PV,km^2}}\) | 光伏合格面积 | `area_km2` | km² |
| \(A_{\mathrm{wind}},A_{\mathrm{PV}}\) | 换算成 ha 的风光用地 | 由 `area_km2` 乘 100 | ha |
| \(\rho_{\mathrm{wind}}\) | 风电装机密度 | `density_mw_per_km2` | MW/km² |
| \(\rho_{\mathrm{PV}}\) | 光伏装机密度 | `density_mw_per_km2` | MW/km² |
| \(X_{\mathrm{wind}}\) | 风电装机 | `installed_mw` | MW |
| \(X_{\mathrm{PV}}\) | 光伏装机 | 由面积乘密度计算 | MW |
| \(P_{\mathrm{self}}\) | 自建电源可靠净功率 | 计算结果 | MW |
| \(P_E\) | 电力承载上限 | `P_E_mw_it` | MW IT |

## 3. 方案实际发电用地

设方案 \(x\) 包含的发电技术集合为 \(\mathcal G(x)\)，则其发电设施
用地为

$$
A_{\mathrm{gen}}(x)
=
\sum_{j\in\mathcal G(x)}A_j.
\tag{Ae3}
$$

### 3.1 火电

对煤电或燃气，若单机厂区用地为 \(a_{\mathrm{unit},j}\)，则

$$
A_j
=
N_j\,a_{\mathrm{unit},j},
\qquad
j\in\{\text{煤电},\text{燃气}\}.
\tag{Ae4}
$$

未提供 `unit_land_ha` 时，程序把该项用地记为 0，即不做火电用地
约束；这只适合缺少数据时的初筛，不应作为详细选址结论。

### 3.2 风电与光伏

面积以 km² 输入，而土地预算以 ha 计，换算关系为

$$
1\ \mathrm{km^2}=100\ \mathrm{ha}.
\tag{Ae5}
$$

因此

$$
A_{\mathrm{wind}}=100\,A_{\mathrm{wind,km^2}},
\qquad
A_{\mathrm{PV}}=100\,A_{\mathrm{PV,km^2}}.
\tag{Ae6}
$$

风电装机由面积与密度给出：

$$
X_{\mathrm{wind}}=A_{\mathrm{wind,km^2}}\,\rho_{\mathrm{wind}},
\qquad
P_{\mathrm{wind}}=\alpha_{\mathrm{wind}}X_{\mathrm{wind}}.
\tag{Ae7}
$$

若同时给出 `installed_mw` 与密度，程序可用
\(A_{\mathrm{wind,km^2}}=X_{\mathrm{wind}}/\rho_{\mathrm{wind}}\)
反推面积。若只给 `installed_mw`，又没有面积、密度或显式
`generation_land_required_ha`，则无法把该风电方案与 \(A_e\)
耦合，程序不会凭空估计其占地。

光伏必须由面积与密度给出装机：

$$
X_{\mathrm{PV}}=A_{\mathrm{PV,km^2}}\,\rho_{\mathrm{PV}},
\qquad
P_{\mathrm{PV+st}}
=
f_{\mathrm{PV+st}}\left(X_{\mathrm{PV}},\mathcal W,\ldots\right).
\tag{Ae8}
$$

### 3.3 水电、电池和边界外电源

- 水电占地按要求不纳入当前土地约束；水电容量仍由装机
  \(X_{\mathrm{hydro}}\)、流量 \(Q\) 和净落差 \(H\) 决定。
- 电池占地暂不单独建模。若需要把电池区计入园区，请用
  `generation_land_required_ha` 显式给出。
- `combined_battery` 方案目前也用 `generation_land_required_ha`
  显式给出风光及电池合计用地；程序不把合计装机 \(X_{\mathrm{风+光}}\)
  自动拆成风电和光伏面积。
- 若某方案实际发电设施用地已知，可用
  `generation_land_required_ha` 直接覆盖式（Ae3）的计算结果。
- `generation_land_in_site: false` 表示发电设施位于园区边界外：
  这块地不从 \(A_{\mathrm{eff}}\) 中扣除，也不受园区 \(A_e\)
  预算约束；但风电和光伏的资源面积仍决定其可建容量。

## 4. 用 \(A_e\) 限制设备规模

园区内发电设施必须满足

$$
A_{\mathrm{gen}}(x)\le A_e.
\tag{Ae9}
$$

当 \(A_e\) 小于原配置所需面积时，程序按技术类型缩减设备规模，
而不是把不存在的土地当作可用。

### 4.1 火电按整台机组向下取整

$$
N_j^{\max}
=
\left\lfloor
\frac{A_e}{a_{\mathrm{unit},j}}
\right\rfloor,
\qquad
N_j'
=
\min\left\{N_j,N_j^{\max}\right\}.
\tag{Ae10}
$$

缩减后的容量为

$$
P_j'
=
N_j'\,p_j^{\mathrm{net}}.
\tag{Ae11}
$$

若 \(A_e<a_{\mathrm{unit},j}\)，连一台机组都放不下，该 \(A_e\)
候选不可行。

### 4.2 风电和光伏按面积等比例缩减

对 \(i\in\{\mathrm{wind},\mathrm{PV}\}\)，定义面积缩减系数

$$
s_i
=
\min\left\{
1,\
\frac{A_e}{100\,A_{i,\mathrm{km^2}}}
\right\}.
\tag{Ae12}
$$

则

$$
A_{i,\mathrm{km^2}}'
=
s_i A_{i,\mathrm{km^2}},
\qquad
X_i'
=
A_{i,\mathrm{km^2}}'\rho_i.
\tag{Ae13}
$$

风电若使用同期净功率序列，序列按同一 \(s_i\) 缩放；若使用
\(\alpha_{\mathrm{wind}}\)，则

$$
P_{\mathrm{wind}}'
=
\alpha_{\mathrm{wind}}X_{\mathrm{wind}}'.
\tag{Ae14}
$$

光伏和光储使用缩减后的 \(X_{\mathrm{PV}}'\) 重新代入正文式（5）
和附录 A；电池的 \(C_{\max},D_{\max},E_{\mathrm{usable}}\) 不因
光伏面积缩减而自动改变。

### 4.3 显式发电用地

若给出 `generation_land_required_ha`，则把它视为已经确定的
设备方案用地：

$$
A_{\mathrm{gen}}^{\mathrm{explicit}}\le A_e.
\tag{Ae15}
$$

不满足时该 \(A_e\) 候选不可行；满足时不再按比例缩减设备容量。
这意味着显式值是“固定设计”，而式（Ae10）–（Ae13）是“可缩放
设计”。

## 5. A_e 候选与最优方案

当 \(A_e\) 尚未确定时，可以给出工程上可行的离散候选
\(A_e^{(k)}\)。对每个候选分别计算

$$
P_E^{(k)}
=
\frac{P_{\mathrm{grid}}+P_{\mathrm{self}}\left(A_e^{(k)}\right)}
{k(x)},
\qquad
P_W^{(k)}
=
\frac{
\max\left\{0,Q_{\mathrm{DC,max}}-Q_{\mathrm{发电耗水}}^{(k)}\right\}
}{WUE},
\tag{Ae16}
$$

$$
P_L^{(k)}
=
\max\left\{
0,\
\frac{A_{\mathrm{eff}}-A_0^{\mathrm{IT}}-A_e^{(k)}}{a_{\mathrm{site}}}
\right\},
\qquad
P^{(k)}
=
\min\left\{P_E^{(k)},P_W^{(k)},P_L^{(k)}\right\}.
\tag{Ae17}
$$

然后选择

$$
A_e^\star
=
\arg\max_{A_e^{(k)}}\ P^{(k)},
\tag{Ae18}
$$

若 \(P^{(k)}\) 并列，选择较小的 \(A_e^{(k)}\)。这里的关键权衡是：
增大 \(A_e\) 可能提高自建电源容量，从而提高 \(P_E\)；但它同时
减少可留给 IT 设备的土地，使 \(P_L\) 下降。最优值来自两者与
水约束的联合比较，而不是单纯让 \(A_e\) 取最大。

候选枚举是离散搜索，不把 \(A_e\) 当作无约束连续变量。若没有
工程下限、成本或最小用地约束，连续模型会自然选择最小的
\(A_e\)，无法代表真实地块的可行性。

### 5.1 燃机实际出力如何进入水预算

对给定的发电用地候选，先用式（Ae10）–（Ae11）确定能建几台燃机及其最大净出力。设园区优先使用电网，燃机可以停机，也可以在零至最大净出力之间连续调节。若要维持 \(P\) MW 的 IT 负载，设施共需 \(k(x)P\) MW 电力。电网供满后，燃机补足其余部分。用 \(g(P)\) 表示实际调用的燃机净出力，则供电和用水须同时满足

$$
g(P)=\max\{0,k(x)P-P_{\mathrm{grid}}\},\qquad
g(P)\le P_{\mathrm{self}}\!\left(A_e^{(k)}\right),
$$

$$
\mathrm{WUE}\,P+c_{\mathrm{气}}\,g(P)\le Q_{\mathrm{DC,max}}.
$$

式（Ae16）中的发电用水随 \(P\) 变化。上式左侧两项分别是园区现场取水和燃机从同一水预算中取用的水。功率用 MW、用水系数用 L/kWh 时，两项均为 m³/h。若限制的是日总量，在负载与出力恒定的条件下，将两项之和乘以 24 即得 m³/day。现场 WUE 为零时，仍须满足燃机的取水约束。

以湿冷燃气演示方案为例，电网可供 108 MW，燃机最多可供 60 MW，设施用电倍率为 1.2。电力上限为 \((108+60)/1.2=140\) MW IT。单靠电网可支撑 90 MW IT，此时现场每小时取水 \(1.5\times90=135\) m³，距 150 m³/h 的预算还剩 15 m³/h。

在 90 MW IT 的基础上，每增加 1 MW IT，现场每小时多取 1.5 m³ 水。燃机还要增发 1.2 MW，每小时多取 \(0.78\times1.2=0.936\) m³ 水。因此剩余水量还能支撑 \(15/(1.5+0.936)\approx6.16\) MW IT。该方案的土地上限为 130 MW IT，水量先达到上限，联合容量约为 **96.16 MW IT**，对应的燃机实际出力约为 **7.39 MW**。

## 6. 与最终容量的衔接

对每个进入候选集的方案，最终仍按

$$
P(x)
=
\min\left\{P_E(x),P_W(x),P_L(x)\right\},
\qquad
P_{\max}(y)
=
\max_{x\in\mathcal X_y}P(x)
\tag{Ae19}
$$

计算。\(A_e\) 通过 \(P_{\mathrm{self}}\) 进入 \(P_E\)，通过
发电耗水进入 \(P_W\)，并通过式（Ae2）进入 \(P_L\)。因此它不是
一个只出现在土地公式里的常数，而是连接土地、电力和水的方案级
设计变量。

若所有方案都使用电网，取 \(A_e=0\)。若发电设施在园区外，取
园区侧 \(A_e=0\)，不执行式（Ae9）的园区预算约束。

## 7. 当前实现的对应位置

- `code/immc_power_capacity/core.py:752` 的 `land_capacity`：
  式（Ae1）–（Ae2）。
- `core.py:825` 的 `_generation_area_km2`、`core.py:848` 的
  `_generation_land_required`：
  式（Ae3）–（Ae8）。
- `core.py:872` 的 `_cap_generation_by_land`：式（Ae9）–（Ae15）。
- `core.py:941` 的 `_resource_row_single`：处理边界外发电设施不扣
  园区土地。
- `core.py:1108` 的 `_resource_row`：式（Ae16）–（Ae18）的候选枚举。
- 测试覆盖：
  `test_generation_land_must_cover_resource_area`（光储面积缩减）、
  `test_external_wind_land_is_not_deducted`（边界外风电），
  `test_wind_installed_capacity_scales_with_land`（风电装机随面积缩减）。

## 8. 算例

以下均为测试数据，不代表真实场址：

- `q1_site_ae_options.csv`：候选 \(A_e=10\) ha 与 \(20\) ha，程序
  选择使联合容量最大的候选，并记录每个候选的 \(P_L\)、\(P\) 与
  binding。
- 光储面积 \(0.2\) km² = 20 ha，若只给 \(A_e=10\) ha，则面积
  缩减为 10 ha，\(P_{\mathrm{self}}\) 重新计算。
- 风电面积 1 km² = 100 ha，若只给 \(A_e=10\) ha，则面积缩减为
  0.1 km²；装机 100 MW 按比例缩减为 10 MW，再乘
  \(\alpha_{\mathrm{wind}}=0.2\) 得到 2 MW 可靠净功率。

这些结果只解释所给配置和考察期，不直接外推为全年或真实场址的
可靠容量。
