# -*- coding: utf-8 -*-
"""清掉拆分假设时产生的空 noteblock。"""
import io
import os
import re

SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"
EMPTY = re.compile(r"\\begin\{noteblock\}\s*\\end\{noteblock\}\n?")

for name in ("02-q1.tex", "03-q2.tex"):
    p = os.path.join(SEC, name)
    s = io.open(p, encoding="utf-8").read()
    before = s.count("\\begin{noteblock}")
    s, n = EMPTY.subn("", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("%-14s noteblock %d -> %d（删除空块 %d）" % (name, before, s.count("\\begin{noteblock}"), n))
