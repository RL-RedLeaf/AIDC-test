# IMMC 2027 A 题第一问真实场址数据

## 模型定位

本目录服务于 Q1-v2 的“给定场址最大可持续规模”模型。输出是：

\[
P(x)=\min\{P_E(x),P_W(x),P_L(x)\},\qquad
P_{\max}=\max_{x\in\mathcal X_y}P(x).
\]

其中 \(P_{\max}\) 是在同一场址、同一设计期和同一服务水平下，电力、水和土地同时满足时能够支撑的最大额定 IT 负载。它不是实际运行负载、年耗电量、设备铭牌容量、并网许可或可靠容量保证。

公开项目规模用于两类检查：

- 校准设施功率、场址面积、WUE 和冷却等工程参数；
- 把模型上界与实际或规划规模比较，并解释差异。

部分案例的电力或土地输入由公开规模反推，因此它们首先是一致性情景，不能当作独立预测。每个结果的 `near_binding_within_0_1pct` 字段保留了三个约束中相差不到 0.1% 的项目，避免把四舍五入造成的微小差异解释成唯一瓶颈。

这不是合格的模型验证。编号 28 的审计逐项标出了循环参数；编号 30–31 另做了一套 Abilene 底部向上测试，只使用 1.2 GW 公共接入、1,100 英亩场址、每栋楼年度冷却补水量、共同设施/IT 倍率和跨站点土地强度，不采用 Epoch 给 Abilene 的 IT 目标。

## 目录

| 路径 | 内容 |
|---|---|
| `raw/` | 2026-11-21 下载的 Epoch AI 站点与时间线原始 CSV |
| `outputs/00_output_index.csv` | 全部 35 个编号输出的总索引，记录输入、意义、条件、用途与置信状态 |
| `outputs/01-10_*` | 站点库存、重点场址表、来源表、技术参数、比较表和质量审计 |
| `outputs/11-18_*_input.yaml` | 可直接交给当前 `code/run.py` 的编号模型配置 |
| `outputs/19-26_*_result.json` | 与上述输入一一对应的完整 Q1 计算结果 |
| `outputs/27_water_stress_exact.csv` | 七个站点所在流域的 Aqueduct 原始 BWS、地下水与干旱数值 |
| `outputs/28_calibration_audit.csv` | 逐案例说明哪些参数由公布容量反推，以及结果是否属于循环验证 |
| `outputs/29_hyperion_plan_vs_model.csv` | Hyperion 现状、首期、1.8 GW 接入和 5 GW 规划的同口径差异 |
| `outputs/30-31_*` | 不采用 Abilene IT 目标值的独立参数测试及其结果 |
| `outputs/32_abilene_nasa_power_2025.csv` | Abilene 2025 年逐日温度、辐照、风速和降水 |
| `outputs/33_data_manifest.json` | 原始快照哈希、数据集定位、文件清单与许可信息 |
| `outputs/34_bottom_up_inputs.csv` | 八套独立底层输入，项目实际 IT 只放在对照列，不参与计算 |
| `outputs/35_bottom_up_results.csv` | 逐案例一层公式计算及与当前/规划 IT 的误差 |
| `outputs/10_sites.geojson` | 可在 QGIS 打开的重点场址点图层 |
| `scripts/` | 重建库存和批量运行 Q1 的脚本 |

`data/outputs/` 是唯一的结果发布目录。每个文件均以连续编号开头，编号不会随时间点或名称排序而改变。

## 已识别的主要口径冲突

| 场址 | 公开数字的差异 | 本目录的处理 |
|---|---|---|
| Colossus 2 | 约 946 MW 是 Epoch 当前 IT 估计，1,276 MW 是同口径设施功率；题面的 950 MW 是近似值 | 保留当前与 2027 投影；不把 950 当成独立测量 |
| Fairwater Wisconsin | Compute Atlas 给出约 1,000 MW 公开园区容量；Epoch 对 11 栋扩建给出 2,263 MW IT / 2,715 MW 设施功率 | 拆成 public phase 与 Epoch expansion 两个 Q1 情景 |
| Meta Hyperion | 1.8 GW 是 MISO 接入负荷，2.262 GW 是初期燃气轮机容量，2 GW 是首期园区表述，5 GW 是 Meta 的最大算力/园区描述 | 不把这些数相加；正常运营情景排除备份燃机，单独保留 5 GW 扩张情景 |
| New Carlisle | 2.2 GW 是全场接入上界，1,925 MW 是 Epoch 的扩建 IT 投影，2.310 GW 是 Epoch 设施功率，1.58 MGD 是 Phase 1 排水上限 | Q1 使用 2.2 GW 公共接入上界；水预算使用公开的每年 1,800 万加仑，而非把排水上限当取水 |
| Abilene | Oracle 的 618 MW 未说明是 IT 还是设施；Epoch 的 824 MW 是 IT 估计；1.2 GW 是并网/园区容量 | 正常运营使用 1.2 GW 电网；360.5 MW 现场燃气按备份电源处理，不计入基准 |

## 重点场址结论

以下均以 `outputs/09_q1_case_summary.csv` 为准，单位是 MW IT：

| 情景 | \(P_E\) | \(P_W\) | \(P_L\) | \(P_{\max}\) | 近触顶约束 |
|---|---:|---:|---:|---:|---|
| Colossus 1，2026 | 457.6 | 438.5 | 340.0 | 340.0 | 土地 |
| Fairwater Atlanta，规划电网 | 1,110.6 | 157,700 | 1,110.5 | 1,110.5 | 电力、土地 |
| Fairwater Wisconsin，公开园区 | 833.5 | 2,263.0 | 4,167.5 | 833.5 | 电力 |
| Fairwater Wisconsin，Epoch 扩展 | 2,263.0 | 2,263.0 | 4,167.5 | 2,263.0 | 电力、水 |
| New Carlisle，2028 | 1,833.3 | 1,924.8 | 1,925.0 | 1,833.3 | 电力 |
| Hyperion，2028 首期 | 1,333.5 | 2,000.6 | 1,333.4 | 1,333.4 | 电力、土地 |
| Hyperion，5 GW 扩张 | 3,704.0 | 5,005.3 | 3,704.3 | 3,704.0 | 电力、土地 |
| Stargate Abilene，2026 | 856.8 | 1,212.2 | 824.0 | 824.0 | 土地 |
| Stargate Abilene，独立公共参数测试 | 923.1 | 923.1 | 1,764.4 | 923.1 | 电力、水近并列 |

Fairwater、New Carlisle 和 Abilene 的土地强度由公开场址面积与项目规模校准，因此这些案例的土地结果主要用于检查边界一致性，不是独立土地预测。Hyperion 的 2028 首期只使用 MISO 的 1.8 GW 接入负荷，不把备份燃机加入正常容量；其约 1.33 GW IT 结果低于 Epoch 的 1.63 GW 投影。Hyperion 的 5 GW 情景说明，即使假定 5 GW 可到园区，按约 1.35 的设施/IT 倍率，可比 IT 容量约为 3.7 GW。

## 电源技术差异

`outputs/05_generation_technology_factors.csv` 采用运行阶段口径：

- 煤电湿冷塔：耗水中位数约 687 gal/MWh，即 2.60 L/kWh；
- 天然气联合循环湿冷塔：约 205 gal/MWh，即 0.78 L/kWh；
- 天然气联合循环干冷：约 2 gal/MWh，即 0.008 L/kWh；
- 风电：运行耗水中位数 0；
- 光伏：中位数 1 gal/MWh，即 0.004 L/kWh。

土地比较必须区分直接扰动和项目间距。风电直接占地中位数约 130 ha/TWh/年，但项目间距中位数约 12,000 ha/TWh/年；天然气直接占地约 410 ha/TWh/年，加上气田间距约 1,900 ha/TWh/年。两者不能只报一个“风电/天然气占地”数字。

## 复现

在仓库根目录运行：

```powershell
python data/scripts/build_epoch_inventory.py
python data/scripts/run_q1_cases.py
python data/scripts/build_output_index.py
python data/scripts/validate_dataset.py
```

在 QGIS 中打开 `data/outputs/10_sites.geojson` 可查看重点场址位置。坐标主要用于定位和后续 GIS 核查，不代表已完成地块产权或生态边界筛选。

## 当前限制

- Epoch 最新记录包含未来投影；`record_scope` 和 `current_record_date` 已保留区别。
- WRI Aqueduct 的流域水压力不是可分配的立方米，也不是项目取水许可。
- 冷却方式、WUE、接入容量和占地边界经常不是同一来源、同一年份或同一阶段。
- 备份电源不等于正常生产容量；本目录不把 N-1 或事故备用加入基准 Q1。
- 场址面积是项目边界或公开土地规模，还不是扣除道路、湿地、洪泛区和生态禁建后的 \(A_{\mathrm{eff}}\)。
- 当前结果是公共数据条件下的条件容量与敏感性情景，不是审批结论。

## 主要来源

原始检索入口：

- Epoch AI 数据中心库：<https://epoch.ai/data/ai-data-centers>
- Epoch 站点 CSV：<https://epoch.ai/data/data_centers/data_centers.csv>
- Epoch 时间线 CSV：<https://epoch.ai/data/data_centers/data_center_timelines.csv>
- Compute Atlas 场址记录：<https://www.compute-atlas.com/dataset>
- WRI Aqueduct 4.0：<https://www.wri.org/data/aqueduct-water-risk-atlas>

具体来源、用途和网页地址见 `outputs/04_source_registry.csv`。每个输出的完整元数据见 `outputs/00_output_index.csv`。
