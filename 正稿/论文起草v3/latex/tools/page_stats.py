# -*- coding: utf-8 -*-
"""统计 main.pdf 各部分页数：封面 / 信件 / 目录 / 正文 / 参考文献 / 附录。

页数从 main.toc 的页码算（比在 PDF 文本里找标题可靠，目录页里也会出现同名条目）。
"""
import io
import re
import subprocess

TOC = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\main.toc"
PDF = r"D:\GYH\coding\git\immc-2027\正稿\论文起草v3\latex\main.pdf"


def total_pages():
    out = subprocess.run(["pdfinfo", PDF], capture_output=True)
    m = re.search(r"Pages:\s+(\d+)", out.stdout.decode("utf-8", "ignore"))
    return int(m.group(1))


def main():
    n = total_pages()
    pages = {}
    for line in io.open(TOC, encoding="utf-8"):
        m = re.search(r"\\contentsline \{(section|subsection)\}\{(.*?)\}\{(\d+)\}", line)
        if not m:
            continue
        level, title, page = m.group(1), m.group(2), int(m.group(3))
        # 自动编号后 toc 里是 “\numberline {1}问题重述”
        title = re.sub(r"\\numberline\s*\{[^}]*\}", "", title)
        title = re.sub(r"\\[A-Za-z]+\s*", "", title)
        title = title.replace("{", "").replace("}", "").strip()
        if level != "section" or title in pages:
            continue
        pages[title] = page

    order = ["致 WAICO 的一封信", "问题重述", "模型的建立与求解", "结果讨论", "参考文献", "光储可靠容量的计算"]
    print("总页数：%d" % n)
    for k in order:
        if k in pages:
            print("  %-16s 起始页（印刷页码）%d" % (k, pages[k]))

    intro = pages.get("问题重述")
    refs = pages.get("参考文献")
    appx = pages.get("光储可靠容量的计算")
    if intro and refs:
        body = refs - intro
        print("\n正文（引言→结论）＝ %d 页   %s" % (body, "✅ ≤20" if body <= 20 else "❌ >20"))
        print("  其中 问题重述→模型 %d 页，模型→结果讨论 %d 页，空章节 %d 页"
              % (pages.get("模型的建立与求解", intro) - intro,
                 pages.get("结果讨论", refs) - pages.get("模型的建立与求解", intro),
                 refs - pages.get("结果讨论", refs)))
    if refs and appx:
        print("参考文献 ＝ %d 页；附录 ＝ %d 页" % (appx - refs, n - appx + 1))
    if intro:
        print("正文之前（封面＋信件＋目录）＝ %d 页；总计 %d 页" % (intro - 1, n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

