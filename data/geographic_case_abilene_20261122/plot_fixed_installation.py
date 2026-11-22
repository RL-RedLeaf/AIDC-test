"""Compare exact installed MW using Q1's site budgets and cyclic design day."""

import csv
import itertools
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
import yaml

CASE = Path(__file__).resolve().parent
OUT = CASE / "outputs"
sys.path.insert(0, str(CASE.parents[1] / "code"))
from immc_power_capacity.core import assess_site, solve_storage_capacity, water_budget
from plot_supply_choice import write_csv

TECHS = ("燃煤", "燃气", "风电", "光伏")
COLORS = ("#94725f", "#3274a7", "#26957e", "#df9d28")
TOL = 2e-6


class Mix:
    def __init__(self, site, weather):
        self.site = site
        self.grid = site["P_grid_mw"]
        self.k = site["k_factor"]
        self.wue = site["water"]["wue_l_per_kwh_it"]
        self.q = water_budget(site["water"])["Q_max_m3_h"]
        land = site["land"]
        self.area = land["effective_ha"] - land["fixed_it_ha"]
        self.intensity = land["ha_per_mw_it"]
        specs = [s for s in site["scenarios"] if s["online_year"] <= site["assessment_year"]]
        coal, gas = [max((s for s in specs if s["type"] == tech), key=lambda s: s["units"])
                     for tech in ("coal", "gas")]
        wind = next(s for s in specs if s["type"] == "combined_battery")
        pv = next(s for s in specs if s["type"] == "solar")
        self.counts = list(itertools.product(range(coal["units"] + 1), range(gas["units"] + 1)))
        self.unit = np.array([s["unit_net_mw"] for s in (coal, gas)])
        self.wcoef = np.array([s["generation_water_l_per_kwh"] for s in (coal, gas)])
        self.land_per_mw = np.array([
            coal["unit_land_ha"] / self.unit[0], gas["unit_land_ha"] / self.unit[1],
            wind["generation_land_ha"] / wind["installed_mw"], 100 / pv["density_mw_per_km2"],
        ])
        self.profile = np.array([[float(r["wind_turbine_power_ratio_assumed"]),
                                  float(r["PV_AC_supply_ratio_PR_0_85_temp_adjusted"])] for r in weather])
        np.testing.assert_allclose(self.profile[:, 0], np.array(wind["supply_series_mw"]) / wind["installed_mw"])
        np.testing.assert_allclose(self.profile[:, 1], pv["supply_ratios"])
        battery = wind["battery"]
        self.charge, self.discharge, self.energy = [
            battery[key] / wind["installed_mw"] for key in ("C_max_mw", "D_max_mw", "E_usable_mwh")]
        self.ec, self.ed = battery["charge_efficiency"], battery["discharge_efficiency"]
        pv_mw = pv["area_km2"] * pv["density_mw_per_km2"]
        ratings = ("C_max_mw", "D_max_mw", "E_usable_mwh")
        np.testing.assert_allclose([pv["battery"][key] / pv_mw for key in ratings],
                                   [self.charge, self.discharge, self.energy])
        np.testing.assert_allclose([pv["battery"]["charge_efficiency"], pv["battery"]["discharge_efficiency"]],
                                   [self.ec, self.ed])
        assert wind["dt_hours"] == pv["dt_hours"] == 1 and len(self.profile) == 24
        self.prepare_lp()

    def prepare_lp(self):
        # Variables: IT MW, wind MW, solar MW, then hourly coal/gas/charge/discharge/SOC.
        hours = len(self.profile)
        self.hourly = np.arange(3, 3 + 5 * hours).reshape(5, hours)
        n = 3 + 5 * hours
        inequalities, limits, equalities = [], [], []

        def limit(terms, rhs):
            row = np.zeros(n)
            for j, coefficient in terms:
                row[j] = coefficient
            inequalities.append(row)
            limits.append(rhs)

        limit([(0, self.intensity), (1, self.land_per_mw[2]), (2, self.land_per_mw[3])], self.area)
        for t, (wind, pv) in enumerate(self.profile):
            coal, gas, charge, discharge, soc = self.hourly[:, t]
            limit([(0, self.k), (1, -wind), (2, -pv), (coal, -1), (gas, -1),
                   (charge, 1), (discharge, -1)], self.grid)
            limit([(0, self.wue), (coal, self.wcoef[0]), (gas, self.wcoef[1])], self.q)
            limit([(charge, 1), (1, -wind), (2, -pv)], 0)
            for index, rate in [(charge, self.charge), (discharge, self.discharge), (soc, self.energy)]:
                limit([(index, 1), (1, -rate), (2, -rate)], 0)
            row = np.zeros(n)
            row[[self.hourly[4, (t + 1) % hours], soc, charge, discharge]] = [1, -1, -self.ec, 1/self.ed]
            equalities.append(row)
        self.power_objective = np.zeros(n)
        self.power_objective[0] = -1
        self.renew_objective = np.zeros(n)
        self.renew_objective[1:3] = 1
        self.A = csr_matrix(inequalities)
        self.b = np.array(limits)
        self.cycle = csr_matrix(equalities)
        self.fixed = csr_matrix(np.vstack([equalities, self.renew_objective]))

    def solve(self, counts, total=None, peak=None):
        thermal = np.array(counts) * self.unit
        remaining_land = self.area - thermal @ self.land_per_mw[:2]
        residual = None if total is None else total - thermal.sum()
        if residual is not None and (residual < -1e-8 or residual * min(self.land_per_mw[2:]) > remaining_land + 1e-8):
            return None
        b = self.b.copy()
        b[0] = remaining_land
        bounds = [(0, None)] * len(self.power_objective)
        for indexes, capacity in zip(self.hourly[:2], thermal):
            for index in indexes:
                bounds[index] = (0, capacity)
        if peak is not None:
            bounds[0] = (peak, peak)
        rhs = np.zeros(len(self.profile))
        result = linprog(self.power_objective if peak is None else self.renew_objective,
                         A_ub=self.A, b_ub=b,
                         A_eq=self.cycle if total is None else self.fixed,
                         b_eq=rhs if total is None else np.r_[rhs, max(0, residual)],
                         bounds=bounds, method="highs")
        if result.status == 2:
            return None
        if not result.success:
            raise RuntimeError(result.message)
        return result.x

    def audit(self, counts, solution, total):
        p, w, s = solution[:3]
        mix = np.r_[counts * self.unit, w, s]
        coal, gas, charge, discharge, soc = solution[self.hourly]
        # Remove any simultaneous charging/discharging while preserving the solved SOC.
        stored = self.ec * charge - discharge/self.ed
        charge = np.maximum(0, stored) / self.ec
        discharge = np.maximum(0, -stored) * self.ed
        renewable = self.profile @ mix[2:]
        water = self.wue*p + self.wcoef[0]*coal + self.wcoef[1]*gas
        surplus = self.grid + renewable + coal + gas + discharge - charge - self.k*p
        assert abs(mix.sum() - total) < TOL and min(mix) >= -TOL
        assert self.intensity*p + mix @ self.land_per_mw <= self.area + TOL
        assert water.max() <= self.q + TOL and surplus.min() >= -TOL
        assert (charge <= renewable + TOL).all() and charge.max() <= self.charge*(w+s) + TOL
        assert discharge.max() <= self.discharge*(w+s) + TOL and soc.max() <= self.energy*(w+s) + TOL
        np.testing.assert_allclose(np.roll(soc, -1), soc + self.ec*charge - discharge/self.ed, atol=TOL)
        assert coal.max() <= mix[0] + TOL and gas.max() <= mix[1] + TOL
        return mix, water, np.array([renewable, coal, gas, charge, discharge, soc, surplus])

    def pure_capacity(self, total, pure_renewable):
        result = [None, None, None, None]
        for i, kind in enumerate(("coal", "gas")):
            if total == 0:
                result[i] = self.grid / self.k
            for s in self.site["scenarios"]:
                if s["type"] == kind and s["units"]*s["unit_net_mw"] == total:
                    result[i] = assess_site(dict(self.site, scenarios=[s]))["P_max_mw_it"]
        for j, firm in enumerate(pure_renewable, 2):
            left = self.area - self.land_per_mw[j]*total
            if left >= -TOL:
                result[j] = max(0, min((self.grid + firm*total)/self.k, self.q/self.wue, left/self.intensity))
        return result


def run():
    with (OUT / "04_design_day_weather_to_PV.csv").open(encoding="utf-8-sig", newline="") as f:
        weather = list(csv.DictReader(f))
    model = Mix(yaml.safe_load((OUT / "01_q1_inputs.yaml").read_text(encoding="utf-8")), weather)
    # The appendix-A LP is homogeneous for one technology when battery ratings scale with MW.
    pure_firm = [solve_storage_capacity(r, 1, model.charge, model.discharge, model.energy,
                                        model.ec, model.ed)[0] for r in model.profile.T]
    peaks, limits = [], []
    for counts in model.counts:
        thermal = model.unit * counts
        limits.append(thermal.sum() + (model.area - thermal @ model.land_per_mw[:2]) / min(model.land_per_mw[2:]))
        primary = model.solve(counts)
        if primary is not None:
            sol = model.solve(counts, peak=primary[0])
            peaks.append((sol[0], thermal.sum() + sum(sol[1:3]), counts, sol))
    capacity = max(p[0] for p in peaks)
    peak, peak_x, peak_counts, peak_sol = min((p for p in peaks if p[0] >= capacity - 1e-8), key=lambda p: p[1])
    max_x = max(limits)
    # Include actual branch ends and all integer-block thresholds. Plot jumps explicitly.
    renewable_turns = [(model.area - model.intensity*model.grid/model.k) /
                       (a + model.intensity*f/model.k) for a,f in zip(model.land_per_mw[2:], pure_firm)]
    thresholds = np.unique([model.unit @ counts for counts in model.counts])
    boundaries = np.r_[limits, [p[1] for p in peaks], renewable_turns, thresholds[1:] - .001]
    xs = np.unique(np.round(np.r_[np.arange(0, max_x, 1), np.arange(0, 15.01, .25),
                                 [model.area/a for a in model.land_per_mw[2:]], boundaries, peak_x], 9))
    rows = []
    for x in xs:
        choices = []
        for counts in model.counts:
            sol = model.solve(counts, total=x)
            if sol is not None:
                choices.append((sol[0], counts, sol))
        if not choices:
            raise ValueError(f"Unexpected infeasible sample {x}")
        _, counts, sol = max(choices, key=lambda choice: choice[0])
        mix, water, _ = model.audit(counts, sol, x)
        pure = model.pure_capacity(x, pure_firm)
        assert all(sol[0] + TOL >= v for v in pure if v is not None)
        rows.append(dict(zip(("总装机_MW", "最优联合容量_MW_IT", *(t+"装机_MW" for t in TECHS),
                              *(t+"单项上限_MW_IT" for t in TECHS), "发电用地_ha", "最大逐时取水_m3_h"),
                             (x, sol[0], *mix, *pure, mix @ model.land_per_mw, water.max()))))
    mix, water, hourly = model.audit(peak_counts, peak_sol, peak_x)
    assert abs(max(row["最优联合容量_MW_IT"] for row in rows) - peak) < TOL
    dispatch = [dict(zip(("当地时刻", "总装机_MW", "IT容量_MW", "风光可用_MW", "煤电调用_MW", "气电调用_MW",
                          "充电_MW", "放电_MW", "期初可用电量_MWh", "可削减供电余量_MW", "总取水_m3_h"),
                         (r["local_time"], peak_x, peak, *hourly[:, t], water[t]))) for t, r in enumerate(weather)]
    write_csv(OUT / "21_fixed_installation_mix.csv", rows)
    write_csv(OUT / "22_fixed_installation_peak_day.csv", dispatch)
    draw(rows, peak_x, peak)
    update_index()
    print(dict(peak=peak, X=peak_x, mix=mix.tolist(), max_X=max_x, samples=len(rows),
               land_used=mix@model.land_per_mw, water_peak=water.max()))


def draw(rows, peak_x, peak):
    plt.rcParams.update({"font.family": "Microsoft YaHei", "font.size": 9, "axes.unicode_minus": False,
                         "svg.fonttype": "path", "mathtext.fontset": "stix"})
    x = np.array([r["总装机_MW"] for r in rows])
    y = np.array([r["最优联合容量_MW_IT"] for r in rows])
    parts = np.array([[r[t+"装机_MW"] for r in rows] for t in TECHS])
    optimum = "#6d428c"
    fig = plt.figure(figsize=(11, 7.4), layout="constrained")
    layout = fig.add_gridspec(4, 2, height_ratios=[.12, 1, .8, .11], width_ratios=[1.95, 1])
    key = fig.add_subplot(layout[0, :])
    key.axis("off")
    full, zoom, stack = fig.add_subplot(layout[1, 0]), fig.add_subplot(layout[1, 1]), fig.add_subplot(layout[2, :])
    notes = fig.add_subplot(layout[3, :])
    notes.axis("off")
    switches = np.flatnonzero(np.any(np.diff(parts[:2], axis=1) != 0, axis=0)) + 1
    groups = np.split(np.arange(len(x)), switches)
    for ax in (full, zoom):
        for indices in groups:
            ax.plot(x[indices], y[indices], color=optimum, lw=2.8, zorder=2)
            ax.scatter(x[indices[0]], y[indices[0]], s=10, color=optimum, zorder=3)
        for t, col, mark in zip(TECHS, COLORS, ("s", "D", None, None)):
            pure = np.array([r[t+"单项上限_MW_IT"] for r in rows], dtype=float)
            if mark:
                ok = np.isfinite(pure) & (x > 0)
                ax.scatter(x[ok], pure[ok], color=col, marker=mark, s=36, zorder=5,
                           edgecolors="white", linewidth=.8)
            else:
                ax.plot(x, pure, color=col, lw=1.65, linestyle="--", zorder=3)
        ax.set(xlabel="新增发电总装机 $X$（MW）", ylabel="可持续 IT 容量（MW IT）")
    full.set(title="（a）全部可行装机范围", xlim=(-4, x[-1]+4), ylim=(-3, peak*1.17))
    full.scatter(peak_x, peak, color=optimum, marker="*", s=110, zorder=6)
    full.annotate(f"最高 {peak:.2f} MW IT", (peak_x, peak), xytext=(-68, 15),
                  textcoords="offset points", color=optimum, fontsize=9,
                  arrowprops=dict(arrowstyle="-", color=optimum))
    zoom.set(title="（b）0–15 MW 局部放大", xlim=(0, 15),
             ylim=(y[0]-.07, max(y[x <= 15])+.09))
    zoom.axhline(y[0], color="#66747c", ls=":", lw=1)
    zoom.text(.04, .93, "纯光伏配储与最优线重合\n点线为纯电网基准", transform=zoom.transAxes,
              fontsize=8, va="top", color="#384852")
    for indices in groups:
        stack.stackplot(x[indices], *parts[:, indices], colors=COLORS, linewidth=0, alpha=.93)
    stack.plot(x, x, color="#54616a", lw=.8, ls=":")
    stack.set(xlim=full.get_xlim(), ylim=(0, x[-1]*1.055), title="（c）各装机规模下最优组合的构成",
              xlabel="新增发电总装机 $X$（MW）", ylabel="各技术装机（MW）")
    for ax in (full, zoom, stack):
        ax.grid(axis="y", color="#dce3e6", lw=.65)
        ax.set_axisbelow(True)
        ax.spines[["top","right"]].set_visible(False)
    key.legend(handles=[Line2D([],[],marker=m,color=c,linestyle="none",label=t)
                        for t,c,m in zip(TECHS[:2],COLORS[:2],("s","D"))] +
               [Line2D([],[],ls="--",color=c,label=t+"配储") for t,c in zip(TECHS[2:],COLORS[2:])] +
               [Line2D([],[],color=optimum,lw=2.8,label="最优混装")],
               loc="center", ncol=5, frameon=False)
    notes.text(0,.55, "同一场址，电网持续供电取 100 MW，设计日为 2025 年 1 月 29 日。煤、气各限 0–2 台，每台净出力 100 MW。\n"
               "装机总量仅计煤、气、风、光。风光配套储能按相同规则配置，装机配比突变处分段绘制。",
               fontsize=8, va="center", color="#4e6068")
    fig.suptitle("给定新增发电总装机，哪种组合能支撑最大的 IT 容量？", fontsize=15)
    for fmt in ("png","svg"):
        fig.savefig(OUT / f"23_fixed_installation_mix.{fmt}", dpi=220)
    plt.close(fig)


def update_index():
    index = OUT/"00_output_index.csv"
    with index.open(encoding="utf-8-sig", newline="") as f:
        records = [r for r in csv.DictReader(f) if r["编号"] not in {"21","22","23"}]
    records.extend(index_entries())
    next(r for r in records if r["编号"]=="10")["输入"] = "输出 01–09、11–23 与来源表"
    write_csv(index, sorted(records, key=lambda r:int(r["编号"])))


def index_entries():
    fields = ("编号","文件","输入","意义","条件","用途")
    entries = [
        ("21","21_fixed_installation_mix.csv","01 场址与设备，04 设计日风光出力","各给定装机量的四类单项容量、最优混装和资源使用","四类新增净装机之和等于 X，风光共享储能，空白为单项不可行","复算图 23 的坐标和组成"),
        ("22","22_fixed_installation_peak_day.csv","01、04 与连续装机最优解","峰值方案的 24 小时电、水及储能平衡","设计日循环，充放电效率分别 0.90","核查连续负载和取水约束"),
        ("23","23_fixed_installation_mix.png; 23_fixed_installation_mix.svg","输出 21、22","新增装机、可持续 IT 容量及最优技术配比","同一场址条件，煤、气各最多两台，风光可连续配比","与参考图按相同坐标维度比较"),
    ]
    return [dict(zip(fields, entry)) for entry in entries]


if __name__ == "__main__":
    run()
