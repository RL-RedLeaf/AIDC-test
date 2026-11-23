# -*- coding: utf-8 -*-
"""数值保真校验：把 markdown 源与 LaTeX 片段里的数字 token 各取一份多重集比对。

用来发现“手抄数字抄错”这类错误（1,266.15 → 1,266.15 而不是 1266.5）。
"""
import io
import os
import re
import sys
from collections import Counter

MD = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v2\论文起草.md"
SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

JOBS = [("01-intro.tex", 9, 78), ("02-q1.tex", 79, 478),
        ("03-q2.tex", 479, 859), ("04-results.tex", 860, 871),
        ("05-appendix.tex", 1022, 1300)]

# 数字 token：至少一位数字，可带小数、千分位逗号、百分号
TOK = re.compile(r"\d[\d,]*(?:\.\d+)?%?")


def tokens(s):
    out = []
    for m in TOK.finditer(s):
        t = m.group(0).replace(",", "")
        out.append(t)
    return Counter(out)


def strip_latex(s):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\tag\{\s*(\w+)\s*\}", r" TAG\1 ", s)   # 公式标签单独处理
    s = re.sub(r"\\cite[a-z]*(\[[^\]]*\])?\{[^}]*\}", " ", s)  # 引用键里的数字不算
    s = re.sub(r"\\label\{[^}]*\}", " ", s)
    s = re.sub(r"\\(includegraphics|input|addbibresource)(\[[^\]]*\])?\{[^}]*\}", " ", s)
    # 排版参数（列宽、间距、可选参数）里的数字不是正文数值
    s = re.sub(r"\\begin\{longtable\}\{[^\n]*\}", " ", s)
    s = re.sub(r"\\begin\{tabular[x*]?\}\{[^\n]*\}", " ", s)
    s = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", " ", s)
    s = re.sub(r"\\(begin|end)\{[a-zA-Z*]+\}(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\[A-Za-z]+\*?(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\[^A-Za-z]", " ", s)
    return s.replace("{", "").replace("}", "").replace("$", "")


def strip_md(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)          # 图片（文件名里有 4-1）
    s = re.sub(r"\]\([^)]*\)", "]", s)                   # 链接地址
    s = re.sub(r"\\\[([0-9L][^\]]*)\\\]", " ", s)        # 引用标记 [1] [4-1] [L1]
    s = re.sub(r"\\tag\{\s*(\w+)\s*\}", r" TAG\1 ", s)
    s = s.replace("{,}", "")                             # 千分位写法归一
    s = s.replace("\\.", ".").replace("\\-", "-")        # markdown 转义去反斜杠
    return s


def main():
    md = io.open(MD, encoding="utf-8").read().split("\n")
    rc = 0
    for name, lo, hi in JOBS:
        p = os.path.join(SEC, name)
        if not os.path.exists(p):
            continue
        a = tokens(strip_md("\n".join(md[lo - 1:hi])))
        b = tokens(strip_latex(io.open(p, encoding="utf-8").read()))
        only_md = a - b
        only_tex = b - a
        if not only_md and not only_tex:
            print("[OK]   %-16s %d 个数字 token 完全一致" % (name, sum(a.values())))
            continue
        rc = 1
        print("[DIFF] %-16s md %d 个 / tex %d 个" % (name, sum(a.values()), sum(b.values())))
        for k, v in sorted(only_md.items()):
            print("   只在 md : %-12s x%d" % (k, v))
        for k, v in sorted(only_tex.items()):
            print("   只在 tex: %-12s x%d" % (k, v))
    return rc


if __name__ == "__main__":
    sys.exit(main())
