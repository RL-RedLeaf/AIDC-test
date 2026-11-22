"""Plot a conditional Abilene sensitivity from numbered Q1 model outputs.

Run after data/primary_20261121/scripts/build_abilene.py. This script does
not estimate new capacities or use Epoch's reported IT power as an input.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "primary_20261121" / "outputs"
POWER = "#396D9D"
LAND = "#CA7D35"
INK = "#24313B"
MUTED = "#64717A"


def text(english: str, chinese: str, zh: bool) -> str:
    return chinese if zh else english


def model_rows() -> list[dict[str, str]]:
    with (DATA / "04_design_sensitivity.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 12:
        raise ValueError("Expected exactly twelve static sensitivity cases")
    return rows


def plot(zh: bool, rows: list[dict[str, str]]) -> None:
    plt.rcParams.update({
        "font.family": "Noto Serif SC" if zh else "Times New Roman",
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
        "savefig.facecolor": "white",
        "svg.fonttype": "path",
    })
    fractions = [0.25, 0.50, 0.75, 1.00]
    multipliers = [1.15, 1.30, 1.40]
    lookup = {(float(row["k_design"]), float(row["effective_site_fraction"])): row
              for row in rows}
    capacities = np.array([[float(lookup[(k, area)]["P_max_mw_it"]) for area in fractions]
                           for k in multipliers])
    binding = np.array([[0 if lookup[(k, area)]["binding"] == "\u7535\u529b" else 1
                         for area in fractions] for k in multipliers])

    fig, (left, right) = plt.subplots(1, 2, figsize=(7.4, 3.55), sharex=True,
                                     sharey=True, gridspec_kw={"width_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.09, right=0.97, bottom=0.26, top=0.83, wspace=0.38)
    im = left.imshow(capacities, cmap="YlGnBu", vmin=700, vmax=900,
                     interpolation="nearest", aspect="auto")
    colorbar = fig.colorbar(im, ax=left, shrink=0.83, pad=0.025)
    colorbar.set_label(text("MW IT", "MW IT", zh))
    right.imshow(binding, cmap=ListedColormap([POWER, LAND]),
                 norm=BoundaryNorm([-0.5, 0.5, 1.5], 2),
                 interpolation="nearest", aspect="auto")

    for ax, title in ((left, text("A  |  Electricity-land ceiling", "A  |  \u7535\u529b\u2014\u571f\u5730\u7b5b\u67e5", zh)),
                      (right, text("B  |  Binding constraint", "B  |  \u9996\u8981\u7ea6\u675f", zh))):
        ax.set_title(title, loc="left", pad=9)
        ax.set_xticks(range(4), [f"{fraction:.0%}" for fraction in fractions])
        ax.set_yticks(range(3), [f"{k:.2f}" for k in multipliers])
        ax.set_xlabel(text("Usable share of gross campus", "\u6709\u6548\u7528\u5730\u6bd4\u4f8b", zh))
        ax.tick_params(length=0)
        ax.spines[:].set_visible(False)
        ax.set_xticks(np.arange(-.5, 4, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 3, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.5)
        ax.tick_params(which="minor", bottom=False, left=False)
    left.set_ylabel(text("Full-load facility / IT factor k", "\u6ee1\u8f7d\u8bbe\u65bd/IT\u500d\u7387 k", zh))

    for i in range(3):
        for j in range(4):
            number = capacities[i, j]
            is_base = (i, j) == (1, 3)
            left.text(j, i, f"{number:.0f}{'*' if is_base else ''}",
                      ha="center", va="center", color="white" if number > 810 else INK,
                      fontsize=8.5, fontweight="medium")
            right.text(j, i, text("E" if binding[i, j] == 0 else "L",
                                  "\u7535" if binding[i, j] == 0 else "\u5730", zh),
                       ha="center", va="center", color="white", fontsize=9,
                       fontweight="medium")
    right.legend(handles=[Patch(facecolor=POWER, label=text("Electricity", "\u7535\u529b", zh)),
                          Patch(facecolor=LAND, label=text("Land", "\u571f\u5730", zh))],
                 loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2,
                 frameon=False, fontsize=8)
    fig.text(0.09, 0.93, text("Abilene 2030: static conditional screen",
                              "Abilene 2030: \u9759\u6001\u6761\u4ef6\u7b5b\u67e5", zh), fontsize=10, color=INK)
    fig.text(0.09, 0.04, text(
        "* Baseline: k=1.30, gross land 100%. Water WUE/limit unresolved; not a three-resource P_max.",
        "* \u57fa\u51c6: k=1.30, \u603b\u7528\u5730\u5168\u90e8\u53ef\u7528. \u6c34 WUE/\u4e0a\u9650\u672a\u5b9a; \u975e\u7535\u6c34\u5730\u8054\u5408\u6700\u5927\u503c.", zh), fontsize=7.4, color=MUTED)
    stem = "fig06_abilene_binding_zh" if zh else "fig06_abilene_binding"
    for extension in ("png", "svg"):
        fig.savefig(OUT / f"{stem}.{extension}", dpi=300, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def write_data(rows: list[dict[str, str]]) -> None:
    fields = ["k_design", "effective_site_fraction", "P_E_mw_it", "P_W_mw_it",
              "P_L_mw_it", "P_max_mw_it", "binding", "classification"]
    with (OUT / "fig06_abilene_binding.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_index() -> None:
    meanings = {
        "fig01": "Synthetic: six supply portfolios and joint constraints",
        "fig02": "Synthetic: grid/water capacity and binding map",
        "fig03": "Synthetic: generation-land tradeoff",
        "fig04": "Synthetic: battery power and energy constraints",
        "fig05": "Synthetic: commissioning-year candidate set",
        "fig06": "Abilene: conditional k and effective-land sensitivity",
    }
    fields = ["number", "file", "inputs", "meaning", "conditions", "use"]
    with (OUT / "00_output_index.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(dict(zip(fields, ("00", "00_output_index.csv", "all figure files",
                                          "index of every output in visualize", "mixed synthetic and conditional real-site figures",
                                          "find figures and their scope"))))
        for path in sorted(OUT.glob("fig*.*")):
            group = path.stem[:5]
            if group not in meanings:
                continue
            is_real = group == "fig06"
            writer.writerow({
                "number": group[3:5], "file": path.name,
                "inputs": "data/primary_20261121/outputs/04_design_sensitivity.csv" if is_real else "visualize/plot_q1.py",
                "meaning": meanings[group],
                "conditions": "2030 static conditional screen; P_W not verified" if is_real else "fully synthetic model diagnostic",
                "use": "inspect exact values" if path.suffix == ".csv" else "chart preview/editing",
            })


def main() -> None:
    raise SystemExit(
        "Abilene fig06 was withdrawn because its grid and land inputs are "
        "unsupported. See data/primary_20261121/outputs/15_validity_audit.csv."
    )

    rows = model_rows()
    write_data(rows)
    plot(False, rows)
    plot(True, rows)
    write_index()


if __name__ == "__main__":
    main()
