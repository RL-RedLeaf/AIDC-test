"""Reproducible power/compute proxy regression. Run: python fit_eta.py [--csv PATH]."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def r2(y, pred):
    return float(1 - np.sum((y - pred)**2) / np.sum((y - y.mean())**2))


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=root / 'data_centers.csv')
    args = parser.parse_args()
    if not args.csv.exists() and args.csv == root / 'data_centers.csv':
        shutil.copy2(Path('E:/Downloads/data_centers.csv'), args.csv)
    raw = pd.read_csv(args.csv)
    power = pd.to_numeric(raw['Current power (MW)'], errors='coerce')
    compute = pd.to_numeric(raw['Current H100 equivalents'], errors='coerce')
    valid = np.isfinite(power) & np.isfinite(compute) & (power > 0) & (compute > 0)
    audit = raw[['Name', 'Current power (MW)', 'Current H100 equivalents']].copy()
    audit['included'] = valid
    audit['reason'] = np.where(valid, 'positive finite pair', 'nonpositive or missing pair; not an operating observation')
    audit.to_csv(root / 'sample_audit.csv', index=False, encoding='utf-8-sig')
    d = raw.loc[valid].copy()
    x = power[valid].to_numpy()  # MW; never silently relabel as IT power
    y = compute[valid].to_numpy()  # H100-equivalent capacity proxy
    if len(x) < 3 or np.ptp(x) == 0:
        raise ValueError('At least three positive pairs and varying power are required.')
    eta = float(x @ y / (x @ x))
    pred = eta * x
    a, b = np.linalg.lstsq(np.column_stack([x, np.ones(len(x))]), y, rcond=None)[0]
    rng = np.random.default_rng(20261122)
    idx = rng.integers(0, len(x), size=(10000, len(x)))
    xb, yb = x[idx], y[idx]
    slopes = np.sum(xb * yb, axis=1) / np.sum(xb * xb, axis=1)
    ci = np.quantile(slopes, [.025, .975])
    loo = np.array([(x @ y - x[i]*y[i]) / (x @ x - x[i]**2) for i in range(len(x))])
    loo_prediction = x * loo
    reverse = float(y @ x / (y @ y))
    result = {
        'source_sha256': hashlib.sha256(args.csv.read_bytes()).hexdigest(),
        'n_total': len(raw), 'n_used': len(x), 'n_excluded': int((~valid).sum()),
        'eta_proxy_H100eq_per_MW': eta, 'eta_proxy_H100eq_per_kW': eta / 1000,
        'eta_proxy_bootstrap95_per_MW': ci.tolist(),
        'origin_fit_centered_R2': r2(y, pred),
        'origin_fit_uncentered_R2': float(1 - np.sum((y-pred)**2) / (y@y)),
        'free_intercept_fit': {'slope_per_MW': float(a), 'intercept_H100eq': float(b), 'R2': r2(y, a*x+b)},
        'leave_one_out_R2': r2(y, loo_prediction),
        'leave_one_out_eta_range_per_MW': [float(loo.min()), float(loo.max())],
        'direct_power_on_compute_origin_fit': {'MW_per_H100eq': reverse, 'implied_eta_per_MW': 1/reverse, 'centered_R2': r2(x, reverse*y)},
        'individual_efficiency_percentiles_per_MW': np.quantile(y/x, [.1, .5, .9]).tolist(),
        'interpretation': 'Cross-sectional capacity proxies, not measured sustained output. Power scope unspecified. IT eta cannot be identified without power scope/PUE and utilization. Bootstrap assumes independent rows; shared-source errors are not included.'
    }
    (root / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    d['fitted_H100eq'] = pred
    d['residual_H100eq'] = y-pred
    d['eta_proxy_H100eq_per_kW'] = y/x/1000
    d.to_csv(root / 'fitted_data.csv', index=False, encoding='utf-8-sig')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.labelcolor': '#24344c', 'text.color': '#14263e',
                         'xtick.color': '#52627a', 'ytick.color': '#52627a', 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(13.5, 9), facecolor='#f6f8fc')
    gs = fig.add_gridspec(2, 2, height_ratios=[3.5, 1], width_ratios=[3.8, 1.5],
                          left=.09, right=.97, top=.83, bottom=.13, hspace=.12, wspace=.25)
    ax = fig.add_subplot(gs[0, 0]); res = fig.add_subplot(gs[1, 0], sharex=ax)
    info = fig.add_subplot(gs[:, 1]); info.axis('off')
    xx = np.linspace(0, x.max()*1.06, 300)
    ax.fill_between(xx, ci[0]*xx/1000, ci[1]*xx/1000, color='#2aa89d', alpha=.17, label='95% pairs-bootstrap band')
    ax.plot(xx, eta*xx/1000, color='#078b83', lw=2.8, label='Proportional fit (through origin)')
    ax.plot(xx, (a*xx+b)/1000, color='#b27b42', lw=1.5, ls='--', label='Free-intercept OLS')
    ax.scatter(x, y/1000, s=53, c='#265d96', alpha=.76, edgecolors='white', linewidths=.8, zorder=3, label=f'Data centers (n = {len(x)})')
    label_offsets = {'Colossus 2': (-12, 20),
                     'Anthropic-Amazon New Carlisle': (-18, -38),
                     'Google Pryor (North)': (-12, 20)}
    for name, offset in label_offsets.items():
        match = np.flatnonzero(d['Name'].to_numpy() == name)
        if len(match):
            i = match[0]
            ax.annotate(name, (x[i], y[i]/1000), xytext=offset, textcoords='offset points',
                        ha='right', fontsize=8, color='#334965',
                        arrowprops={'arrowstyle': '-', 'color': '#9aaabd', 'lw': .7,
                                    'shrinkA': 4, 'shrinkB': 5})
    ax.set_ylabel('Compute capacity (thousand H100 equivalents)', labelpad=12)
    ax.set_xlim(0, xx.max()); ax.set_ylim(bottom=0)
    ax.legend(loc='upper left', frameon=False, fontsize=9)
    ax.tick_params(labelbottom=False)
    res.axhline(0, color='#078b83', lw=1.3)
    res.scatter(x, (y-pred)/1000, s=27, c='#265d96', alpha=.7, edgecolors='white', linewidths=.4)
    res.set_ylabel('Residual\n(thousand)', fontsize=10)
    res.set_xlabel('Reported current power (MW)', labelpad=10)
    res.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    for axis in [ax, res]:
        axis.set_facecolor('white'); axis.grid(color='#dfe6ef', lw=.7, alpha=.7); axis.set_axisbelow(True)
        for spine in axis.spines.values(): spine.set_color('#d5deeb')
    info.text(0, .98, 'MODEL ESTIMATE', fontsize=10, color='#60738d', weight='bold', va='top')
    info.text(0, .89, r'$O_{\mathrm{proxy}}=\widehat{\eta}_{\mathrm{proxy}}P_{\mathrm{reported}}$', fontsize=15)
    info.text(0, .77, f'{eta/1000:.3f}', fontsize=39, weight='bold', color='#078b83')
    info.text(0, .71, 'H100 equivalents / kW', fontsize=11)
    info.text(0, .64, f'95% bootstrap interval\n[{ci[0]/1000:.3f}, {ci[1]/1000:.3f}]', fontsize=11, linespacing=1.6)
    info.text(0, .49, f'Centered R²       {r2(y,pred):.4f}\nFree-intercept R²  {r2(y,a*x+b):.4f}\nLeave-one-out R²   {r2(y,loo_prediction):.4f}', fontsize=11, linespacing=1.9)
    info.text(0, .24, 'INTERPRETATION', fontsize=10, weight='bold', color='#60738d')
    info.text(0, .19, 'Capacity proxy, not measured\nsustained compute. Reported\npower scope is unspecified.\nIT efficiency requires verified\nIT power and utilization.', fontsize=10, linespacing=1.55, va='top')
    fig.text(.09, .94, 'Compute scales with reported power', fontsize=25, weight='bold')
    fig.text(.09, .888, 'Cross-sectional data-center capacity  /  proportional regression with diagnostic comparison', fontsize=11, color='#60738d')
    fig.text(.09, .035, f'Source: supplied data_centers.csv. {len(x)} positive pairs; {len(raw)-len(x)} nonpositive/missing pairs excluded. All eligible observations retained.\nBand: 10,000 pairs-bootstrap samples, seed 20261122; uncertainty excludes shared-source and measurement errors.', fontsize=8.5, color='#60738d', linespacing=1.5)
    for ext in ['png', 'pdf', 'svg']:
        fig.savefig(root / f'compute_power_fit.{ext}', dpi=320, facecolor=fig.get_facecolor())
    plt.close(fig)
    report = f'''# 算力与功率关系：可复现拟合

原始数据共 {len(raw)} 条，使用两列均为正且有限的 {len(x)} 条记录，排除 {len(raw)-len(x)} 条无正值配对记录；不删除离群点。原始论文仅作为背景阅读，未修改。

## 结果

拟合方向为 O_proxy = η_proxy × P_reported，采用过原点最小二乘：η_hat = Σ(P_i O_i)/Σ(P_i²)。这直接估计算力对功率的效率参数。

- η_proxy = {eta:.6f} H100-equivalent/MW = {eta/1000:.6f} H100-equivalent/kW。
- 将算力方向的拟合关系代数反解：P_reported（kW）≈ O_proxy / {eta/1000:.6f} ≈ {1000/eta:.6f} O_proxy。此处功率仍为原数据报告功率，非已验证的 IT 功率；下述主模型 R² 衡量算力方向的拟合。
- 95% 配对 bootstrap 区间：[{ci[0]/1000:.6f}, {ci[1]/1000:.6f}] H100-equivalent/kW（10,000 次，固定随机种子）。
- 中心化 R² = 1 − SSE/Σ(O_i−均值)² = {r2(y,pred):.6f}。建议正文引用这个值。
- 非中心化 R² = {result['origin_fit_uncentered_R2']:.6f}，不可与通常带截距回归 R² 混用。
- 带截距对照：O_proxy = {a:.6f} P_reported + ({b:.6f})，R² = {r2(y,a*x+b):.6f}。
- 留一交叉验证 R² = {r2(y,loo_prediction):.6f}；逐个删除样本的 η 范围为 [{loo.min()/1000:.6f}, {loo.max()/1000:.6f}]。
- 直接拟合 P 对 O 与将本拟合代数反解不同：直接过原点回归的 R² = {r2(x,reverse*y):.6f}，隐含 η = {1/reverse/1000:.6f} H100-equivalent/kW。本文主模型是 O 对 P 的回归，不混用两种回归的斜率与 R²。

## 能支持什么结论

若 η 定义为 O_out/P_IT，则 P_IT = O_out/η 是定义的代数改写。真正待检验的假设是不同设施及工况下 η 是否近似固定。横截面线性相关不能证明因果关系、单设施负荷曲线或效率永远不变。

CSV 的 Current H100 equivalents 是容量代理指标，缺少负载率、持续实测吞吐量及精度/任务口径；Current power (MW) 未明确区分设施总功率、IT 功率和实测平均功率。因此本程序估计的是 η_proxy，不能直接宣称得到真实 IT 持续算力效率。不同项目可能共用推算系数，源数据中的 Calculations sheet 和 Selected Sources 需要后续核验，相关性可能部分来自数据生成方法。Bootstrap 假定记录独立，不能覆盖共享来源造成的系统误差。

若验证 P_reported 为 IT 功率且 O_proxy 可作为持续算力，才可条件性使用 η_IT≈η_proxy。若验证功率为设施总功率，且 PUE=k 恒定、持续输出为容量的 u 倍，则 η_IT = u·k·η_proxy；未提供 k、u，不能擅自指定。若各中心 k、u 不同，应逐条修正后重新回归，不可只乘一个统一系数。H100-equivalent 不是 FLOP/s，缺少其定义时不转换。

## 可放入论文的文字

为检验固定效率近似，我们将数据中心的 H100 等效容量作为算力代理指标，对报告功率进行过原点最小二乘拟合。在 {len(x)} 个正值样本中，估计 η_proxy={eta/1000:.4f} H100-equivalent/kW，中心化决定系数 R²={r2(y,pred):.4f}，表明容量与报告功率在样本内具有较强的近似比例关系。该结果为固定效率的简化建模提供经验依据，但由于原始数据缺少持续输出和 IT 功率的统一计量口径，不能将其视为对真实持续算力效率的直接测定。应用 P_IT=O_out/η 前，需统一设备、利用率和功率边界，并对 η 作敏感性分析。

## 运行与文件

安装：`python -m pip install -r requirements.txt`；运行：`python fit_eta.py`。可用 `--csv 路径` 指定新数据。默认使用本目录保留的原始 CSV 副本。图为英文以便论文使用；PNG 为 320 dpi，PDF/SVG 为矢量格式。results.json 保存完整精度与原始文件 SHA-256；sample_audit.csv 保存逐条纳入规则；fitted_data.csv 保存预测值与残差。
'''
    (root / 'README_结果说明.md').write_text(report, encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
