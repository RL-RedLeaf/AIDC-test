"""Build native Q1 inputs, run the repository CLI and export the case figures."""
import csv
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "code"))
from run import calculate

LIMITS = ["P_E_mw_it", "P_W_mw_it", "P_L_mw_it"]
LABELS = ["Power", "Water", "Land"]
COLORS = ["#216581", "#399687", "#BD7747"]
PARAMS = ["grid", "k", "Q", "wue", "A", "A0", "a", "roof_m2"]
UNITS = ["MW", "—", "m³/h", "L/kWh IT", "ha", "ha", "ha/MW IT", "m²"]
plt.rcParams.update({"font.size":10,"font.family":"DejaVu Sans","pdf.fonttype":42,
                     "axes.spines.top":False,"axes.spines.right":False,"axes.labelcolor":"#243744",
                     "axes.titlelocation":"left","axes.titleweight":"bold","axes.edgecolor":"#A2AFB2"})

def table(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def save(fig,d,name):
    fig.savefig(d/(name+".pdf"),bbox_inches="tight")
    fig.savefig(d/(name+".png"),bbox_inches="tight",dpi=300)
    plt.close(fig)

def load_weather(d):
    with gzip.open(d/"weather_2016_2025.csv.gz","rt") as f:
        rows = list(csv.DictReader(f))
    assert len(rows)==87672
    t = np.array([r["time_UTC"] for r in rows],dtype="datetime64[h]")
    assert np.all(np.diff(t)==np.timedelta64(1,"h"))
    series = {k:np.array([float(r[k]) for r in rows]) for k in rows[0] if k!="time_UTC"}
    assert all(np.isfinite(x).all() for x in series.values())
    return t,series

def profile(s):
    ghi=s["shortwave_radiation_W_m2"]
    cell=s["temperature_2m_C"]+(45-20)*ghi/800
    return np.clip(ghi/1000*.85*(1-.0035*(cell-25)),0,1)

def config(site,v,ratios,note):
    installed=v["roof_m2"]*.18/1000
    photovoltaic=dict(name="Roof PV + storage",type="solar",online_year=2030,
                      area_km2=v["roof_m2"]/1e6,density_mw_per_km2=180,
                      generation_land_ha=0,generation_land_required_ha=0,
                      supply_ratios=ratios.round(8).tolist(),dt_hours=1,
                      battery={"C_max_mw":installed*.25,"D_max_mw":installed*.25,
                               "E_usable_mwh":installed,"charge_efficiency":.9,"discharge_efficiency":.9})
    return dict(model="q1",site=site,assessment_year=2030,period_note=note,
                service_level="固定园区、正常运营、逐时持续额定IT负荷。候选假定2030年具备投运条件。",
                P_grid_mw=v["grid"],k_factor=v["k"],
                water={"basis":"withdrawal","source_m3_h":v["Q"],"wue_l_per_kwh_it":v["wue"],
                       "generation_water_l_per_kwh":{"solar":0}},
                land={"effective_ha":v["A"],"fixed_it_ha":v["A0"],"ha_per_mw_it":v["a"]},
                scenarios=[{"name":"Grid","type":"grid","online_year":2030},photovoltaic])

def capacities(v,firm):
    return np.array([(v["grid"]+firm)/v["k"],v["Q"]/v["wue"],max(0,v["A"]-v["A0"])/v["a"]])

def sensitivity(d,v,firm):
    tests=[("Base",{})]
    for key in ["grid","k","Q","wue","A","a"]:
        factors=(.5,.75,1.25,1.5,2) if key!="k" else (.95,1.05,1.15)
        for scale in factors:
            tests.append((f"{key} × {scale:g}",{key:max(1,v[key]*scale) if key=="k" else v[key]*scale}))
    if "golden" in d.name:
        tests += [("Water frozen at historical 9500 m3/year",{"Q":9500/8760}),("6 MW interpreted as IT-side",{"grid":6*v["k"]}),("Cooling tower with heat recovery",{"wue":1.27})]
    if "keflavik" in d.name:
        tests += [("240 MW planned station fully deliverable",{"grid":240}),("Closed-loop water allowance reduced",{"Q":.9}),("Legacy low-density land proxy",{"a":.143748}),("No separate common substation deduction",{"A0":0})]
    if "tanjong" in d.name:
        tests += [(f"Equivalent {mm} mm pipe",{"Q":np.pi*(mm/1000)**2/4*1.5*3600}) for mm in (200,300)]
        tests += [("PUB sector benchmark",{"wue":2.1})]
    if "quilicura" in d.name:
        tests += [("Wells at planned average 15 L/s",{"Q":54}),("2025 actual withdrawal as fixed budget",{"Q":278.2*3785.411784/8760})]
        tests += [(f"2025 mean facility load at {load:.0%} of 65 MW",{"wue":v["wue"]*.75/load}) for load in (.5,1)]
    if "huntingwood" in d.name:
        tests += [("Withdraw 25% of existing main maximum",{"Q":216}),("Framework WUE 0.7",{"wue":.7}),("350 MW IT on same parcel (alternative density)",{"a":8.3/350})]
    out=[]
    for label,changes in tests:
        p=v|changes
        limits=capacities(p,firm)
        out.append([label,*[p[k] for k in PARAMS[:7]],*limits,min(limits),LABELS[np.argmin(limits)]])
    table(d/"sensitivity.csv",["case",*PARAMS[:7],*LIMITS,"P_mw_it","binding"],out)
    return out

def charts(d,name,t,s,limits,v,firm,actual):
    fig,ax=plt.subplots(1,2,figsize=(9.5,3.7),layout="constrained",gridspec_kw={"width_ratios":[1,1.32]})
    fig.suptitle(name+"  |  Capacity under the site scenario",weight="bold",fontsize=14)
    ax[0].barh(range(3),limits,color=COLORS,height=.52)
    ax[0].set(yticks=range(3),yticklabels=LABELS,xlim=(0,max(limits)*1.27),xlabel="Sustainable IT load (MW)")
    ax[0].invert_yaxis()
    for j,x in enumerate(limits): ax[0].text(x+max(limits)*.025,j,f"{x:,.2f}",va="center",fontsize=9)
    ax[0].axvline(actual,color="#182E3A",ls=":",lw=1.3)
    ax[0].set_title("A   Three resource ceilings",fontsize=11)
    x=np.linspace(.25,2,176);y=np.linspace(.25,2,176)
    xx,yy=np.meshgrid(x,y)
    arr=np.stack([(v["grid"]*xx+firm)/v["k"],v["Q"]*yy/v["wue"],np.full_like(xx,limits[2])])
    ax[1].pcolormesh(xx,yy,np.argmin(arr,axis=0),vmin=-.5,vmax=2.5,cmap=ListedColormap(COLORS),shading="auto",alpha=.88,rasterized=True)
    ax[1].plot(1,1,"o",mec="white",mew=1.5,mfc="#172E3A",ms=8)
    ax[1].annotate("Base",(1,1),xytext=(6,6),textcoords="offset points",color="white",weight="bold")
    ax[1].set(xlabel="Grid delivery / base",ylabel="Water allocation / base",xticks=[.5,1,1.5,2],yticks=[.5,1,1.5,2])
    ax[1].set_title("B   Binding resource",fontsize=11)
    save(fig,d,"fig1_capacity")
    years=t.astype("datetime64[Y]").astype(int)+1970
    months=t.astype("datetime64[M]").astype(int)%12+1
    fig,axes=plt.subplots(1,2,figsize=(9.5,3.45),layout="constrained")
    fig.suptitle(name+"  |  Seasonal resources, 2016–2025",weight="bold",fontsize=14)
    raw=[]
    for j,(key,label,col,scale) in enumerate([("shortwave_radiation_W_m2","Horizontal irradiation (kWh/m²/day)","#BC752E",.024),("wind_speed_100m_m_s","100 m wind speed (m/s)","#277889",1)]):
        byyear=np.array([[np.mean(s[key][(years==yr)&(months==m)])*scale for m in range(1,13)] for yr in range(2016,2026)])
        lo,mid,hi=np.percentile(byyear,[10,50,90],axis=0)
        for m in range(12):raw.append([key,m+1,lo[m],mid[m],hi[m],byyear[-1,m]])
        a=axes[j]; x=np.arange(1,13)
        a.fill_between(x,lo,hi,color=col,alpha=.19,label="10–90% across years")
        a.plot(x,mid,color=col,lw=2.3,label="Median")
        a.plot(x,byyear[-1],color="#394956",ls="--",lw=1.2,label="2025")
        a.set(xlim=(1,12),ylim=(0,None),xticks=[1,3,5,7,9,11],xlabel="Month (UTC)",ylabel=label)
        a.set_title(("A   Solar resource","B   Wind resource")[j],fontsize=11)
        a.grid(axis="y",alpha=.18)
        if j==0:a.legend(fontsize=8,frameon=False)
    save(fig,d,"fig2_climate")
    table(d/"fig2_data.csv",["variable","month","p10","median","p90","2025"],raw)

def build(d):
    meta=json.loads((d/"parameters.json").read_text()); site=meta["site"]
    p=meta["parameters"];v={k:r["value"] for k,r in p.items()}
    t,s=load_weather(d); r=profile(s); year=t.astype("datetime64[Y]").astype(int)+1970
    conf=config(site,v,r[year==2025],"2025 ERA5全年8760小时循环，2030条件性建成情景。")
    path=d/"q1.yaml";path.write_text(yaml.safe_dump(conf,sort_keys=False,allow_unicode=True))
    subprocess.run([sys.executable,str(ROOT/"code/run.py"),str(path),"--json",str(d/"result.json")],check=True,stdout=subprocess.DEVNULL)
    report=json.loads((d/"result.json").read_text())
    roof=report["scenarios"][1];firm=roof["breakdown"]["self_generation_mw"]
    limits=capacities(v,firm)
    assert np.allclose(limits,[roof[k] for k in LIMITS])
    assert np.isclose(report["P_max_mw_it"],min(limits))
    # Separate adverse-period check: same hardware and resources; pick the lowest rolling 168-hour PV yield.
    start=int(np.argmin(np.convolve(r,np.ones(168),mode="valid")))
    stress_conf=config(site,v,r[start:start+168],f"十年最低连续168小时光伏出力窗口；首个UTC时间戳{t[start]}")
    stress=calculate(stress_conf)
    item=stress["scenarios"][1]
    table(d/"weather_check.csv",["case","first_utc","last_utc","firm_pv_MW","best_IT_MW","binding_roof"],
          [["2025",str(t[year==2025][0]),str(t[-1]),firm,report["P_max_mw_it"],"+".join(roof["binding"])],
           ["weakest_168h_by_total_pv",str(t[start]),str(t[start+167]),item["breakdown"]["self_generation_mw"],stress["P_max_mw_it"],"+".join(item["binding"])]])
    sens=sensitivity(d,v,firm)
    # The grid and roof branches share identical water/land terms; the roof dominates weakly.
    # Check analytic sensitivity against the native model at an off-base point.
    check=config(site,v|{"Q":v["Q"]*.5,"grid":v["grid"]*1.5},r[start:start+168],"复核")
    assert np.isclose(calculate(check)["P_max_mw_it"],min(capacities(v|{"Q":v["Q"]*.5,"grid":v["grid"]*1.5},item["breakdown"]["self_generation_mw"])))
    charts(d,site,t,s,limits,v,firm,report["P_max_mw_it"])
    b=report["P_max_mw_it"]; grid=report["scenarios"][0]["P_mw_it"]
    bott="、".join(roof["binding"])
    lines=[f"# {site} 第一问",f"2030 条件情景：**{b:.3f} MW IT**，限制资源为**{bott}**。纯电网 {grid:.3f} MW IT；全年光储可靠增供 {firm:.5f} MW（设施侧）。获胜候选：{', '.join(report['winners'])}。","## 三项上限（MW IT）","| 供电配置 | 供电 | 取水 | 土地 | 可持续容量 |","|---|---:|---:|---:|---:|"]
    for row in report["scenarios"]:
        lines.append("| "+row["name"]+" | "+" | ".join(f"{row[k]:.4f}" for k in LIMITS+["P_mw_it"])+" |")
    lines+=["","## 输入、依据与不确定性","","| 参数 | 数值 | 证据身份 | 口径与来源 |","|---|---:|---|---|"]
    for k,u in zip(PARAMS,UNITS):
        a=p[k];links=" ".join("[来源]("+url+")" for url in a["source"].split(" ; "))
        lines.append(f"| {k} | {v[k]:.5g} {u} | {a['status']} | {a['rationale']} {links} |")
    lines+=["","## 什么变化会改变结论",f"保持其余参数不变，要达到另外两项中较低的上限：电网需 {max(0,min(limits[1:])*v['k']-firm):.2f} MW，取水需 {min(limits[0],limits[2])*v['wue']:.2f} m³/h，有效用地需 {v['A0']+min(limits[:2])*v['a']:.3f} ha。这三个阈值分别单独计算。",
            "", "| 专项情景 | 容量 MW IT | 限制资源 |","|---|---:|---|"]
    cn={"Power":"电力","Water":"取水","Land":"土地"}
    for row in sens:
        if " × " not in row[0] and row[0]!="Base":
            lines.append(f"| {row[0]} | {row[-2]:.3f} | {cn[row[-1]]} |")
    lines+=["",f"十年最低连续七天光伏总出力窗口从 {t[start]} UTC 起；独立循环复算得 {stress['P_max_mw_it']:.4f} MW IT。这是一个弱光压力情景，未与跨年枯水同时优化。", "",
            "## 图与复算","图1左为三个资源上限，点线标出联合容量；右为固定土地、设备和冷却参数时的电网—供水瓶颈分区，颜色对应左图。图2为十年各月资源分布，风速用于描述资源背景。两图均附矢量 PDF 及 300 dpi PNG。",
            "",f"在仓库根目录执行 `python code/run.py data/{d.name}/q1.yaml --json /tmp/{d.name}_result.json`。设计假设、光储换算和完整复算见[五地计算说明](../q1_five_sites/README.md)。"]
    (d/"README.md").write_text("\n".join(lines)+"\n")
    print(site,limits,b,bott,flush=True)
    return [site,grid,firm,*limits,b,bott,", ".join(report["winners"]),stress["P_max_mw_it"]]

if __name__=="__main__":
    rows=[build(p.parent) for p in sorted(DATA.glob("q1_*/parameters.json"))]
    table(DATA/"q1_five_sites"/"comparison.csv",["site","grid_only_MW_IT","firm_roof_MW",*LIMITS,"maximum_MW_IT","binding","winners","weak_week_MW_IT"],rows)
