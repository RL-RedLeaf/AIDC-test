import io, os, re, sys
sys.path.insert(0, r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\tools")
import verify_numbers as V
from collections import Counter

def key(t):
    t2 = t.rstrip("%")
    try:
        v = float(t2)
    except ValueError:
        return None
    has_dot = "." in t2
    if has_dot and len(t2.replace(".", "")) >= 4:
        return t2
    if (not has_dot) and v >= 100:
        return t2
    return None

md = io.open(V.MD, encoding="utf-8").read().split("\n")
for name, lo, hi in V.JOBS:
    p = os.path.join(V.SEC, name)
    if not os.path.exists(p):
        continue
    def big(c):
        out = Counter()
        for t, n in c.items():
            k = key(t)
            if k:
                out[k] += n
        return out
    a = big(V.tokens(V.strip_md("\n".join(md[lo-1:hi]))))
    b = big(V.tokens(V.strip_latex(io.open(p, encoding="utf-8").read())))
    only_a, only_b = a - b, b - a
    if not only_a and not only_b:
        print("[OK]   %-16s %d 个关键数值（>=100 或 4 位以上小数）完全一致" % (name, sum(a.values())))
        continue
    print("[DIFF] %-16s md %d / tex %d" % (name, sum(a.values()), sum(b.values())))
    for k, v in sorted(only_a.items()):
        print("   只在 md : %-12s x%d" % (k, v))
    for k, v in sorted(only_b.items()):
        print("   只在 tex: %-12s x%d" % (k, v))
