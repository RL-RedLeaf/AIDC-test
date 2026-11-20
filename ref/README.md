# A 题参考文献与政策原文

本目录现有 55 份不同的 PDF，含政策与排放资料 9 份、从旧研究库补入的 21 份、电网与容量评估 16 份，以及固定电网与园区自建电源专题 9 份。旧库另有 5 份与政策专题重合，下表保留旧编号对照。编号 `02` 的新加坡网页仅有书目线索。

**固定电网与自建电源（48–56）** 按讨论中的近似静态边界，给出从发电用地、气象、水和燃料条件到可靠供电和额定 IT 容量的模型流程，并比较 HOMER、PyPSA-Earth、热电容量和微网可靠性等方法。[模型、摘译和角标](固定电网与自建电源_终态容量模型.md) · [电力专题 BibTeX](电力子模型_引文.bib)

**电力专题（32–47）** 涵盖接入点的电网可交付容量、输配电潮流与故障、资源充足性与长期扩建、风光储能、UPS 冗余和机房冷却功率。八种方法的比较、中文摘译、公式、数据入口和逐页脚注见[从当地条件到可靠接入与 IT 容量](电力子模型_从当地条件到可靠接入与IT容量.md)。新增书目见[电力专题 BibTeX](电力子模型_引文.bib)，32 号论文沿用[旧引文键 IMMC_AV01](A题因素核验_补充引文.bib)。

引文文件：[原 28 项书目](A题参考文献.bib)、[因素核验补充引文](A题因素核验_补充引文.bib)、[政策与排放引文](政策与排放_引文.bib)。旧库尚未取得全文的书目仍见[书目导航](../research/A题文献库/书目导航.md)，不能因为有 BibTeX 条目就视为本地有 PDF。政策专题的逐条中文摘译和页码见[证据译读](政策_碳排放与污染_证据译读.md)。

## 政策、排放与地方调查

| 文件 | 来源和版本 | 用途 |
|---|---|---|
| [01 爱尔兰监管决定](01_CRU2025236_Ireland_Grid_Connection.pdf) | [CRU 官网公告](https://www.cru.ie/about-us/news/the-cru-publishes-its-decision-on-new-electricity-connection-policy-for-data-centres/)，CRU2025236，PDF 134 页 | 数据中心接入、关联电源/储能及新增可再生电力要求 |
| [03 范围二核算指南](03_GHG_Protocol_Scope2_Guidance.pdf) | [GHG Protocol 原版](https://ghgprotocol.org/sites/default/files/2023-03/Scope%202%20Guidance.pdf)，PDF 120 页 | 区域法、市场法、绿证和物理电力的区别 |
| [04 世界银行集团通用 EHS 指南](04_IFC2007_General_EHS_Guidelines.pdf) | [IFC 原版](https://www.ifc.org/content/dam/ifc/doc/2000/2007-general-ehs-guidelines-en.pdf)，2007，PDF 99 页 | 空气、污水、噪声及评价方法；技术参考，非普适法律 |
| [05 爱尔兰输电接入执行流程](05_EirGrid2026_DC_Connection_Process.pdf) | [EirGrid v3 原版](https://cms.eirgrid.ie/sites/default/files/publications/Data-Centre-Connection-Offer-Process-and-Policy-V3-May-2026.pdf)，2026-05-20，PDF 31 页 | 项目级配套电源/储能及可再生电力方案如何申报 |
| [06 中国专项行动计划](06_NDRC2024_Green_Data_Centers.pdf) | [国家发改委发布页](https://www.ndrc.gov.cn/xwdt/tzgg/202407/t20240723_1391895.html)，PDF 7 页，旧库编号 27 | 能效、节能审查、绿电目标、节水评价 |
| [07 弗吉尼亚数据中心调查](07_JLARC2024_Virginia_Data_Centers.pdf) | [JLARC 原版](https://jlarc.virginia.gov/pdfs/reports/Rpt598.pdf)，2024，PDF 156 页，旧库编号 V08 | 备用机排放许可、水权、邻里噪声实际案例 |
| [08 IEEE 碳感知调度作者稿](08_Radovanovic2021_Carbon_Aware_Computing.pdf) | [IEEE 正式版](https://doi.org/10.1109/TPWRS.2022.3173250)，本地为 2021 arXiv 作者稿，共 14 页 | 有弹性任务的排放降低机制 |
| [09 Nature Sustainability 美国 AI 服务器研究](09_Xiao2025_AI_Servers_Environmental_Impact.pdf) | [期刊 DOI](https://doi.org/10.1038/s41893-025-01681-y)，本地 PDF 16 页 | 选址、技术和电网脱碳与足迹的关系 |
| [10 联合国大学环境足迹报告](10_UNU2026_AI_Environmental_Cost.pdf) | [UNU-INWEH 原版](https://unu.edu/sites/default/files/2026-10/UNU-INWEH-Report-The_Env_Cost_of_AI-2026.pdf)，本地 PDF 56 页 | 碳、水、土地的跨资源权衡与题面数字核对 |

## 旧研究库 PDF 对照与摘要

以下编号沿用旧库，`V` 表示因素核验阶段的补充文献。右栏是摘要要点及对 A 题的用途，不是可直接套用到任一场址的参数。11 篇已有逐段中文译读，可从[译读目录](../research/A题文献库/02_中文译读/按三道小问读论文.md)进入。

| 旧编号 | 本目录 PDF | 摘要要点及使用边界 |
|---|---|---|
| 01 | [Masanet 2020，全球数据中心能耗](11_Masanet2020_Data_Center_Energy.pdf) | 自下而上估计 2010–2018 年计算服务增长与能耗脱钩；历史通用服务器效率不能直接外推到新 GPU 园区。 |
| 02 | [Xiao 2025，美国 AI 服务器环境影响](09_Xiao2025_AI_Servers_Environmental_Impact.pdf) | 美国 2024–2030 年部署情景显示用水和排放受选址、效率与电网变化影响；并非单站承载 MW。 |
| 03 | [Siddik 2021，美国数据中心足迹](12_Siddik2021_US_Data_Center_Footprints.pdf) | 将现场、供排水和发电造成的水/碳足迹定位到流域；2018 年一般数据中心样本只提供核算方法与量级参照。 |
| 04 | [Mytton 2021，数据中心耗水](13_Mytton2021_Data_Center_Water.pdf) | 解释现场冷却、发电间接耗水和用水披露缺口；明确取水、净耗水与 WUE 的分母。 |
| 05 | [Boulay 2018，AWARE](14_Boulay2018_AWARE_Water_Scarcity.pdf) | 以满足人和生态需求后的相对剩余水量加权耗水，衡量稀缺影响；表征因子不是新增取水许可量。 |
| 06 | [Macknick 2012，发电用水系数](15_Macknick2012_Electricity_Water_Factors.pdf) | 汇总各电源及冷却技术的运行期取水和净耗水系数；保留技术、冷却方式、范围和单位。 |
| 07 | [Lovering 2022，发电用地强度](16_Lovering2022_Electricity_Land_Use.pdf) | 比较按年发电量归一的土地强度；不同技术跨度大，风电实际扰动与场内间距不可混算。 |
| 08 | [NREL 2013，太阳能电站用地](17_NREL2013_Solar_Land_Use.pdf) | 美国地面光伏和光热场址按装机/年发电量、直接/总面积分列；旧样本需按当代技术作敏感性检查。 |
| 09 | [NREL 2009，风电场用地](18_NREL2009_Wind_Land_Use.pdf) | 172 个既有或拟建项目区分道路与基座的直接扰动、完整项目边界；两类土地口径相差很大。 |
| 11 | [Radovanović，碳感知调度](08_Radovanovic2021_Carbon_Aware_Computing.pdf) | 按次日碳强度预测延迟可延期任务，以小时容量曲线保住日内任务量；本地是作者稿。 |
| 13 | [Li 2024，地理负载均衡公平性](19_Li2024_Equitable_AI_Load_Balancing.pdf) | 推理调度显式降低地区间最高环境代价；环境负担公平与用户端能否获得算力仍是两个指标。 |
| 14 | [Attenni 2026，云任务三足迹](20_Attenni2026_Cloud_Three_Footprints.pdf) | 云任务跨时空迁移对碳、水、土地有不同优化结果；分别优化得到的最大收益不能相加，也不能视为已建土地立即释放。 |
| 16 | [WRI 2023，Aqueduct 4.0](21_WRI2023_Aqueduct_4.pdf) | 13 项数量、质量及声誉风险指标与未来流域情景用于风险筛查；综合风险分值不是可分配立方米。 |
| 17 | [UNU-INWEH 2026，碳水地足迹](10_UNU2026_AI_Environmental_Cost.pdf) | 2030 年约 945 TWh、9.3 万亿升和逾 14,500 km² 属全球全部数据中心电力情景；AI 用电占比情景为 40%，约 378 TWh。 |
| 21 | [Jiang 2025，WaterWise](22_Jiang2025_WaterWise.pdf) | 跨地域并行任务的碳水共同优化；只压低碳足迹可能加重用水。 |
| 22 | [Hsieh 2017，Gaia](23_Hsieh2017_Gaia_Geo_Distributed_ML.pdf) | 跨广域网同步是跨地训练瓶颈，改进通信可缓解；旧实验速度比不可作为现代大模型统一效率折扣。 |
| 23 | [IEA 2025，Energy and AI](24_IEA2025_Energy_and_AI.pdf) | 全球数据中心用电及电源/电网情景，2030 年约 945 TWh 为全部数据中心；全球装机不能替代某园区可靠接入容量。 |
| 25 | [Colangelo 现场削峰试验](25_Colangelo2025_Grid_Interactive_AI.pdf) | 菲尼克斯 256 GPU 集群三小时约 25% 降功率且满足所测 QoS；不能外推为所有负载可全天削峰。 |
| 26 | [Luccioni 2024，推理能耗](26_Luccioni2024_Inference_Energy.pdf) | 88 个模型、10 类任务以每 1,000 次推理比较能耗/碳；跨部署比较须固定任务质量与延迟要求。 |
| 27 | [中国绿色低碳专项行动计划](06_NDRC2024_Green_Data_Centers.pdf) | 对新建项目、枢纽节点分别规定能效目标并鼓励非实时任务迁移；政策目标有年份和适用范围。 |
| NERC | [2025 长期可靠性评估](27_NERC2025_Long_Term_Reliability.pdf) | 基于 2025 年规划数据评估 2026–2035 年北美资源充足性；2025 是评估版次，封面出版时间为 2026 年 1 月。 |
| V02 | [Turek 2021，中尺度气候与选址](28_Turek2021_Data_Center_Site_Selection.pdf) | 德国参考机房的地点变化影响再冷却机组能耗；所报节省率不代表设施总电量同比下降。 |
| V03 | [Gupta 2021，Chasing Carbon](29_Gupta2021_Chasing_Carbon.pdf) | 计算设备制造与运行的碳需全寿命核算；作者稿结论不能代替各国服务器实测制造系数。 |
| V07 | [Wu 2022，Sustainable AI](30_Wu2022_Sustainable_AI.pdf) | 从数据、算法、硬件和生命周期理解 AI 碳足迹；企业特定任务结构不可普遍化。 |
| V08 | [JLARC 2024，弗吉尼亚调查](07_JLARC2024_Virginia_Data_Centers.pdf) | 调查电力扩建、费用、水资源、柴油机排污和噪声，既记录局地问题也记录当时总体用水可持续。 |
| V09 | [ITU-T L.1300，绿色数据中心实践](31_ITU2014_Green_Data_Centres.pdf) | 分计设施与 ICT 设备用能，记录各来源水量，按气候选择冷却；工程建议不是各国统一法定限值。 |

来自其他研究者的作者稿用于队内研读；对外引用以 BibTeX 中的正式版本为准，二次传播与全文翻译按出版方许可处理。中文译读及本页摘要只供导航，不代替法规、论文原文或具体场址的资源预算。
