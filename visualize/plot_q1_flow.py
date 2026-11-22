"""Export the Q1 method overview in both paper languages."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent
INK, MUTED, RULE = "#24313B", "#64717A", "#C9D3D6"
POWER, WATER, LAND, JOINT = "#396D9D", "#168B81", "#CA7D35", "#2D3038"


def draw(chinese):
    def label(english, mandarin):
        return mandarin if chinese else english

    plt.rcParams.update({
        "font.family": label("Arial", "Microsoft YaHei"),
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
    })
    width, height = 7.25, 4.16
    fig = plt.figure(figsize=(width, height), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, width), ylim=(height, 0))
    ax.set_axis_off()

    def text(x, y, value, size, color=INK, weight="normal"):
        ax.text(x, y, value, ha="center", va="center", fontsize=size,
                color=color, fontweight=weight, linespacing=1.35)

    def line(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color=MUTED, lw=0.8,
                solid_capstyle="round", zorder=0)

    def arrow(x, y1, y2):
        ax.add_patch(FancyArrowPatch((x, y1), (x, y2), arrowstyle="-|>",
                                     color=MUTED, linewidth=0.8, mutation_scale=8,
                                     shrinkA=0, shrinkB=0, zorder=0))

    def box(x, y, w, h, fill, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.055",
                                    facecolor=fill, edgecolor=edge, linewidth=0.75))

    mid = width / 2
    box(1.43, 0.055, width - 2 * 1.43, 0.60, "#F6F8F8", RULE)
    text(mid, 0.235, label("Assess each commissioned option at the site",
                           "逐一评估该场址在评估年已投运的方案"), 11, weight="bold")
    text(mid, 0.48, label("Normal operation under the same design conditions",
                          "同一设计工况下，园区正常运行"), 9, MUTED)

    centers = [1.25, mid, width - 1.25]
    line(mid, 0.655, mid, 0.79)
    line(centers[0], 0.79, centers[-1], 0.79)
    for x in centers:
        arrow(x, 0.79, 0.97)

    rows = [
        (POWER, "#F3F7FA", label("Energy", "能源约束"),
         label("Combine firm grid supply\nand on-site generation.\nAllow for cooling and power losses.",
               "合并电网与自建电源的持续供电\n扣除满载冷却用电与配电损耗"),
         label("Power-limited IT capacity", "电力可支撑的 IT 容量")),
        (WATER, "#F1F8F7", label("Water", "水资源约束"),
         label("Limit supply by source, local stress\nand permits where applicable.\nAllow for generation and cooling.",
               "按水源、适用的水压力与许可限额\n确定可用水量，扣除自发电用水\n按冷却用水强度换算容量"),
         label("Water-limited IT capacity", "水资源可支撑的 IT 容量")),
        (LAND, "#FCF7F1", label("Land", "土地约束"),
         label("Identify buildable land.\nReserve land for fixed facilities\nand on-site generation.",
               "筛选符合规划和生态要求的地块\n扣除固定设施与自建电源用地\n按机房用地强度换算容量"),
         label("Land-limited IT capacity", "土地可支撑的 IT 容量")),
    ]
    card_width = 2.20
    for x, (color, fill, title, detail, output) in zip(centers, rows):
        box(x - card_width / 2, 0.97, card_width, 1.36, fill, color)
        text(x, 1.18, title, 12, color, "bold")
        text(x, 1.67, detail, 8.6)
        text(x, 2.15, output, 9.3, color, "bold")
        line(x, 2.33, x, 2.49)
    line(centers[0], 2.49, centers[-1], 2.49)
    arrow(mid, 2.49, 2.67)
    box(1.42, 2.67, width - 2.84, 0.58, "#FFFFFF", MUTED)
    text(mid, 2.86, label("Sustainable capacity of each option",
                          "每套方案的可持续规模"), 10.8, weight="bold")
    text(mid, 3.09, label("Take the lowest of its three IT capacity limits",
                          "取电、水、土地三项 IT 容量上限中的最低值"), 9, MUTED)
    arrow(mid, 3.25, 3.46)
    box(1.15, 3.46, width - 2.30, 0.61, JOINT, JOINT)
    text(mid, 3.65, label("Maximum sustainable IT capacity at the site", "场址最大可持续规模（MW IT）"),
         12, "white", "bold")
    text(mid, 3.90, label("Select the highest feasible capacity (MW IT) and identify its bottleneck",
                          "比较可行方案，选取容量最高者并识别其限制资源"), 8.8, "#EEF2F3")

    stem = "fig07_q1_overview" + ("_zh" if chinese else "")
    for ext in ("pdf", "svg", "png"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    for chinese_version in (False, True):
        draw(chinese_version)
