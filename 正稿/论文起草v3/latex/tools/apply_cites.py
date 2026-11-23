# -*- coding: utf-8 -*-
"""把 \citemark{原标记} 按上下文替换成 \cite{键}。

原稿的文献编号有三套重叠命名空间（第一问 1-6 / 第一问水 1-10 / 4-x / L1-L5 /
第二问 1,1,2），同一个数字在不同段落指向不同文献，所以只能按上下文定，
不能全局替换。这里用“锚点文本 + 原标记”的精确串替换，逐条校验。
"""
import io
import re
import sys

BASE = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

# 文件 -> [(锚点+标记原文, 替换结果)]
JOBS = {
    "02-q1.tex": [
        ("分项计量的口径\\citemark{1}", "分项计量的口径\\cite{q1ref01}"),
        ("能够维持的净功率\\citemark{2}", "能够维持的净功率\\cite{q1ref02}"),
        ("决定各时段的出力\\citemark{3}", "决定各时段的出力\\cite{q1ref03}"),
        ("协调光伏和电池运行\\citemark{4}", "协调光伏和电池运行\\cite{q1ref04}"),
        ("估算可持续供电功率\\citemark{6}", "估算可持续供电功率\\cite{q1ref06}"),
        ("具体见附录D。\\citemark{4}", "具体见附录D。\\cite{q1bref04}"),
        ("将其忽略不计。\\citemark{9}", "将其忽略不计。\\cite{q1bref09}"),
        ("资源竞争越大。\\citemark{1}", "资源竞争越大。\\cite{q1bref01}"),
        ("可用可再生水资源之比”。\\citemark{1}", "可用可再生水资源之比”。\\cite{q1bref01}"),
        ("是因为新增取水不能为负。\\citemark{2}\\citemark{3}\\citemark{8}",
         "是因为新增取水不能为负。\\cite{q1bref02,q1bref03,q1bref08}"),
        ("计入同一场址的水量预算 \\citemark{10}", "计入同一场址的水量预算~\\cite{q1bref10}"),
    ],
    "03-q2.tex": [
        ("SETI@home项目\\citemark{1}", "SETI@home项目\\cite{q2cref01}"),
        ("众多因素\\citemark{2}\\citemark{3}", "众多因素\\cite{q2cref03,q2cref02}"),
        ("更在于对土地和水资源的占用\\citemark{1}", "更在于对土地和水资源的占用\\cite{q2ref01}"),
        # 原稿“碳足迹参考文献”列出了这两条部委公告，但正文没有标引用标记；
        # 在该数值与发布时点的出处处补上引用（文字未改，可随时删掉这处 \cite）。
        ("数据发布于 2025 年 12 月 31 日。",
         "数据发布于 2025 年 12 月 31 日\\cite{q2bref01,q2bref02}。"),
    ],
    "05-appendix.tex": [
        # 原稿把 Goiri 写成 [7]，但内容与 §5.2 原式（6）–（13）都指向 q1ref04（Goiri, Parasol/GreenSwitch）
        ("追踪电池剩余电量 \\citemark{7, §5.2，原式（6）–（13）}",
         "追踪电池剩余电量 \\cite[§5.2，原式（6）–（13）]{q1ref04}"),
        # 原稿 [5] 指“装机与同期气象条件转换为可用光伏净功率”，语义对应 PyPSA-Earth（atlite 气象转出力）
        ("由装机与同期气象条件转换得到 \\citemark{5}", "由装机与同期气象条件转换得到~\\cite{q1ref03}"),
        ("的水力功率推导\\citemark{6}", "的水力功率推导\\cite{q1ref06}"),
        ("需要避让的区域 \\citemark{L1}", "需要避让的区域~\\cite{apxrefL01}"),
        ("并追溯原始披露 \\citemark{L2}", "并追溯原始披露~\\cite{apxrefL02}"),
        ("能否合法且实际用于机房建设 \\citemark{L3–L5}", "能否合法且实际用于机房建设~\\cite{apxrefL03,apxrefL04,apxrefL05}"),
        ("相应用地口径下的装机密度估算可建规模 \\citemark{L4, L5}", "相应用地口径下的装机密度估算可建规模~\\cite{apxrefL04,apxrefL05}"),
        ("可直接将其作为 $Q_{\\text{可用}}$ 的取值依据。\\citemark{2}\\citemark{3}\\citemark{8}\\citemark{9}",
         "可直接将其作为 $Q_{\\text{可用}}$ 的取值依据。\\cite{q1bref02,q1bref03,q1bref08,q1bref09}"),
        # E.2 的 [11] 原稿文献表里没有：正文点名 StateMod，对应 q1bref10
        ("科罗拉多州的 StateMod 模型等。\\citemark{6}\\citemark{11}",
         "科罗拉多州的 StateMod 模型等。\\cite{q1bref06,q1bref10}"),
    ],
}


def main():
    only = sys.argv[1:] or list(JOBS)
    rc = 0
    for fname in only:
        path = BASE + "\\" + fname
        s = io.open(path, encoding="utf-8").read()
        miss = []
        for old, new in JOBS[fname]:
            if old in s:
                s = s.replace(old, new, 1)
            else:
                miss.append(old)
        # 4-N 系列：统一映射到 apxrefNN（附录/结果讨论的 4-1…4-29）
        s, n4 = re.subn(r"\\citemark\{4-(\d+)\}", lambda m: "\\cite{apxref%02d}" % int(m.group(1)), s)
        io.open(path, "w", encoding="utf-8", newline="\n").write(s)
        left = len(re.findall(r"\\citemark", s))
        print("%s: 4-x -> %d 条, 未匹配锚点 %d 条, 剩余 \\citemark %d 处" % (fname, n4, len(miss), left))
        for m in miss:
            print("   MISS:", m)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
