"""Reproducible, synthetic Q1 model diagnostics for the paper.

Run from any working directory: python visualize/plot_q1.py
All numerical outputs are computed through code/immc_power_capacity.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "code"))

from immc_power_capacity.core import assess_site, solar  # noqa: E402


# Designed full-load multiplier and water/land budgets below are illustrative
# model inputs, not estimates for a particular region or facility.
INK = "#24313B"
MUTED = "#64717A"
GRID = "#DCE3E5"
POWER = "#396D9D"
WATER = "#168B81"
LAND = "#CA7D35"
JOINT = "#2D3038"
OTHER = "#84648F"
ZH = False
SCENARIO_ZH = {
    "Grid only": "纯电网", "Wind": "风电", "PV + battery": "光储",
    "Gas / wet": "湿冷燃气", "Gas / dry": "干冷燃气", "Coal": "煤电",
}


def text(en: str, zh: str) -> str:
    return zh if ZH else en

plt.rcParams.update({
    "font.family": "Times New Roman",
    "mathtext.fontset": "stix",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.linewidth": 0.7,
    "lines.linewidth": 1.8,
    "savefig.facecolor": "white",
    "pdf.fonttype": 42,
    "svg.fonttype": "path",
})


def base_site() -> dict:
    return {
        "model": "q1",
        "site": "Illustrative fixed site",
        "assessment_year": 2032,
        "period_note": "Illustrative design cycle; constant rated IT load",
        "service_level": "Normal operation; no outage reliability criterion",
        "P_grid_mw": 108.0,
        "k_factor": 1.2,
        "water": {
            "basis": "consumption",
            "source_m3_h": 150.0,
            "wue_l_per_kwh_it": 1.5,
            "generation_water_l_per_kwh": {
                "coal": 2.6,
                "gas": 0.78,
                "wind": 0.0,
                "solar": 0.0,
            },
        },
        "land": {
            "effective_ha": 160.0,
            "fixed_it_ha": 10.0,
            "ha_per_mw_it": 1.0,
            "generation_land_ha": 0.0,
        },
        "scenarios": [],
    }


def technologies() -> list[dict]:
    return [
        {"name": "Grid only", "type": "grid", "online_year": 2026},
        {"name": "Wind", "type": "wind", "online_year": 2028,
         "generation_land_ha": 30, "area_km2": 0.3,
         "density_mw_per_km2": 100, "net_output_mw": [12, 4]},
        {"name": "PV + battery", "type": "solar", "online_year": 2028,
         "generation_land_ha": 20, "area_km2": 0.2,
         "density_mw_per_km2": 100, "net_output_mw": [20, 0],
         "dt_hours": 1,
         "battery": {"C_max_mw": 10, "D_max_mw": 10, "E_usable_mwh": 10}},
        {"name": "Gas / wet", "type": "gas", "online_year": 2029,
         "generation_land_ha": 20, "units": 1, "unit_net_mw": 60,
         "unit_land_ha": 5},
        {"name": "Gas / dry", "type": "gas", "online_year": 2030,
         "generation_land_ha": 20, "units": 1, "unit_net_mw": 60,
         "unit_land_ha": 5, "wue_l_per_kwh_it": 0.75,
         "generation_water_l_per_kwh": 0.0076},
        {"name": "Coal", "type": "coal", "online_year": 2032,
         "generation_land_ha": 30, "units": 2, "unit_net_mw": 80,
         "unit_land_ha": 15},
    ]


def write_csv(stem: str, columns: list[str], rows: list[tuple]) -> None:
    if ZH:
        return  # The numerical table is shared by both language editions.
    with (OUT / f"{stem}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)


def finish(fig: plt.Figure, stem: str) -> None:
    if ZH:
        stem += "_zh"
    for ext in ("pdf", "svg", "png"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=300, bbox_inches="tight",
                    pad_inches=0.12)
    plt.close(fig)


def tidy(ax: plt.Axes, axis: str = "x") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=axis, color=GRID, lw=0.55, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.6)


def figure_01_limits() -> None:
    site = base_site()
    site["scenarios"] = technologies()
    rows = assess_site(site)["scenarios"]
    fig, ax = plt.subplots(figsize=(7.25, 3.65), layout="constrained")
    y = np.arange(len(rows))
    specs = (("P_E_mw_it", POWER, -0.20),
             ("P_W_mw_it", WATER, 0.0),
             ("P_L_mw_it", LAND, 0.20))
    for field, color, shift in specs:
        values = [row[field] if row[field] is not None else np.nan for row in rows]
        ax.scatter(values, y + shift, s=37, color=color, zorder=3,
                   label={"P_E_mw_it": text("Electricity", "电力"),
                          "P_W_mw_it": text("Water", "水量"),
                          "P_L_mw_it": text("Land", "土地")}[field])
    joint = [row["P_mw_it"] for row in rows]
    ax.scatter(joint, y, s=60, marker="D", facecolor=JOINT,
               edgecolor="white", linewidth=0.8, zorder=4,
               label=text("Joint limit", "联合容量"))
    ax.set_yticks(y, [SCENARIO_ZH[row["name"]] if ZH else row["name"] for row in rows])
    ax.invert_yaxis()
    ax.set_xlim(65, 235)
    ax.set_xlabel(text("Rated IT capacity (MW)", "额定 IT 容量 (MW)"))
    ax.set_title(text("One site, six completed configurations", "同一场址下的六种供能方案"),
                 loc="left", pad=9)
    binding_label = {"电力": text("E", "电"), "水": text("W", "水"),
                     "土地": text("L", "地")}
    for idx, row in enumerate(rows):
        labels = "+".join(binding_label[item] for item in row["binding"])
        ax.annotate(f"{row['P_mw_it']:.1f}  ({labels})",
                    (row["P_mw_it"], idx), xytext=(5, -13), textcoords="offset points",
                    fontsize=7.5, color=INK)
    tidy(ax)
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              fontsize=7.5, handletextpad=0.35, columnspacing=0.9)
    finish(fig, "fig01_joint_limits")
    write_csv("fig01_joint_limits", ["scenario", "P_E_mw_it", "P_W_mw_it",
                                    "P_L_mw_it", "P_mw_it", "binding"],
              [(r["name"], r["P_E_mw_it"], r["P_W_mw_it"], r["P_L_mw_it"],
                r["P_mw_it"], "+".join(r["binding"])) for r in rows])


def figure_02_phase() -> None:
    grids = np.linspace(40, 180, 57)
    budgets = np.linspace(60, 260, 51)
    capacity = np.empty((len(budgets), len(grids)))
    binding = np.empty_like(capacity, dtype=int)
    site = base_site()
    site["scenarios"] = [technologies()[3]]  # wet-cooled gas, fixed equipment
    index = {"电力": 0, "水": 1, "土地": 2}
    output = []
    for i, water_limit in enumerate(budgets):
        site["water"]["source_m3_h"] = float(water_limit)
        for j, grid_mw in enumerate(grids):
            site["P_grid_mw"] = float(grid_mw)
            row = assess_site(site)["scenarios"][0]
            capacity[i, j] = row["P_mw_it"]
            binding[i, j] = index[row["binding"][0]]
            output.append((grid_mw, water_limit, row["P_E_mw_it"],
                           row["P_W_mw_it"], row["P_L_mw_it"],
                           row["P_mw_it"], "+".join(row["binding"])))
    fig, (left, right) = plt.subplots(1, 2, figsize=(7.35, 3.65), sharex=True,
                                     sharey=True, layout="constrained")
    extent = (grids[0], grids[-1], budgets[0], budgets[-1])
    im = left.imshow(capacity, origin="lower", extent=extent, aspect="auto",
                     cmap="YlGnBu", vmin=30, vmax=130, interpolation="nearest")
    left.contour(grids, budgets, capacity, levels=[60, 90, 110, 125],
                 colors="white", linewidths=0.65, alpha=0.8)
    bar = fig.colorbar(im, ax=left, shrink=0.83, pad=0.015)
    bar.set_label(text("Joint capacity (MW IT)", "联合容量 (MW IT)"))
    cmap = ListedColormap([POWER, WATER, LAND])
    right.imshow(binding, origin="lower", extent=extent, aspect="auto",
                 cmap=cmap, norm=BoundaryNorm([-0.5, 0.5, 1.5, 2.5], 3),
                 interpolation="nearest")
    for ax, title in ((left, text("A  |  Joint capacity", "A  |  联合容量")),
                      (right, text("B  |  Binding constraint", "B  |  首要约束"))):
        ax.set_title(title, loc="left", pad=8)
        ax.set_xlabel(text("Grid delivery (MW)", "电网可交付功率 (MW)"))
        ax.tick_params(length=3, width=0.6)
    left.set_ylabel(text("Water budget (m³/h)", "耗水预算 (m³/h)"))
    right.legend(handles=[Patch(facecolor=color, label=label) for color, label in
                          ((POWER, text("Electricity", "电力")),
                           (WATER, text("Water", "水量")),
                           (LAND, text("Land", "土地")))],
                 loc="upper center", bbox_to_anchor=(0.5, -0.20), frameon=False,
                 ncol=3, fontsize=7.5, columnspacing=0.8, handlelength=1)
    finish(fig, "fig02_binding_map")
    write_csv("fig02_binding_map", ["P_grid_mw", "water_budget_m3_h", "P_E_mw_it",
                                   "P_W_mw_it", "P_L_mw_it", "P_mw_it", "binding"], output)


def figure_03_land_allocation() -> None:
    site = base_site()
    site["P_grid_mw"] = 80
    site["water"].update(source_m3_h=130, wue_l_per_kwh_it=1.0,
                         generation_water_l_per_kwh={"gas": 0.4})
    site["land"].update(effective_ha=180, fixed_it_ha=10)
    site["scenarios"] = [{"name": "Modular gas plant", "type": "gas",
                          "units": 3, "unit_net_mw": 40, "unit_land_ha": 10}]
    rows = []
    for area in np.arange(10, 91):
        site["scenarios"][0]["generation_land_ha"] = int(area)
        row = assess_site(site)["scenarios"][0]
        rows.append((area, row["method"]["units"], row["P_E_mw_it"],
                     row["P_W_mw_it"], row["P_L_mw_it"], row["P_mw_it"],
                     "+".join(row["binding"])))
    arr = np.array([r[:6] for r in rows], dtype=float)
    best = max(rows, key=lambda r: (r[5], -r[0]))
    fig, ax = plt.subplots(figsize=(7.25, 3.7), layout="constrained")
    for col, label, color in ((2, text("Electricity", "电力"), POWER),
                              (3, text("Water", "水量"), WATER)):
        ax.step(arr[:, 0], arr[:, col], "--", where="post", color=color,
                lw=1.5, label=label)
    ax.plot(arr[:, 0], arr[:, 4], "--", color=LAND, lw=1.5,
            label=text("Land", "土地"))
    flat = arr[:, 0] <= 60
    ax.step(arr[flat, 0], arr[flat, 5], where="post", color=JOINT, lw=2.3,
            label=text("Joint limit", "联合容量"))
    ax.plot(arr[~flat, 0], arr[~flat, 5], color=JOINT, lw=2.3)
    ax.scatter([best[0]], [best[5]], s=56, marker="D", color=JOINT, zorder=5)
    ax.annotate(text("Smallest maximizing area", "达到最大值的最小用地")
                + f"\n{best[0]:.0f} ha  |  {best[5]:.1f} MW IT",
                (best[0], best[5]), xytext=(35, 14), textcoords="offset points",
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.8}, fontsize=8)
    ax.set_xlim(9, 91)
    ax.set_ylim(55, 185)
    ax.set_xlabel(text("Reserved generation land $A_e$ (ha)", "预留发电用地 $A_e$ (ha)"))
    ax.set_ylabel(text("Rated IT capacity (MW)", "额定 IT 容量 (MW)"))
    ax.set_title(text("Generation land raises supply and removes IT space",
                      "发电用地的收益与代价"), loc="left", pad=9)
    tidy(ax)
    ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16),
              fontsize=7.5, handlelength=1.7, columnspacing=1.1)
    finish(fig, "fig03_land_tradeoff")
    write_csv("fig03_land_tradeoff", ["A_e_ha", "available_units", "P_E_mw_it",
                                    "P_W_mw_it", "P_L_mw_it", "P_mw_it", "binding"], rows)


def figure_04_storage() -> None:
    hour = np.arange(24)
    supply = 50 * np.maximum(0, np.sin(np.pi * (hour - 6) / 12))

    def result(energy: int) -> dict:
        battery = None if energy == 0 else {
            "C_max_mw": 30, "D_max_mw": 30, "E_usable_mwh": energy,
            "charge_efficiency": 0.9, "discharge_efficiency": 0.9,
        }
        return solar("PV", 0, 1.2, 0.5, 100, dt_hours=1,
                     net_output_mw=supply.tolist(), battery=battery)

    energies = np.arange(0, 241, 10)
    capacities = [result(int(e))["breakdown"]["self_generation_mw"] for e in energies]
    dispatch = result(100)["method"]
    fig = plt.figure(figsize=(7.4, 4.7), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[1.4, 1], height_ratios=[1.2, 0.8])
    top = fig.add_subplot(gs[0, 0])
    bottom = fig.add_subplot(gs[1, 0], sharex=top)
    right = fig.add_subplot(gs[:, 1])
    top.plot(hour, supply, color=LAND, label=text("PV available", "光伏可用"), lw=1.8)
    top.axhline(dispatch["L_mw"], color=JOINT, lw=1.5, ls="--",
                label=text("Firm addition", "稳定增量"))
    top.step(hour, dispatch["charge_mw"], where="mid", color=WATER,
             label=text("Charge", "充电"), lw=1.2)
    top.step(hour, dispatch["discharge_mw"], where="mid", color=POWER,
             label=text("Discharge", "放电"), lw=1.2)
    top.set_ylabel(text("Power (MW)", "功率 (MW)"))
    top.set_title(text("A  |  One repeatable design day", "A  |  可重复运行的设计日"),
                  loc="left", pad=9)
    top.legend(loc="upper right", frameon=False, ncol=2, fontsize=7, columnspacing=0.7)
    bottom.step(hour, dispatch["energy_start_mwh"], where="post", color=OTHER, lw=1.8)
    bottom.set_ylabel(text("Battery energy (MWh)", "电池电量 (MWh)"))
    bottom.set_xlabel(text("Hour of cycle", "周期内时刻 (h)"))
    bottom.set_xticks([0, 6, 12, 18, 23])
    right.plot(energies, capacities, color=POWER, lw=2.2)
    right.scatter([100], [dispatch["L_mw"]], color=JOINT, marker="D", s=48, zorder=4)
    right.annotate(text("Dispatch shown at left", "左侧为该点的调度"),
                   (100, dispatch["L_mw"]),
                   xytext=(9, -22), textcoords="offset points", fontsize=7.5)
    right.set_title(text("B  |  Storage energy response", "B  |  储能容量响应"), loc="left", pad=9)
    right.set_xlabel(text("Usable battery energy (MWh)", "电池可用电量 (MWh)"))
    right.set_ylabel(text("Firm PV addition (MW)", "光伏稳定增量 (MW)"))
    for ax in (top, bottom, right):
        tidy(ax)
    finish(fig, "fig04_storage_cycle")
    write_csv("fig04_storage_sweep", ["E_usable_mwh", "firm_addition_mw"],
              list(zip(energies, capacities)))
    write_csv("fig04_storage_dispatch", ["hour", "available_pv_mw", "firm_addition_mw",
                                         "charge_mw", "discharge_mw", "energy_start_mwh",
                                         "curtailment_mw"],
              [(int(h), supply[h], dispatch["L_mw"], dispatch["charge_mw"][h],
                dispatch["discharge_mw"][h], dispatch["energy_start_mwh"][h],
                dispatch["curtailment_mw"][h]) for h in hour])


def figure_05_year() -> None:
    site = base_site()
    site["scenarios"] = [technologies()[i] for i in (0, 2, 3, 4, 5)]
    years = np.arange(2026, 2034)
    results = []
    for year in years:
        site["assessment_year"] = int(year)
        report = assess_site(site)
        results.append((year, report["P_max_mw_it"], "+".join(report["winners"]),
                        "+".join(row["name"] for row in report["scenarios"]),
                        "+".join(row["name"] for row in report["excluded"])))
    fig, ax = plt.subplots(figsize=(7.25, 3.35), layout="constrained")
    colors = {"Grid only": POWER, "PV + battery": LAND, "Gas / wet": WATER,
              "Gas / dry": OTHER, "Coal": MUTED}
    final = assess_site(site)
    for row in final["scenarios"]:
        online = row["online_year"]
        ax.plot([online, years[-1] + 0.25], [row["P_mw_it"]] * 2,
                color=colors[row["name"]], ls="--", lw=1.1, alpha=0.8)
        ax.scatter([online], [row["P_mw_it"]], color=colors[row["name"]], s=31, zorder=3)
        ax.annotate(SCENARIO_ZH[row["name"]] if ZH else row["name"],
                    (online, row["P_mw_it"]),
                    xytext=(3, 5 if row["name"] != "Gas / wet" else -13),
                    textcoords="offset points", fontsize=7.1, color=colors[row["name"]])
    ax.step(years, [r[1] for r in results], where="post", color=JOINT,
            lw=2.7, label="$P_{max}(y)$", zorder=4)
    ax.set_xlim(2025.8, 2033.5)
    ax.set_ylim(82, 153)
    ax.set_xticks(years)
    ax.set_xlabel(text("Assessment year $y$", "评估年份 $y$"))
    ax.set_ylabel(text("Rated IT capacity (MW)", "额定 IT 容量 (MW)"))
    ax.set_title(text("New availability changes the candidate set", "投运时间改变可选方案"),
                 loc="left", pad=9)
    tidy(ax)
    ax.legend(handles=[Line2D([], [], color=JOINT, lw=2.7,
                              label=text("Best available", "当年最大容量")),
                       Line2D([], [], color=MUTED, lw=1.1, ls="--",
                              label=text("Completed option", "已投运方案"))],
              frameon=False, loc="upper left", ncol=2, fontsize=7.7)
    finish(fig, "fig05_commissioning")
    write_csv("fig05_commissioning", ["year", "P_max_mw_it", "winners",
                                      "included", "excluded"], results)


def main() -> None:
    global ZH
    for ZH in (False, True):
        plt.rcParams["font.family"] = "Noto Serif SC" if ZH else "Times New Roman"
        figure_01_limits()
        figure_02_phase()
        figure_03_land_allocation()
        figure_04_storage()
        figure_05_year()
    print(f"Saved 5 bilingual figure pairs and numerical tables in {OUT}")


if __name__ == "__main__":
    main()
