"""Site-specific engineering screens. Missing firm allocations remain unknown."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = Path(__file__).resolve().parent
DATA = HERE.parent


def write(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=rows[0], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def compute():
    # site, stage, technical input, input MW, PUE, IT-area screen, water
    # intensity, published reference (IT MW), scope of calculated result.
    # The intake is an engineering or planning envelope, not firm delivery.
    golden_layout = (930 // 6) * 0.100
    verne_layout = (24000 * 0.5 * 0.5 // 6) * 0.100
    cases = [
        ('us_golden','ESIF upgrade','usable distribution, facility-side reading',6,1.06,golden_layout,.7,10,'upgrade stage conditional'),
        ('is_keflavik','VDC04','module grid allocation unknown',None,1.20,verne_layout,.02,120,'layout ceiling only'),
        ('sg_tanjongkling','Sunview campus','firm grid allocation unknown',None,1.19,None,2.4,150/1.19,'independent capacity unidentified'),
        ('cl_quilicura','Data Luna','illustrative surviving 76 MVA corridor circuit at PF 0.95',76*.95,1.08,None,None,65/1.08,'one-circuit component screen only'),
        ('au_huntingwood','SYD3','planning approval total site consumption envelope',400,1.15,None,1.2,320,'approval envelope only'),
    ]
    rows=[]
    for site,stage,kind,p,k,land,w,target,scope in cases:
        power = None if p is None else p/k
        known = [lim for lim in (power,land) if lim is not None]
        screen = min(known) if known else None
        rows.append(dict(site=site,stage=stage,input_basis=kind,facility_input_MW=p,
            k=k,layout_ceiling_IT=land,scope=scope,conditional_screen_IT=screen,
            benchmark_IT=target,facility_MW_needed=target*k,
            design_water_intensity_L_per_kWh=w,design_water_needed_m3_h=None if w is None else target*w))
    return rows


def figures(rows):
    labels = [r['site'].split('_',1)[1].title() for r in rows]
    for zh in (True,False):
        fonts = {f.name for f in font_manager.fontManager.ttflist}
        plt.rcParams['font.family'] = next(f for f in ['Arial Unicode MS','Noto Sans CJK SC','PingFang SC'] if f in fonts) if zh else 'DejaVu Sans'
        fig, ax = plt.subplots(figsize=(8.5,4.1),layout='constrained')
        names = ['戈尔登','凯夫拉维克','丹戎吉岭','基利库拉','悉尼西部'] if zh else labels
        notes = (['改造阶段','布局上限','供电份额待核','单回路技术情景','审批用电上限'] if zh else
                 ['Upgrade stage','Layout ceiling','Grid allocation unknown','One-circuit screen','Approved site envelope'])
        for i,r in enumerate(rows):
            val=r['conditional_screen_IT']
            if val is not None:
                ax.scatter(val,i,color='#176b72',s=60)
            ax.text(1.02,i,notes[i],va='center',transform=ax.get_yaxis_transform(),fontsize=9)
            ax.scatter(r['benchmark_IT'],i,marker='|',s=160,color='#ae562e',linewidth=2)
        ax.set(yticks=range(5),yticklabels=names,xscale='log',xlim=(4,450),ylim=(4.6,-.6),
               xlabel='IT 功率（MW，对数刻度）' if zh else 'IT power (MW, logarithmic scale)')
        ax.set_title('场址工程条件（圆点）与公开规模（竖线）' if zh else 'Site engineering screens (dots) and public benchmarks (ticks)',loc='left')
        ax.grid(axis='x',alpha=.25)
        ax.spines[['top','right']].set_visible(False)
        fig.savefig(HERE/('五地规划对照.pdf' if zh else 'five_site_benchmarks.pdf'),bbox_inches='tight')
        plt.close(fig)


if __name__=='__main__':
    results=compute()
    write(HERE/'comparison.csv',results)
    for row in results:
        write(DATA/('q1_'+row['site'])/'plan_comparison.csv',[row])
    figures(results)
