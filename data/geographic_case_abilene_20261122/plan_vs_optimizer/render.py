"""Make the three figures and the four-page student PDF from the saved solver outputs."""
import csv
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap

CASE = Path(__file__).resolve().parent
FIG = CASE / "figures"
DARK, GREEN, GOLD, SLATE, FAINT = "#163342", "#09726B", "#AF561F", "#52717B", "#D9E5E4"
PALE = "#A5D8C9"


def rows(name):
    with (CASE / "results" / name).open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def chart_style():
    command = shutil.which("kpsewhich")
    path = subprocess.check_output([command, "FandolHei-Regular.otf"], text=True).strip() if command else ""
    if path:
        fm.fontManager.addfont(path)
        bold = Path(path).with_name("FandolHei-Bold.otf")
        if bold.is_file():
            fm.fontManager.addfont(str(bold))
        cjk = fm.FontProperties(fname=path).get_name()
    else:
        cjk = "Noto Sans CJK SC"
    plt.rcParams.update({"font.family":["DejaVu Sans",cjk], "font.size":12, "axes.labelcolor":SLATE,
                         "axes.edgecolor":FAINT, "text.color":DARK, "xtick.color":SLATE, "ytick.color":DARK,
                         "axes.spines.top":False, "axes.spines.right":False, "axes.unicode_minus":False,
                         "axes.titleweight":"bold", "axes.titlelocation":"left", "axes.titlepad":13,
                         "figure.facecolor":"white", "axes.facecolor":"white", "savefig.facecolor":"white"})


def save(fig,name):
    fig.savefig(FIG/name,dpi=210,bbox_inches="tight",pad_inches=.12)
    plt.close(fig)


def planned(s):
    raw = rows("plan_limits.csv")[0]
    limits = [float(raw[key]) for key in ("P_L_mw_it","P_W_mw_it","P_E_mw_it")]
    fig, (a,b) = plt.subplots(1,2,figsize=(10.2,3.15),gridspec_kw={"width_ratios":[1.15,1]})
    fig.subplots_adjust(left=.10,right=.97,bottom=.23,top=.82,wspace=.42)
    a.set_title("原规划的三项资源上限",fontsize=14)
    a.barh(range(3), limits,color=[SLATE,PALE,GREEN],height=.48)
    a.set_yticks(range(3),["土地","取水","供电"])
    a.set_xlim(0,1390); a.set_xticks([0,400,800,1200]); a.set_xlabel("可支持的 MW IT")
    a.axvline(s["reference_mw_it"],ls="--",color=GOLD,lw=1.6)
    for i,v in enumerate(limits):
        a.text(v+14,i,f"{v:,.1f}",va="center",size=11)
    a.text(s["reference_mw_it"]-12,-.51,"八栋 824",ha="right",va="top",color=GOLD,size=10)
    a.set_ylim(-.80,2.6);a.spines["left"].set_visible(False);a.tick_params(axis="y",length=0)
    b.set_title(f"{s['plan_resources_mw']-s['reference_mw_it']:.2f} MW 的差额从哪里来",fontsize=14)
    y=[s["reference_mw_it"],s["epoch_power_to_it_mw"],s["plan_resources_mw"]]
    x=np.arange(3); b.plot(x,y,color=SLATE,lw=1.7); b.scatter(x,y,s=73,c=[GOLD,SLATE,GREEN],zorder=3)
    for i,val in enumerate(y):
        b.annotate(f"{val:.2f}",(i,val),xytext=(0,9),textcoords="offset points",ha="center",color=DARK,fontsize=11)
    b.set_xlim(-.35,2.40); b.set_ylim(805,865); b.set_yticks([810,830,850]); b.set_ylabel("MW IT")
    b.set_xticks(x,["Epoch\nIT 参照","阶段设施\n1,154 ÷ k","额定并网\n1,200 ÷ k"])
    b.grid(axis="y",color=FAINT,linewidth=.65);b.set_axisbelow(True)
    save(fig,"plan.png")


def technologies(s):
    allrows={r['option']:r for r in rows('portfolio.csv')}
    terms=[('gas','干冷燃气'),('coal','湿冷煤电'),('pv','光伏加储能'),('wind','风电加储能'),('grid','纯网电')]
    fig,ax=plt.subplots(figsize=(10.1,3.25))
    fig.subplots_adjust(left=.14,right=.80,bottom=.23,top=.92)
    base=float(allrows['grid']['it_mw'])
    for n,(tech,label) in enumerate(terms):
        q=allrows[tech]; v=float(q["it_mw"]); y=4-n
        ax.hlines(y,base,v,color=GREEN,lw=4,alpha=.54)
        ax.scatter(v,y,c=GREEN if tech=='gas' else SLATE,s=66,zorder=4)
        ax.text(v+2.3,y,f"{v:.2f}",va="center",fontsize=11,color=DARK)
        extra=v-base
        ax.text(1.025,y,"参照" if tech=='grid' else f"+{extra:.2f} MW IT",
                transform=ax.get_yaxis_transform(),ha="left",va="center",
                fontsize=11,fontweight="bold" if tech=='gas' else "normal",color=GOLD if tech=='gas' else SLATE)
    ax.text(1.025,4.74,"相对纯网电",transform=ax.get_yaxis_transform(),size=10,color=SLATE)
    ax.axvline(s["reference_mw_it"],ls="--",color=GOLD,lw=1.5)
    ax.text(s["reference_mw_it"],4.66,"原规划 824",color=GOLD,ha="center",fontsize=10)
    ax.axvline(base,ls=":",color=SLATE,lw=1)
    ax.set_yticks(range(5),[x[1] for x in terms[::-1]])
    ax.set_ylim(-.55,4.9); ax.set_xlim(808,1016); ax.set_xticks([820,860,900,940,980])
    ax.set_xlabel("重配后可支持的 MW IT"); ax.tick_params(axis="y",length=0)
    ax.spines["left"].set_visible(False);ax.grid(axis="x",color=FAINT,linewidth=.6)
    ax.set_axisbelow(True);save(fig,"technology.png")


def sensitivities():
    data=[r for r in rows("sensitivity.csv") if r['test']=='grid_water']
    water=sorted({float(r['water_m3_h']) for r in data});grid=sorted({float(r['grid_mw']) for r in data})
    lookup={(float(r['water_m3_h']),float(r['grid_mw'])):r for r in data}
    cmap=LinearSegmentedColormap.from_list("capacity",["#FAF6EA","#D9E8CC","#90C5B5","#3D938E","#165C63"])
    fig,axes=plt.subplots(1,2,figsize=(10.25,3.7),layout="constrained",sharey=True)
    for i,(ax,key,title) in enumerate(zip(axes,["fixed_plan_mw","it_mw"],["保留八栋设备","允许重新配置"])):
        values=np.array([[float(lookup[q,g][key]) for g in grid] for q in water])
        image=ax.imshow(values,origin="lower",vmin=585,vmax=990,cmap=cmap,aspect="auto")
        for j in range(len(water)):
            for k in range(len(grid)):
                v=values[j,k]
                ax.text(k,j,f"{v:.0f}",color="white" if v>835 else DARK,ha="center",va="center",fontsize=12)
        ax.set_title(title,fontsize=14)
        ax.set_xticks(range(len(grid)),[f"{v/1200:.0%}" for v in grid])
        ax.set_yticks(range(len(water)),[f"{q:.0f}" for q in water])
        ax.set_xlabel("额定并网量中可持续交付的比例")
        if i==0:ax.set_ylabel("到场可用水量（m³/h）")
        ax.tick_params(length=0)
    cb=fig.colorbar(image,ax=axes,shrink=.9,pad=.035,ticks=[600,700,800,900,980])
    cb.set_label("MW IT");save(fig,"sensitivity.png")


def pdf(s):
    # The report uses the same result files as the figures. Compile intermediate files in isolation.
    fields={"planMW":(s["plan_deliverable_mw"],0),"resourceMW":(s["plan_resources_mw"],2),
            "bestMW":(s["redesign_mw"],2),"gainPlan":(s["increment_over_plan_mw"],2),
            "gainResource":(s["increment_over_resources_mw"],2),"wholeMW":(s["whole_module_mw"],0),
            "slopeVal":(s["slope"],6),"patchVal":(s["patch_ha"],2),
            "anchoredMW":(s["anchored_extension_mw"],2),"minGrid":(s["plan_min_grid_mw"],2),"phaseHa":(s["phase1_ha"],2)}
    with tempfile.TemporaryDirectory() as temp:
        work=Path(temp)
        (work/"values.tex").write_text("\n".join(f"\\newcommand{{\\{k}}}{{{v:.{n}f}}}" for k,(v,n) in fields.items()),encoding="utf8")
        env=dict(os.environ,TEXINPUTS=str(work)+os.pathsep+str(CASE)+os.pathsep)
        subprocess.run(["latexmk","-silent","-xelatex","-halt-on-error","-interaction=nonstopmode",
                        "-outdir="+str(work),str(CASE/"report.tex")],cwd=CASE,env=env,check=True)
        shutil.copyfile(work/"report.pdf", CASE/"report.pdf")


if __name__=="__main__":
    FIG.mkdir(exist_ok=True)
    s=json.loads((CASE/"results/summary.json").read_text(encoding="utf8"))
    chart_style();planned(s);technologies(s);sensitivities();pdf(s)
