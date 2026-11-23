# -*- coding: utf-8 -*-
"""修 GB/T 7714 样式下暴露的几个细节：ref.bib 的弯引号/作者写法、附录段落伸缩。"""
import io
import re

BASE = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex"
BIB = BASE + r"\ref.bib"

s = io.open(BIB, encoding="utf-8").read()
before = s

# 1) 弯引号 → ASCII 撇号（biber 转义后在中文字体里会渲染成 “` s”）
s = s.replace("\u2019", "'").replace("\u2018", "`")

# 2) 全大写作者名改写为 bib 认可的 “姓, 名首字母” 形式（字母不变，仅写法）
s = s.replace("author         = {SIDDIK M A B and SHEHABI A and MARSTON L}",
              "author         = {Siddik, M. A. B. and Shehabi, A. and Marston, L.}")

io.open(BIB, "w", encoding="utf-8", newline="\n").write(s)
print("ref.bib 修改：%d 处弯引号，作者写法 %s" %
      (before.count("\u2019") + before.count("\u2018"),
       "已改" if "Siddik, M. A. B." in s else "未改"))

# 3) 附录 A 第一段（Goiri 那段）加一点伸缩，消掉 0.9pt overfull
APPX = BASE + r"\sections\05-appendix.tex"
a = io.open(APPX, encoding="utf-8").read()
old = "{\\tolerance=4000\\emergencystretch=1.5em"
if old in a:
    a = a.replace(old, "{\\tolerance=4000\\emergencystretch=3em", 1)
    io.open(APPX, "w", encoding="utf-8", newline="\n").write(a)
    print("05-appendix: 段落伸缩已放宽")
else:
    print("05-appendix: 未找到目标段落（可能已被改写）")
