# 从地理可用水量到 IT 功率：证据链与中文译读

**范围**：本页只为“水文条件能提供多少水，再用现场取水 WUE 讨论 IT 功率上限”找依据；不是某个地点的取水许可或完整求解。下文“译读”为对原文要点的中文意译，不是逐字引文。书目、原始网址及已取得的 PDF 见文末；正文角标与书目编号对应。

## 证据链

1. **水文上有多少水**：取水口在有关月份的可靠流量，不能仅以年平均代替；生态流量应保留。Hoekstra 等用月度自然径流扣除假定环境流量，讨论“可用蓝水”与既有耗水的关系。其核算对象是**耗水足迹**，不是某项目的最大**取水**许可；作者使用的环境预留比例也不能不加核验地搬到选定河段。<sup>[1]</sup>
2. **多少水能送到中心**：还需分清取水口位置、下游已承诺的供水、取输水设施能力。水文站的实际流量一般已经包含上游取水造成的影响；不能重复扣除。Aqueduct 的区域水压力可提示竞争风险，但其风险得分不是可新增取水量，不能直接乘以单站河流流量。<sup>[1][2]</sup> 若这些本地资料缺失，只能报告条件性/情景性上限，不宜称为已核实的项目可用水量。
3. **同口径 WUE 到 IT 功率**：Mytton 定义的现场 WUE 用现场用水量除以同期 IT 用电量。采用**现场取水 WUE**时，给定同一时期中心能稳定取得的水量，可以反推该时期支持的 IT 用电量；再结合运行时长和负载假设讨论持续 IT 功率。不能把发电间接用水、耗水 WUE、额定功率与实际 IT 用电量混用。<sup>[3]</sup>
4. **WUE 必须匹配冷却条件**：NREL 的高性能计算中心案例报告，采用混合冷却后第一年现场 WUE 为 0.70 L/kWh；报告给出的“若仍仅采用既有余热回收和冷却塔”反事实 WUE 为 1.27 L/kWh。前者是该中心运行结果，后者是报告中的比较情景，不是两个通用系数。<sup>[4]</sup>

**最简换算（由 WUE 定义推得，并非论文给出某地上限）**：若同一时期中心可取水量为 `V` m³，现场取水 WUE 为 `w` L/kWh，持续 `t` 小时且 IT 设备平均负载率为 `u`，则额定 IT 功率上限为 `V / (w × t × u)` MW；这里 m³→L 与 kW→MW 的两个 1000 正好抵消。若只求该时段**平均实际 IT 功率**，令 `u = 1`。`w = 0` 时不能用该反推式；还应单独检查电力、冷却和设备约束。<sup>[3]</sup>

**计算边界提醒**：文献支持“可用水量、现场取水 WUE、IT 用电”之间的单位关系，但没有哪篇文献能从某地 Aqueduct 风险级别和一条河的总流量，直接给出具体项目已获保障的取水量。若用枯水期日供水检查全年持续运行，应匹配同季节/同冷却工况的用水强度及当日负载；年度平均 WUE 不能无说明地当作最热日 WUE。<sup>[1][2][3][4]</sup>

## 原文关键内容的中文译读

**[1] Hoekstra 等，2012，PLOS ONE（同行评审）**：作者认为只比较年平均供需会遮蔽月度缺水；估算可用蓝水时，应为维持河流生态功能留出流量。文中专门指出，许多工业与家庭取水会回流，因此取水量与实际耗掉的水不一样。**用于本题**：论证按枯水时段而非仅按全年平均检查物理余量；不要把论文中的“剩余可耗水”直接当成数据中心“可抽取水”。原文的全球尺度环境流量假设不等于当地法定或工程取水规则。<sup>[1]</sup>

**[2] Kuzma 等，2023，WRI Aqueduct 4.0（机构技术说明）**：该方法对不同流域的供给、需求与水压力作风险评估，还报告时间和情景差异。**用于本题**：选择需要重点核查的缺水地点；它不能替代河段可新增取水评估，也不提供数据中心独占的剩余额度。<sup>[2]</sup>

**[3] Mytton，2021，npj Clean Water（同行评审）**：数据中心的现场水使用和供电造成的间接用水须区分；现场 WUE 把同期现场水量与 IT 设备的耗电量联系起来，还需分清取水与耗水。**用于本题**：明确从中心可用**取水量**到 IT 用电的参数口径；没有规定哪个地点必然具有某个 WUE，也不能直接把 IT MW 称为芯片运算吞吐量。<sup>[3]</sup>

**[4] Sickinger 等，2018，NREL / OSTI（官方技术报告）**：作者介绍了将热虹吸冷却系统与已有冷却塔结合的实际运行，在第一年记录的现场 WUE 为 0.70 L/kWh；若仅沿用原方案，报告估计为 1.27 L/kWh。**用于本题**：证实冷却配置不同会改变适用的 WUE；案例值不可直接作为其他气候和设备条件下的普适参数。<sup>[4]</sup>

**IEEE 补充候选，暂不作全文依据**：Crossref 已核对 Singh、Singh、Kaur (2026) 的 IEEE CHANDICON 论文 *Estimating Water Consumption of Data Center Expansion in India Using a Capacity–Energy–WUE Modeling Framework*，DOI [10.1109/CHANDICON70877.2026.11767483](https://doi.org/10.1109/chandicon70877.2026.11767483)。出版社当前未提供可直接获取的全文，因此仅记录题名与书目信息，**不据题名推断论文公式、参数或结论，也不伪称已下载/已翻译原文**。Google Scholar 是检索入口而不是原始出版来源；正式引文仍以期刊、IEEE、机构原件为准。

## 可直接套用的角标与书目

正文示例：“对于取水口的水文评估，应区分枯水时段并保留生态所需流量；已有的耗水量与河道取水量不是同一个口径。<sup>[1]</sup> 数据中心可使用现场取水 WUE 将现场水量与同期 IT 用电量关联。<sup>[3]</sup> 不同冷却方案需使用匹配的 WUE。<sup>[4]</sup>”

[1] Hoekstra, A. Y., Mekonnen, M. M., Chapagain, A. K., Mathews, R. E., & Richter, B. D. (2012). Global monthly water scarcity: Blue water footprints versus blue water availability. *PLOS ONE*, 7(2), e32688. [DOI / 期刊原文](https://doi.org/10.1371/journal.pone.0032688) · [本地 PDF](15_Hoekstra_全球月度水稀缺与可用水.pdf)。

[2] Kuzma, S., et al. (2023). *Aqueduct 4.0: Updated Decision-Relevant Global Water Risk Indicators*. World Resources Institute. [DOI / 原件](https://doi.org/10.46830/writn.23.00061) · [本地 PDF](05_WRI_Aqueduct4方法.pdf)。

[3] Mytton, D. (2021). Data centre water consumption. *npj Clean Water*, 4, 11. [DOI / 期刊原文](https://doi.org/10.1038/s41545-021-00101-w) · [本地 PDF](02_Mytton_数据中心用水.pdf) · [已有详细中文译读](../02_中文译读/04_Mytton_数据中心耗水_摘要与正文中译.md)。

[4] Sickinger, D. E., Van Geet, O. D., Belmont, S. A., Carter, T., & Martinez, D. (2018). *Thermosyphon Cooler Hybrid System for Water Savings in an Energy-Efficient HPC Data Center: Results from 24 Months and the Impact on Water Usage Effectiveness*. NREL technical report. [DOI / 官方原件](https://doi.org/10.2172/1471661) · [本地 PDF](16_NREL_高性能计算中心冷却节水与WUE.pdf)。

对应 BibTeX 见 [可用水量与WUE到IT功率_参考文献.bib](可用水量与WUE到IT功率_参考文献.bib)。
