"""Compare site engineering cases with separately specified public benchmarks."""
import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
DATA = HERE.parent
# Benchmarks are read only after computing the forward engineering scenarios.
REFERENCES = {
    "us_golden": (10, "IT", "NREL full build-out", "戈尔登"),
    "is_keflavik_extension": (120, "IT", "HMS VDC04 phases 1–3", "凯夫拉维克扩建"),
    "sg_tanjongkling": (150, "facility", "Cushman & Wakefield 2021 market survey", "丹戎吉岭"),
    "cl_quilicura": (65, "facility", "CEN Data Luna 2025 demand assumption", "基利库拉"),
    "au_huntingwood": (320, "IT minimum", "AirTrunk SYD3 nine phases (2021)", "悉尼西部"),
}


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compare(site, row):
    # Use the Q1 dispatch result, evaluated on the 2025 hourly resource series.
    pv = float(row["roof_PV_firm_MW"])
    k, wue, v, floor = [float(row[key]) for key in
                         ("k", "wue", "voltage_kV", "white_space_m2")]
    rack_limit = math.floor(floor / 6) * 0.1
    unit = math.sqrt(3) * v * .95 / 1000  # Facility MW per net A
    scenarios = []
    for current in [120, 300, 600]:
        energy_limit = (current * unit + pv) / k
        it = min(energy_limit, rack_limit)
        scenarios.append(dict(site=site, net_A=current, energy_limit_IT=energy_limit,
            layout_limit_IT=rack_limit, conditional_IT=it, normal_water_required_m3_h=it*wue,
            first_limit_if_water_adequate="electricity" if energy_limit < rack_limit else "layout"))
    public, basis, source, name = REFERENCES[site]
    target = public/k if basis == "facility" else public
    base = scenarios[1]["conditional_IT"]
    summary = dict(site=site, name=name, benchmark_source=source, public_MW=public,
        public_basis=basis, comparison_IT=target, conditional_IT_at300A=base,
        difference_IT=base-target, difference_pct=100*(base/target-1),
        facility_MW_needed=k*target, net_A_needed=(k*target-pv)/unit,
        white_space_needed_m2=math.ceil(target/.1-1e-9)*6,
        assumed_white_space_m2=floor, normal_water_needed_m3_h=target*wue,
        normal_water_needed_at300A_m3_h=base*wue)
    assert math.isclose((summary["net_A_needed"]*unit+pv)/k, target)
    assert all(a["conditional_IT"] <= b["conditional_IT"] for a,b in zip(scenarios,scenarios[1:]))
    return summary, scenarios


def plot(rows, zh):
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    if zh:
        plt.rcParams["font.family"] = next(x for x in
            ["Arial Unicode MS","Noto Sans CJK SC","PingFang SC"] if x in fonts)
    else:
        plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["pdf.fonttype"] = 42
    fig, ax = plt.subplots(figsize=(8.4,4.6),layout="constrained")
    labels = ([r["name"] for r in rows] if zh else
              ["Golden","Keflavík expansion","Tanjong Kling","Quilicura","Huntingwood"])
    for i,r in enumerate(rows):
        x,y=r["conditional_IT_at300A"],r["comparison_IT"]
        ax.plot([x,y],[i,i],color="#bac9ca")
        ax.scatter(x,i,color="#14716f",s=47,label=("300 A 情景" if zh else "300 A scenario") if i==0 else None)
        ax.scatter(y,i,facecolor="white",edgecolor="#ae521f",s=63,linewidth=2,
                   label=("公开参照*" if zh else "Public benchmark*") if i==0 else None)
        ax.annotate(f"{x:.1f}",(x,i),xytext=(0,8),textcoords="offset points",ha="center",fontsize=9)
        ax.annotate(f"{y:.1f}"+("+" if i==4 else ""),(y,i),xytext=(4,-13),textcoords="offset points",fontsize=9)
    ax.set(yscale="linear",xscale="log",xlim=(4,500),ylim=(4.55,-.65),yticks=range(5),yticklabels=labels,
           xlabel="IT 负载（MW，对数刻度）" if zh else "IT load (MW, log scale)")
    ax.set_title("正常供水充足时的模型容量与同址公开规模" if zh else "Site capacity with adequate utility water vs. public benchmark",loc="left")
    ax.legend(frameon=False,loc="upper right")
    ax.grid(axis="x",alpha=.2)
    ax.spines[["top","right"]].set_visible(False)
    fig.text(.01,.005,("* 新加坡为市场调查；智利为电网需求预测。两者由设施功率折算。悉尼取公布下限。" if zh else
        "* Singapore: market survey. Chile: grid forecast. Both converted from facility MW. Sydney: published minimum."),fontsize=8)
    fig.savefig(HERE/("五地规划对照.pdf" if zh else "five_site_benchmarks.pdf"),bbox_inches="tight",pad_inches=.2)
    plt.close(fig)


if __name__ == "__main__":
    with (DATA/"q1_geography_rebuild/results.csv").open() as f:
        inputs = {r["site"]:r for r in csv.DictReader(f) if float(r["occupied_fraction"]) == .5}
    summaries = []
    for site in REFERENCES:
        summary, scenarios = compare(site, inputs[site])
        summaries.append(summary)
        folder = DATA/("q1_"+site.removesuffix("_extension"))
        write_rows(folder/"plan_comparison.csv",[summary])
        write_rows(folder/"normal_supply_scenarios.csv", scenarios)
    write_rows(HERE/"comparison.csv", summaries)
    for zh in (True,False):
        plot(summaries,zh)
