# -*- coding: utf-8 -*-
"""只比汉字（U+4E00-9FFF）：忽略标点差异，定位真正的内容差异。"""
import io
import os
import re
import difflib
import sys

MD = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v2\论文起草.md"
SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

JOBS = [("01-intro.tex", 9, 78), ("02-q1.tex", 79, 478),
        ("03-q2.tex", 479, 859), ("05-appendix.tex", 1022, 1300),
        ("04-results.tex", 860, 871)]


def ideo(s):
    return "".join(c for c in s if 0x4E00 <= ord(c) <= 0x9FFF)


def strip_latex(s):
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\[A-Za-z]+\*?", "", s)
    s = re.sub(r"\\[^A-Za-z]", "", s)
    return s.replace("$", "").replace("{", "").replace("}", "")


def strip_md(s):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)


def main():
    md = io.open(MD, encoding="utf-8").read().split("\n")
    for name, lo, hi in JOBS:
        p = os.path.join(SEC, name)
        if not os.path.exists(p):
            print("[skip]", name)
            continue
        a = ideo(strip_md("\n".join(md[lo - 1:hi])))
        b = ideo(strip_latex(io.open(p, encoding="utf-8").read()))
        if a == b:
            print("[OK]   %-16s %d 汉字一致" % (name, len(a)))
            continue
        print("[DIFF] %-16s md=%d tex=%d" % (name, len(a), len(b)))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        shown = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            print("   %-7s md[%d:%d]=%r  tex[%d:%d]=%r  @%s" %
                  (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2], a[max(0, i1 - 12):i1]))
            shown += 1
            if shown >= 15:
                print("   ... 更多差异略")
                break


if __name__ == "__main__":
    main()
