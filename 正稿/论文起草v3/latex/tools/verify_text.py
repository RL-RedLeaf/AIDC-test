# -*- coding: utf-8 -*-
"""正文保真度校验：把 markdown 源与 LaTeX 片段都压成“汉字＋全角标点”序列后逐字比对。

目的：证明转换过程中一个字都没丢、没加、没改顺序（只允许 ASCII/公式/标记层面的差异）。
"""
import io
import re
import sys
import unicodedata

MD = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v2\论文起草.md"
SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

RANGES = [
    (0x4E00, 0x9FFF),   # CJK 统一汉字
    (0x3400, 0x4DBF),   # 扩展 A
    (0x3001, 0x303F),   # CJK 标点（不含 U+3000 全角空格：编号与标题间的空格属排版归一）
    (0xFF00, 0xFFEF),   # 全角形式
]
EXTRA = set("—–‘’“”…·％℃")


def keep(ch):
    o = ord(ch)
    if ch in EXTRA:
        return True
    return any(a <= o <= b for a, b in RANGES)


def seq(text):
    return "".join(c for c in text if keep(c))


def strip_latex(s):
    s = re.sub(r"(?<!\\)%.*", "", s)              # 注释
    s = re.sub(r"\\[A-Za-z]+\*?", "", s)          # 命令名
    s = re.sub(r"\\[^A-Za-z]", "", s)             # 转义符号（\% 等）
    s = s.replace("$", "").replace("{", "").replace("}", "").replace("\u3000", "")
    return s


def strip_md(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)    # 图片
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # 链接保留文字
    return s


JOBS = [
    ("01-intro.tex", 79 - 70, 9, 78),
    ("02-q1.tex", None, 79, 478),
    ("03-q2.tex", None, 479, 859),
    ("05-appendix.tex", None, 1022, 1300),
]


def main():
    md_lines = io.open(MD, encoding="utf-8").read().split("\n")
    rc = 0
    for name, _skip, lo, hi in JOBS:
        import os
        path = os.path.join(SEC, name)
        if not os.path.exists(path):
            print("[skip] %s 不存在" % name)
            continue
        md_txt = strip_md("\n".join(md_lines[lo - 1:hi]))
        tex_txt = strip_latex(io.open(path, encoding="utf-8").read())
        a, b = seq(md_txt), seq(tex_txt)
        if a == b:
            print("[OK]   %-16s %d 字完全一致" % (name, len(a)))
            continue
        rc = 1
        i = 0
        while i < min(len(a), len(b)) and a[i] == b[i]:
            i += 1
        print("[DIFF] %-16s md=%d tex=%d 首个差异位置 %d" % (name, len(a), len(b), i))
        print("   md : ...%s..." % a[max(0, i - 30):i + 30].replace("\n", "⏎"))
        print("   tex: ...%s..." % b[max(0, i - 30):i + 30].replace("\n", "⏎"))
    return rc


if __name__ == "__main__":
    sys.exit(main())

