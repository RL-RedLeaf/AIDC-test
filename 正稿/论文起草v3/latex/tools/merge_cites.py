# -*- coding: utf-8 -*-
"""把相邻的多个 \\cite 合并成一个，让 GB/T 7714 样式能压成 [13-20] 这种区间形式。"""
import io
import os
import re

SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"
PAIR = re.compile(r"\\cite\{([^{}]*)\}\s*\\cite\{([^{}]*)\}")

for name in sorted(os.listdir(SEC)):
    if not name.endswith(".tex"):
        continue
    p = os.path.join(SEC, name)
    s = io.open(p, encoding="utf-8").read()
    total = 0
    while True:
        new, n = PAIR.subn(lambda m: "\\cite{%s,%s}" % (m.group(1), m.group(2)), s)
        if n == 0:
            break
        total += n
        s = new
    if total:
        io.open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("%-18s 合并 %d 处" % (name, total))
