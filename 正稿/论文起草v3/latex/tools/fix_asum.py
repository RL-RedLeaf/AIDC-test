# -*- coding: utf-8 -*-
"""结构重构（第二步）：把假设块改成自动编号的 asum 环境，定义/注记块改成 noteblock。"""
import io
import os
import re

SEC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\sections"

# 按出现顺序分配标签（与正文引用对应）
LABELS = ["asum:fixed", "asum:normal", "asum:facility", "asum:gas", "asum:water-ideal",
          "asum:river", "asum:static", "asum:boundary", "asum:sustainable", "asum:homogeneous",
          "asum:node", "asum:no-overlap", "asum:no-decay", "asum:no-cross"]

BLOCK = re.compile(r"\\begin\{asum\}(.*?)\\end\{asum\}", re.S)
START = re.compile(r"(?:^|\n)((?:\\textbf\{)?假设\s*[0-9]*\s*)")
SEP = re.compile(r"[:：]|——")
NOTES_TITLE = re.compile(r"^\\textbf\{([^}]*)\}")


def strip_bold_wrapper(s):
    """去掉把整段假设包起来的 \\textbf{...}，返回（内容, 剩余）。"""
    if s.startswith("\\textbf{"):
        depth, i = 0, len("\\textbf{")
        while i < len(s):
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                if depth == 0:
                    return s[len("\\textbf{"):i], s[i + 1:]
                depth -= 1
            i += 1
    return None, s


def convert(path, labels_left):
    s = io.open(path, encoding="utf-8").read()
    out, last = [], 0
    for m in BLOCK.finditer(s):
        body = m.group(1)
        pos = [x.start(1) for x in START.finditer(body)]
        out.append(s[last:m.start()])
        if not pos:
            # 定义 / 注记
            out.append("\\begin{noteblock}%s\\end{noteblock}" % body)
            last = m.end()
            continue
        chunks = []
        for i, p in enumerate(pos):
            end = pos[i + 1] if i + 1 < len(pos) else len(body)
            chunks.append(body[p:end])
        pieces = []
        if pos[0] > 0:
            pieces.append("\\begin{noteblock}%s\\end{noteblock}" % body[:pos[0]].strip())
        for ch in chunks:
            ch = ch.strip()
            assert labels_left, "标签用完了：%r" % ch[:40]
            label = labels_left.pop(0)
            inner, rest = strip_bold_wrapper(ch)
            if inner is not None:
                lead, tail = inner, rest
            else:
                m2 = re.match(r"假设\s*[0-9]*\s*(.*)$", ch, re.S)
                lead, tail = "", m2.group(1)
            lead = re.sub(r"^假设\s*[0-9]*\s*", "", lead)
            title, text = "", tail.lstrip()
            if lead:
                text = lead + tail
            text = text.lstrip()
            ms = SEP.search(text[:40])
            if ms and ms.start() <= 24:
                title = text[:ms.start()].strip().strip("“”").strip()
                text = text[ms.end():].lstrip()
                text = text.lstrip("—").lstrip("：:").lstrip()
            text = text.strip()
            if title:
                pieces.append("\\begin{asum}[%s]\\label{%s}\n%s\n\\end{asum}" % (title, label, text))
            else:
                pieces.append("\\begin{asum}\\label{%s}\n%s\n\\end{asum}" % (label, text))
        out.append("\n\n".join(pieces))
        last = m.end()
    out.append(s[last:])
    io.open(path, "w", encoding="utf-8", newline="\n").write("".join(out))
    return s.count("\\begin{asum}")


def main():
    left = list(LABELS)
    for name in ["02-q1.tex", "03-q2.tex"]:
        n = convert(os.path.join(SEC, name), left)
        print("%-14s 处理 %d 个块，剩余标签 %d" % (name, n, len(left)))
    if left:
        print("!! 未使用标签:", left)


if __name__ == "__main__":
    main()
