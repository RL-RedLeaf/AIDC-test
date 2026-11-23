# -*- coding: utf-8 -*-
"""结构重构（第一步）：标题层级、公式自动编号与标签、图表题注、交叉引用。

约定：
- 标题全部交给 LaTeX 自动编号（三级编号 + 四级 \\paragraph + 五级 \\subhead 不编号）
- 每条显示公式都变成 equation 环境并带 \\label{eq:...}，去掉原稿手写的 \\tag
- 图/表题注去掉原稿手写的“图 4-1　”前缀，编号由 LaTeX 生成
- 正文里的“第 1–3 节”“式（7）”“图 4-1”“附录 C”等改成 \\ref/\\eqref
"""
import io
import os
import re
import sys

SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

# ---------------------------------------------------------------- 标题
HEADINGS = {
    "01-intro.tex": [
        ("\\section{引言}", "\\section{问题重述}\\label{sec:restate}"),
        ("\\subsection{问题重述}", "\\subsection{问题背景}\\label{sec:background}"),
        ("\\subsection{1　问题一：集中式 AIDC 的最大可持续规模}",
         "\\subsection{问题一：集中式 AIDC 的最大可持续规模}\\label{sec:problem1}"),
        ("\\subsection{2　问题二：弹性分布式算力网络的替代效益与边界}",
         "\\subsection{问题二：弹性分布式算力网络的替代效益与边界}\\label{sec:problem2}"),
    ],
    "02-q1.tex": [
        ("\\section{第一问}", "\\section{模型的建立与求解}\\label{sec:model}"),
        ("\\subsection{可持续规模上限}",
         "\\subsection{第一问：集中式 AIDC 的最大可持续规模}\\label{sec:q1}\n"
         "\n\\subsubsection{可持续规模上限}\\label{sec:scale}"),
        ("\\subsection{1　能源约束}", "\\subsubsection{能源约束}\\label{sec:q1-energy}"),
        ("\\subsubsection{1.1　火力发电}", "\\paragraph{火力发电}\\label{sec:thermal}"),
        ("\\subsubsection{1.2　风力发电}", "\\paragraph{风力发电}\\label{sec:wind}"),
        ("\\subsubsection{1.3　光伏与储能}", "\\paragraph{光伏与储能}\\label{sec:pv}"),
        ("\\subsubsection{1.4　水力发电}", "\\paragraph{水力发电}\\label{sec:hydro}"),
        ("\\subsection{2　水资源约束}", "\\subsubsection{水资源约束}\\label{sec:q1-water}"),
        ("\\subsubsection{2.1　水压力限制}", "\\paragraph{水压力限制}\\label{sec:water-pressure}"),
        ("\\subsubsection{2.2　水源可支持的新增取水量}",
         "\\paragraph{水源可支持的新增取水量}\\label{sec:water-avail}"),
        ("\\subsubsection{2.3　自发电耗水}", "\\paragraph{自发电耗水}\\label{sec:water-gen}"),
        ("\\subsection{3　土地资源约束}", "\\subsubsection{土地资源约束}\\label{sec:q1-land}"),
        ("\\subsubsection{3.1　候选场址选定}", "\\paragraph{候选场址选定}\\label{sec:land-site}"),
        ("\\subsubsection{3.2　功率与需地}", "\\paragraph{功率与需地}\\label{sec:land-power}"),
        ("\\subsubsection{3.3　最大场址}", "\\paragraph{最大场址}\\label{sec:land-max}"),
        ("\\subsection{4　结果讨论}", "\\subsubsection{结果讨论}\\label{sec:q1-results}"),
        ("\\subsubsection{4.1　基准校核：阿比林八栋园区的资源上限}",
         "\\paragraph{基准校核：阿比林八栋园区的资源上限}\\label{sec:abilene}"),
        ("\\subsubsection{4.2　同址同水额：煤、气、风、光四种方案}",
         "\\paragraph{同址同水额：煤、气、风、光四种方案}\\label{sec:same-site}"),
        ("\\subsubsection{4.3　敏感性与压力测试}",
         "\\paragraph{敏感性与压力测试}\\label{sec:sensitivity}"),
        ("\\subsubsection{4.4　迁移检验：四个全球场址}",
         "\\paragraph{迁移检验：四个全球场址}\\label{sec:migration}"),
    ],
    "03-q2.tex": [
        # 先处理“综合评价”下的三个小标题（带上下文，避免与后面新建的重名）
        ("\\subsubsection{环境足迹}\n\n对于\\textbf{环境足迹}维度", "\\subhead{环境足迹}\n\n对于\\textbf{环境足迹}维度"),
        ("\\subsubsection{资源压力}\n\n对于\\textbf{资源压力}维度", "\\subhead{资源压力}\n\n对于\\textbf{资源压力}维度"),
        ("\\subsubsection{最终评价}", "\\subhead{最终评价}"),
        # 再处理两个“集中式/分布式数据设施”（各出现两次，用后文锚定）
        ("\\subsubsection{集中式数据设施}\n\n\\paragraph{碳足迹}",
         "\\paragraph{集中式数据设施}\\label{sec:q2-cen}\n\n\\subhead{碳足迹}"),
        ("\\subsubsection{分布式数据设施}\n\n达到给定算力需求",
         "\\paragraph{分布式数据设施}\\label{sec:q2-dis}\n\n达到给定算力需求"),
        ("\\subsubsection{集中式数据设施}\n\n\\paragraph{水资源压力}",
         "\\paragraph{集中式数据设施}\\label{sec:q2-p-cen}\n\n\\subhead{水资源压力}"),
        ("\\subsubsection{分布式数据设施}\n\n继承上文",
         "\\paragraph{分布式数据设施}\\label{sec:q2-p-dis}\n\n继承上文"),
        # 五级小标题
        ("\\paragraph{水足迹}", "\\subhead{水足迹}"),
        ("\\paragraph{土地足迹}", "\\subhead{土地足迹}"),
        ("\\paragraph{电资源压力}", "\\subhead{电资源压力}"),
        ("\\paragraph{土地资源压力}", "\\subhead{土地资源压力}"),
        # 上层
        ("\\section{第二问}", "\\subsection{第二问：弹性分布式算力网络的替代效益与边界}\\label{sec:q2}"),
        ("\\subsection{1　分布式算力网络模式}", "\\subsubsection{分布式算力网络模式}\\label{sec:q2-network}"),
        ("\\subsection{2　环境足迹}", "\\subsubsection{环境足迹}\\label{sec:q2-footprint}"),
        ("\\subsection{3　资源压力}", "\\subsubsection{资源压力}\\label{sec:q2-pressure}"),
        ("\\subsection{综合评价}", "\\subsubsection{综合评价}\\label{sec:q2-eval}"),
    ],
    "04-results.tex": [
        ("\\section{结果讨论}", "\\section{结果讨论}\\label{sec:results}"),
        ("\\subsection{分布式算力网络的普惠性}", "\\subsection{分布式算力网络的普惠性}\\label{sec:inclusion}"),
        ("\\section{讨论与推广}", "\\section{讨论与推广}\\label{sec:promotion}"),
        ("\\section{结论}", "\\section{结论}\\label{sec:conclusion}"),
    ],
    "05-appendix.tex": [
        ("\\section{附录}\n\n", ""),
        ("\\subsection{附录 A　光储可靠容量的计算}", "\\section{光储可靠容量的计算}\\label{apx:a}"),
        ("\\subsection{附录 B　水电可持续供电功率的推导}", "\\section{水电可持续供电功率的推导}\\label{apx:b}"),
        ("\\subsection{附录 C　有效用地与土地上限的估计}", "\\section{有效用地与土地上限的估计}\\label{apx:c}"),
        ("\\subsubsection{C.1　识别可建设的连续场址}", "\\subsection{识别可建设的连续场址}\\label{apx:c1}"),
        ("\\subsubsection{C.2　估计每增加 1 MW IT 所需的土地}", "\\subsection{估计每增加 1 MW IT 所需的土地}\\label{apx:c2}"),
        ("\\subsubsection{C.3　发电预留地与配套设施的边界}", "\\subsection{发电预留地与配套设施的边界}\\label{apx:c3}"),
        ("\\subsection{附录 D　WUE特殊情况修正}", "\\section{WUE特殊情况修正}\\label{apx:d}"),
        ("\\subsection{附录 E　水源数据缺失修补}", "\\section{水源数据缺失修补}\\label{apx:e}"),
        ("\\subsubsection{E.1 流域管理部门公开数据}", "\\subsection{流域管理部门公开数据}\\label{apx:e1}"),
        ("\\subsubsection{E.2 区域水资源分配模型}", "\\subsection{区域水资源分配模型}\\label{apx:e2}"),
        ("\\subsubsection{E.3 供水单位可交付水量}", "\\subsection{供水单位可交付水量}\\label{apx:e3}"),
        ("\\subsection{附录 F　实证场址的数据凭据、扩展复算与季节性背景}",
         "\\section{实证场址的数据凭据、扩展复算与季节性背景}\\label{apx:f}"),
        ("\\subsubsection{F.1　阿比林的四个规模数与宗地核查}", "\\subsection{阿比林的四个规模数与宗地核查}\\label{apx:f1}"),
        ("\\subsubsection{F.2　四地工程输入的取值与证据性质}", "\\subsection{四地工程输入的取值与证据性质}\\label{apx:f2}"),
        ("\\subsubsection{F.3　四地风光的季节性与弱光压力复算}", "\\subsection{四地风光的季节性与弱光压力复算}\\label{apx:f3}"),
        ("\\subsubsection{F.4　敏感性与压力测试的复算网格}", "\\subsection{敏感性与压力测试的复算网格}\\label{apx:f4}"),
    ],
}

# ---------------------------------------------------------------- 公式标签（按出现顺序）
EQLABELS = {
    "01-intro.tex": ["eq:p-capacity", "eq:p-max", "eq:p-f", "eq:p-s", "eq:p-omega"],
    "02-q1.tex": [
        "eq:q1-capacity", "eq:q1-pmax", "eq:q1-ptotal", "eq:q1-k", "eq:q1-thermal",
        "eq:q1-wind", "eq:q1-alpha", "eq:q1-pv", "eq:q1-storage", "eq:q1-hydro",
        "eq:q1-pw", "eq:q1-qfield", "eq:q1-qdc", "eq:q1-pressure", "eq:q1-qdcpress",
        "eq:q1-qavail", "eq:q1-qgen", "eq:q1-areq", "eq:q1-pland", "eq:q1-pland-linear",
        "eq:q1-pl",
    ],
    "03-q2.tex": [
        "eq:q2-pit", "eq:q2-facility", "eq:q2-balance", "eq:q2-energy", "eq:q2-carbon",
        "eq:q2-fgrid", "eq:q2-fself", "eq:q2-qfield", "eq:q2-qgen", "eq:q2-wout",
        "eq:q2-areq", "eq:q2-sum-o", "eq:q2-cout", "eq:q2-wout-sum", "eq:q2-aout",
        "eq:q2-rw", "eq:q2-reserve", "eq:q2-re", "eq:q2-ra", "eq:q2-rwmax",
        "eq:q2-remax", "eq:q2-ramax", "eq:q2-findex", "eq:q2-fcen", "eq:q2-phi",
        "eq:q2-phi-prop", "eq:q2-phi-deriv", "eq:q2-examples", "eq:q2-infeasible",
        "eq:q2-sweighted", "eq:q2-final",
    ],
    "05-appendix.tex": [
        "eq:apxA-balance", "eq:apxA-limits", "eq:apxA-f", "eq:apxB-energy", "eq:apxB-power",
        "eq:apxC-site", "eq:apxC-gen", "eq:apxE-reverse",
    ],
}

# ---------------------------------------------------------------- 交叉引用
REFS = [
    # 01-intro: 无
    # 02-q1
    ("02-q1.tex", "用地分配的计算见附录 C。", "用地分配的计算见附录~\\ref{apx:c}。"),
    ("02-q1.tex", "按附录 A 的功率与电量平衡", "按附录~\\ref{apx:a} 的功率与电量平衡"),
    ("02-q1.tex", "请参考附录A", "请参考附录~\\ref{apx:a}"),
    ("02-q1.tex", "式（7）应采用枯水期", "式~\\eqref{eq:q1-hydro} 应采用枯水期"),
    ("02-q1.tex", "推导见附录 B。", "推导见附录~\\ref{apx:b}。"),
    ("02-q1.tex", "补偿方法见附录E。", "补偿方法见附录~\\ref{apx:e}。"),
    ("02-q1.tex", "具体选择规范见附录C.1。", "具体选择规范见附录~\\ref{apx:c1}。"),
    ("02-q1.tex", "由3.2中式子可得", "由式~\\eqref{eq:q1-areq} 可得"),
    ("02-q1.tex", "第 1–3 节分别处理", "第~\\ref{sec:q1-energy}--\\ref{sec:q1-land}~节分别处理"),
    ("02-q1.tex", "（$+3.28\\%$，图 4-1）", "（$+3.28\\%$，图~\\ref{fig:abilene}）"),
    ("02-q1.tex", "见附录 F.1）计算", "见附录~\\ref{apx:f1}）计算"),
    ("02-q1.tex", "与 4.1 节只算运营宗地", "与第~\\ref{sec:abilene}~节只算运营宗地"),
    ("02-q1.tex", "（图 4-2、表 4-1：", "（图~\\ref{fig:sources}、表~\\ref{tab:sources}："),
    ("02-q1.tex", "排列于图 4-3，逐项网格见附录 F.4。", "排列于图~\\ref{fig:sensitivity}，逐项网格见附录~\\ref{apx:f4}。"),
    ("02-q1.tex", "表 4-2 第 5 列比第 4 列", "表~\\ref{tab:four-sites} 第 5 列比第 4 列"),
    ("02-q1.tex", "这与第 2 节的 $S\\le S_{\\max}$ 判据", "这与第~\\ref{sec:q1-water}~节的 $S\\le S_{\\max}$ 判据"),
    # 03-q2
    ("03-q2.tex", "式（2）本身只规定供需平衡", "式~\\eqref{eq:q2-balance} 本身只规定供需平衡"),
    # 05-appendix
    ("05-appendix.tex", "公共电网的持续供电已由式（1）计入", "公共电网的持续供电已由式~\\eqref{eq:q1-ptotal} 计入"),
    ("05-appendix.tex", "式（A2）的电量上下限", "式~\\eqref{eq:apxA-limits} 的电量上下限"),
    ("05-appendix.tex", "存在满足式（A1）、（A2）的全周期运行安排",
     "存在满足式~\\eqref{eq:apxA-balance}、\\eqref{eq:apxA-limits} 的全周期运行安排"),
    ("05-appendix.tex", "可在式（A1）左端加入", "可在式~\\eqref{eq:apxA-balance} 左端加入"),
    ("05-appendix.tex", "将式（B2）换算为 MW", "将式~\\eqref{eq:apxB-power} 换算为 MW"),
    ("05-appendix.tex", "即得正文式（5）", "即得正文式~\\eqref{eq:q1-hydro}"),
    ("05-appendix.tex", "若完整模块才可投运，式（L2）给出连续近似", "若完整模块才可投运，式~\\eqref{eq:q1-areq} 给出连续近似"),
    ("05-appendix.tex", "式（C2）检验发电配置能否建成，式（L1）按整块预留地扣减机房可用面积。",
     "式~\\eqref{eq:apxC-gen} 检验发电配置能否建成，式~\\eqref{eq:q1-areq} 按整块预留地扣减机房可用面积。"),
    ("05-appendix.tex", "正文 4.1–4.2 的比较", "第~\\ref{sec:abilene}--\\ref{sec:same-site}~节的比较"),
    ("05-appendix.tex", "表 F-1 给出五者的边界", "表~\\ref{tab:scales} 给出五者的边界"),
    ("05-appendix.tex", "表 F-2 逐项给出正文 4.4 节所用", "表~\\ref{tab:inputs} 逐项给出第~\\ref{sec:migration}~节所用"),
    ("05-appendix.tex", "正文 4.2 节关于", "第~\\ref{sec:same-site}~节关于"),
    ("05-appendix.tex", "逐月统计见表 F-3，", "逐月统计见表~\\ref{tab:seasons}，"),
    ("05-appendix.tex", "两列均按附录 F.2 的同一组参数计算", "两列均按附录~\\ref{apx:f2} 的同一组参数计算"),
    ("05-appendix.tex", "表 F-3 说明三件事。", "表~\\ref{tab:seasons} 说明三件事。"),
    ("05-appendix.tex", "正文图 4-3 的两列基准", "图~\\ref{fig:sensitivity} 的两列基准"),
    ("05-appendix.tex", "由表 F-4 可以读出三点。", "由表~\\ref{tab:grid} 可以读出三点。"),
    ("05-appendix.tex", "图 F-1 左半给出", "图~\\ref{fig:candidates} 左半给出"),
]

# ---------------------------------------------------------------- 图/表标签重命名
LABELMAP = [
    ("02-q1.tex", "\\label{fig:4-1}", "\\label{fig:abilene}"),
    ("02-q1.tex", "\\label{fig:4-2}", "\\label{fig:sources}"),
    ("02-q1.tex", "\\label{fig:4-3}", "\\label{fig:sensitivity}"),
    ("02-q1.tex", "\\label{fig:4-4}", "\\label{fig:four-sites}"),
    ("02-q1.tex", "\\label{tab:4-1}", "\\label{tab:sources}"),
    ("02-q1.tex", "\\label{tab:4-2}", "\\label{tab:four-sites}"),
    ("05-appendix.tex", "\\label{tab:F-1}", "\\label{tab:scales}"),
    ("05-appendix.tex", "\\label{tab:F-2}", "\\label{tab:inputs}"),
    ("05-appendix.tex", "\\label{tab:F-3}", "\\label{tab:seasons}"),
    ("05-appendix.tex", "\\label{tab:F-4}", "\\label{tab:grid}"),
    ("05-appendix.tex", "\\label{fig:F-1}", "\\label{fig:candidates}"),
]

# ---------------------------------------------------------------- 题注：去掉手写编号
CAPTIONS = [
    ("02-q1.tex", "\\caption{图 4-1　", "\\caption{"),
    ("02-q1.tex", "\\caption{图 4-2　", "\\caption{"),
    ("02-q1.tex", "\\caption{图 4-3　", "\\caption{"),
    ("02-q1.tex", "\\caption{图 4-4　", "\\caption{"),
    ("02-q1.tex", "\\caption{表 4-1　", "\\caption{"),
    ("02-q1.tex", "\\caption{表 4-2　", "\\caption{"),
    ("05-appendix.tex", "\\caption{表 F-1　", "\\caption{"),
    ("05-appendix.tex", "\\caption{表 F-2　", "\\caption{"),
    ("05-appendix.tex", "\\caption{表 F-3　", "\\caption{"),
    ("05-appendix.tex", "\\caption{表 F-4　", "\\caption{"),
    ("05-appendix.tex", "\\caption{图 F-1　", "\\caption{"),
]


def read(name):
    return io.open(os.path.join(SEC, name), encoding="utf-8").read()


def write(name, s):
    io.open(os.path.join(SEC, name), "w", encoding="utf-8", newline="\n").write(s)


def apply_simple(name, rules, what):
    s = read(name)
    bad = []
    for old, new in rules:
        n = s.count(old)
        if n != 1:
            bad.append((what, old[:50], n))
            continue
        s = s.replace(old, new, 1)
    write(name, s)
    for b in bad:
        print("  [MISS] %-16s %s  出现 %d 次: %r" % (name, b[0], b[2], b[1]))


def label_equations(name, labels):
    s = read(name)
    pat = re.compile(r"\\\[(.*?)\\\]|\\begin\{equation\}(.*?)\\end\{equation\}", re.S)
    blocks = list(pat.finditer(s))
    if len(blocks) != len(labels):
        print("  [COUNT] %-16s 公式 %d 个，标签 %d 个" % (name, len(blocks), len(labels)))
    out, last = [], 0
    for i, m in enumerate(blocks):
        body = m.group(1) if m.group(1) is not None else m.group(2)
        body = re.sub(r"\\tag\{[^}]*\}", "", body).strip()
        lab = labels[i] if i < len(labels) else "eq:UNUSED%d" % i
        out.append(s[last:m.start()])
        out.append("\\begin{equation}\\label{%s}\n%s\n\\end{equation}" % (lab, body))
        last = m.end()
    out.append(s[last:])
    write(name, "".join(out))
    print("  [EQ]   %-16s %d 个公式已编号" % (name, len(blocks)))


def main():
    for name in sorted(HEADINGS):
        apply_simple(name, HEADINGS[name], "heading")
        print("  [H]    %-16s 标题处理完" % name)
    for name, labels in EQLABELS.items():
        label_equations(name, labels)
    caps = {}
    for name, old, new in CAPTIONS:
        caps.setdefault(name, []).append((old, new))
    for name, rules in caps.items():
        apply_simple(name, rules, "caption")
        print("  [C]    %-16s 题注处理完" % name)
    refs = {}
    for name, old, new in REFS:
        refs.setdefault(name, []).append((old, new))
    for name, rules in refs.items():
        apply_simple(name, rules, "ref")
        print("  [R]    %-16s 引用处理完" % name)
    lab = {}
    for name, old, new in LABELMAP:
        lab.setdefault(name, []).append((old, new))
    for name, rules in lab.items():
        apply_simple(name, rules, "label")
        print("  [L]    %-16s 图表标签改名完" % name)


if __name__ == "__main__":
    main()
