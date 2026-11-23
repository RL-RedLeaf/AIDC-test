# -*- coding: utf-8 -*-
"""一次性调整图片宽度与表格字号（只改尺寸参数，不动内容）。"""
import io
import re

BASE = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"


def patch(name, pairs):
    p = BASE + "\\" + name
    s = io.open(p, encoding="utf-8").read()
    for old, new, expect in pairs:
        n = s.count(old)
        if n != expect:
            print("[WARN] %s: 期望 %d 处 %r，实际 %d 处" % (name, expect, old, n))
        s = s.replace(old, new)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("[ok] %s" % name)


patch("02-q1.tex", [
    ("width=0.95\\textwidth", "width=0.82\\textwidth", 4),
    ("{\\setlength{\\tabcolsep}{4pt}", "{\\small\\setlength{\\tabcolsep}{4pt}", 1),
])
patch("03-q2.tex", [
    ("width=0.95\\textwidth", "width=0.78\\textwidth", 1),
])
patch("05-appendix.tex", [
    ("width=0.95\\textwidth", "width=0.82\\textwidth", 1),
    ("{\\small\n", "{\\footnotesize\n", 2),
    ("{\\small\\setlength", "{\\footnotesize\\setlength", 2),
])
