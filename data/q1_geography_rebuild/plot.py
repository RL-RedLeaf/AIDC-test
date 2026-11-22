"""Plot model outputs and export each site's scenario rows."""
import csv
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

folder = Path(__file__).resolve().parent
with (folder / "results.csv").open() as stream:
    rows = list(csv.DictReader(stream))
base = [r for r in rows if r["occupied_fraction"] == "0.5" and not r["site"].endswith("_extension")]
available = {f.name for f in font_manager.fontManager.ttflist}
zh_font = next((f for f in ("Arial Unicode MS", "Noto Sans CJK SC", "PingFang SC") if f in available), None)
if not zh_font:
    raise RuntimeError("Chinese font required")
for r in base:
    site = r["site"]
    with (folder.parent / ("q1_"+site) / "geography_scenarios.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(s for s in rows if s["site"] in (site,site+"_extension"))
for zh in (True, False):
    plt.rcParams.update({"font.family":zh_font if zh else "DejaVu Sans", "pdf.fonttype":42})
    fig, ax = plt.subplots(figsize=(8,3.8),layout="constrained")
    names = ["戈尔登","凯夫拉维克","丹戎吉岭","基利库拉","悉尼西部"] if zh else ["Golden","Keflavík","Tanjong Kling","Quilicura","Huntingwood"]
    for y,r in enumerate(base):
        a,b = [float(r[k]) for k in ("rain_only_IT","sufficient_external_water_IT")]
        ax.plot([a,b],[y,y],color="#b9c5ca",lw=2,zorder=1)
        ax.scatter(b,y,s=96,facecolors="white",edgecolors="#c26c35",linewidth=2,label=("外部水源充足" if zh else "Sufficient external water") if y==0 else None)
        ax.scatter(a,y,s=27,color="#146a78",label=("仅收集屋面降水" if zh else "Roof precipitation only") if y==0 else None)
    ax.set(xscale="log",yticks=range(5),yticklabels=names,xlabel="可持续 IT 负载（MW，对数刻度）" if zh else "Continuous IT load (MW, logarithmic scale)")
    ax.invert_yaxis()
    ax.grid(axis="x",alpha=.25)
    ax.spines[["right","top"]].set_visible(False)
    ax.set_title("单回路可用 300 A 情景下的冷却补水约束" if zh else "Cooling-water constraints with 300 A available on one circuit",loc="left")
    ax.legend(loc="upper center",bbox_to_anchor=(.5,-.20),ncol=2,frameon=False)
    fig.savefig(folder / ("五地供水与容量.pdf" if zh else "water_and_capacity.pdf"))
    plt.close(fig)
