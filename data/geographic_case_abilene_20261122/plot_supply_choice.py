"""Q1 supply-choice figure over an on-site generation land budget."""

import csv
import json
import sys
from copy import deepcopy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml


CASE = Path(__file__).resolve().parent
OUT = CASE / "outputs"
ROOT = CASE.parents[1]
sys.path.insert(0, str(ROOT / "code"))
from immc_power_capacity.core import assess_site  # noqa: E402


COLORS = {
    "电网": "#586571",
    "燃煤": "#977260",
    "燃气": "#3479ad",
    "风储": "#259a82",
    "光储": "#d69a30",
    "最优": "#8051a0",
}
TECH = ["燃煤", "燃气", "风储", "光储"]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def candidate_row(data, spec):
    trial = deepcopy(data)
    trial["scenarios"] = [spec]
    return assess_site(trial)["scenarios"][0]


def main():
    base = yaml.safe_load((OUT / "01_q1_inputs.yaml").read_text(encoding="utf-8"))
    available = base.pop("scenarios")
    assert base["P_grid_mw"] == 100.0 and base["k_factor"] == 1.41
    grid_spec = next(item for item in available if item["type"] == "grid")
    pv_template = next(item for item in available if item["type"] == "solar")
    wind_template = next(item for item in available if item["type"] == "combined_battery")
    thermal = {
        "燃气": sorted((item for item in available if item["type"] == "gas"),
                     key=lambda item: item["generation_land_ha"]),
        "燃煤": sorted((item for item in available if item["type"] == "coal"),
                     key=lambda item: item["generation_land_ha"]),
    }
    with (OUT / "04_design_day_weather_to_PV.csv").open(encoding="utf-8-sig", newline="") as handle:
        profile = list(csv.DictReader(handle))
    wind_ratios = [float(row["wind_turbine_power_ratio_assumed"]) for row in profile]
    pv_density = pv_template["density_mw_per_km2"]
    wind_ha_per_mw = 30.0
    budgets = sorted({round(i * 0.5, 1) for i in range(91)} |
                     {float(i) for i in range(50, 441, 10)})
    grid_result = candidate_row(base, grid_spec)
    best_pv = None
    best_wind = None
    thermal_rows = {name: [candidate_row(base, spec) for spec in specs]
                    for name, specs in thermal.items()}
    rows = []

    for budget in budgets:
        if budget > 0:
            pv = deepcopy(pv_template)
            pv["name"] = f"光储，实际发电用地 {budget:.1f} ha"
            pv["area_km2"] = budget / 100
            pv["generation_land_ha"] = budget
            pv_mw = pv["area_km2"] * pv_density
            pv["battery"]["C_max_mw"] = pv_mw / 4
            pv["battery"]["D_max_mw"] = pv_mw / 4
            pv["battery"]["E_usable_mwh"] = pv_mw
            pv_result = candidate_row(base, pv)
            if best_pv is None or pv_result["P_mw_it"] > best_pv["P_mw_it"]:
                best_pv = pv_result

            wind = deepcopy(wind_template)
            wind["name"] = f"风储，实际发电用地 {budget:.1f} ha"
            wind["generation_land_ha"] = budget
            wind["generation_land_required_ha"] = budget
            wind["installed_mw"] = budget / wind_ha_per_mw
            wind["supply_series_mw"] = [wind["installed_mw"] * ratio for ratio in wind_ratios]
            wind["battery"]["C_max_mw"] = wind["installed_mw"] / 4
            wind["battery"]["D_max_mw"] = wind["installed_mw"] / 4
            wind["battery"]["E_usable_mwh"] = wind["installed_mw"]
            wind_result = candidate_row(base, wind)
            if best_wind is None or wind_result["P_mw_it"] > best_wind["P_mw_it"]:
                best_wind = wind_result

        candidates = {"电网": grid_result}
        if best_pv is not None:
            candidates["光储"] = best_pv
            candidates["风储"] = best_wind
        for name, options in thermal_rows.items():
            feasible = [item for item in options if item["generation_land_ha"] <= budget]
            if feasible:
                candidates[name] = max(feasible, key=lambda item: item["P_mw_it"])

        winner_name = max(candidates, key=lambda name: candidates[name]["P_mw_it"])
        winner = candidates[winner_name]
        without_gas = max((name for name in candidates if name != "燃气"),
                          key=lambda name: candidates[name]["P_mw_it"])
        method = winner["method"]
        on_site_mw = (method["installed_mw"] if "installed_mw" in method else
                      method.get("units", 0) * method.get("unit_net_mw", 0))
        record = {
            "发电用地预算_Ae_ha": budget,
            "纯电网_MW_IT": grid_result["P_mw_it"],
            "燃煤_MW_IT": candidates["燃煤"]["P_mw_it"] if "燃煤" in candidates else "",
            "燃气_MW_IT": candidates["燃气"]["P_mw_it"] if "燃气" in candidates else "",
            "风储_MW_IT": candidates["风储"]["P_mw_it"] if "风储" in candidates else "",
            "光储_MW_IT": candidates["光储"]["P_mw_it"] if "光储" in candidates else "",
            "全候选最优_MW_IT": winner["P_mw_it"],
            "无燃气时最优_MW_IT": candidates[without_gas]["P_mw_it"],
            "最优技术": winner_name,
            "实际发电用地_ha": winner["generation_land_ha"],
            "最优技术装机_MW": on_site_mw,
            "最优方案可靠自发电_MW": winner["breakdown"]["self_generation_mw"],
            "最优瓶颈": ";".join(winner["binding"]),
        }
        rows.append(record)

    write_csv(OUT / "19_generation_land_portfolio.csv", rows)
    plt.rcParams.update({
        "font.family": "Microsoft YaHei", "font.size": 9,
        "axes.unicode_minus": False, "svg.fonttype": "none",
    })
    fig = plt.figure(figsize=(11.5, 7.1), constrained_layout=True)
    grid = fig.add_gridspec(3, 2, height_ratios=[0.12, 1, 0.8], width_ratios=[2, 1])
    legend_ax = fig.add_subplot(grid[0, :])
    legend_ax.axis("off")
    overview = fig.add_subplot(grid[1, 0])
    zoom = fig.add_subplot(grid[1, 1])
    composition = fig.add_subplot(grid[2, :])
    axis = np.array([row["发电用地预算_Ae_ha"] for row in rows])
    for ax in (overview, zoom):
        ax.plot(axis, [row["纯电网_MW_IT"] for row in rows], color=COLORS["电网"],
                linestyle=":", linewidth=1.1, label="纯电网")
        for name in TECH:
            values = [float(row[f"{name}_MW_IT"]) if row[f"{name}_MW_IT"] != "" else np.nan
                      for row in rows]
            ax.plot(axis, values, color=COLORS[name], linewidth=1.5, label=name)
        ax.plot(axis, [row["无燃气时最优_MW_IT"] for row in rows],
                color="#758b99", linestyle="--", linewidth=1.6, label="未投运燃气时")
        ax.plot(axis, [row["全候选最优_MW_IT"] for row in rows],
                color=COLORS["最优"], linewidth=2.4, label="全候选最优")
        ax.set_xlabel("可供发电的用地上限（ha）")
        ax.grid(axis="y", color="#dce3e5", linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
    overview.set(xlim=(0, 440), ylim=(0, 230), ylabel="联合 IT 容量（MW IT）",
                 title="（a）发电用地预算与候选方案容量")
    zoom.set(xlim=(0, 45), ylim=(65, 225), title="（b）0–45 ha 局部放大")
    zoom.annotate("燃气 1 台", (10, 141.84), (14, 176), fontsize=8,
                  arrowprops={"arrowstyle": "->", "color": "#76838b"})
    zoom.annotate("燃气 2 台", (20, 212.77), (27, 185), fontsize=8,
                  arrowprops={"arrowstyle": "->", "color": "#76838b"})
    handles, labels = overview.get_legend_handles_labels()
    legend_ax.legend(handles, labels, ncol=7, loc="center", frameon=False, fontsize=8)

    lower = np.zeros(len(rows))
    for name in TECH:
        values = np.array([row["最优技术装机_MW"] if row["最优技术"] == name else 0
                           for row in rows])
        composition.fill_between(axis, lower, lower + values, step="post", alpha=0.88,
                                 color=COLORS[name], label=name)
        lower += values
    composition.set(xlim=(0, 440), ylim=(0, 225),
                    xlabel="可供发电的用地上限（ha）", ylabel="最优方案的自建装机（MW）",
                    title="（c）获胜配置的实际自建装机（不含电网）")
    composition.grid(axis="y", color="#dce3e5", linewidth=0.6)
    composition.spines[["top", "right"]].set_visible(False)
    composition.legend(loc="upper right", ncol=4, frameon=False, fontsize=8)
    fig.suptitle("固定场址资源预算：分配多少发电用地、采用哪种供电方案？", fontsize=13)
    for suffix in ("png", "svg"):
        fig.savefig(OUT / f"20_generation_land_supply_choice.{suffix}", dpi=240,
                    bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)

    index_path = OUT / "00_output_index.csv"
    with index_path.open(encoding="utf-8-sig", newline="") as handle:
        index = list(csv.DictReader(handle))
    for item in index:
        if item["编号"] == "10":
            item["文件"] = "../10_geographic_case_report.md"
            item["输入"] = ("输出 01–09、11–23 与来源表" if any(r["编号"] == "23" for r in index)
                          else "输出 01–09、11、19–20 与来源表")
    index = [row for row in index if row["编号"] not in {"19", "20"}]
    index.extend([
        {"编号": "19", "文件": "19_generation_land_portfolio.csv",
         "输入": "基准 Q1 配置、设计日辐照/风速、发电用地预算 0–440 ha",
         "意义": "每种供电技术及最优方案的联合 IT 容量与实际装机",
         "条件": "每点在实际 A_e 不超过横轴用地上限的单技术候选中取最大；燃气按燃料充分且可投运上界",
         "用途": "逐点复算图 20；比较无燃气可投运方案"},
        {"编号": "20", "文件": "20_generation_land_supply_choice.png; 20_generation_land_supply_choice.svg",
         "输入": "输出 19", "意义": "各方案容量、低用地放大与最优装机组成",
         "条件": "横轴为发电用地可用上限，每条曲线最大化实际 A_e 不超过上限的候选；不含煤气风光混装",
         "用途": "与 Q1 主判据及发电用地耦合对应的论文图"},
    ])
    write_csv(index_path, sorted(index, key=lambda row: int(row["编号"])))
    print(json.dumps({
        "points": len(rows), "grid_only_mw_it": grid_result["P_mw_it"],
        "at_0_ha": rows[0]["全候选最优_MW_IT"],
        "at_10_ha": next(row["全候选最优_MW_IT"] for row in rows if row["发电用地预算_Ae_ha"] == 10),
        "at_20_ha": next(row["全候选最优_MW_IT"] for row in rows if row["发电用地预算_Ae_ha"] == 20),
        "at_440_ha": rows[-1]["全候选最优_MW_IT"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
