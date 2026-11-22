"""Optional land reallocation and fuel-guaranteed equipment cases, using the same native Q1 model."""
import sys
import json
import subprocess
import numpy as np
import yaml
from reproduce import DATA, ROOT, LIMITS, load_weather, profile, config, table, save, plt

WIND_URL="https://www.nps100.com/wp/wp-content/uploads/2022/10/brochure-NPS-100C-24_ed2019_light_ENG.pdf"

def battery(mw):
    return dict(C_max_mw=mw*.25,D_max_mw=mw*.25,E_usable_mwh=mw,
                charge_efficiency=.9,discharge_efficiency=.9)

def extended(d):
    m=json.loads((d/"parameters.json").read_text());v={k:a["value"] for k,a in m["parameters"].items()}
    t,s=load_weather(d); ix=t.astype("datetime64[Y]").astype(int)+1970==2025
    pv=profile(s)[ix]
    c=config(m["site"],v,pv,"2025全年逐时循环；2030备选设备均为假设可投运的场地重划方案。")
    water=c["water"]
    water["generation_water_l_per_kwh"].update(combined_battery=0,gas=.02)
    choices=c["scenarios"]; available=v["A"]-v["A0"]
    if "golden" not in d.name:
        # PV production and battery ratings scale together, so the LP firm MW scales
        # linearly with area. At fixed water budget the minimum of three lines
        # peaks where electricity first reaches the water or land ceiling.
        base=json.loads((d/"result.json").read_text())
        roof_firm=base["scenarios"][1]["breakdown"]["self_generation_mw"]
        slope=roof_firm/(v["roof_m2"]*.00018)/3.602/v["k"]
        e0=v["grid"]/v["k"]
        a_star=max(0,min(available,(available/v["a"]-e0)/(slope+1/v["a"]),
                         (v["Q"]/v["wue"]-e0)/slope if slope else 0))
        layouts=[("Ground PV 10% + storage",available*.1),("Ground PV 50% + storage",available*.5)]
        if a_star>1e-7:
            layouts.append(("Ground PV optimal area + storage",a_star))
        for label,a in layouts:
            mw=a/3.602
            choices.append(dict(name=label,type="solar",online_year=2030,
               generation_land_ha=a,area_km2=a/100,density_mw_per_km2=100/3.602,
               supply_ratios=pv.round(8).tolist(),dt_hours=1,battery=battery(mw)))
        if available>=2.85:
            # Interpolate speed linearly in log(height) between the two ERA5 reference heights.
            wind=s["wind_speed_10m_m_s"][ix]+np.log(3.7)/np.log(10)*(s["wind_speed_100m_m_s"][ix]-s["wind_speed_10m_m_s"][ix])
            curve=[0,0,0,1.2,7.2,14.5,24.7,37.9,58.7,74.8,85.1,90.2,94.7,95.3,95.1,94.2,92.9,91.2,88.9,87.1,84.1,81.3,78.6,76.1,74.3,71.7]
            out=np.minimum(95,np.interp(wind,np.arange(26),curve))/1000
            out[(wind<3.5)|(wind>=25)]=0
            roof_mw=v["roof_m2"]*.00018;mw=roof_mw+.095
            choices.append(dict(name="Roof PV + wind + storage",type="combined_battery",online_year=2030,
               generation_land_required_ha=2.85,generation_land_ha=2.85,installed_mw=mw,
               supply_series_mw=(pv*roof_mw+out).round(9).tolist(),dt_hours=1,battery=battery(mw)))
        if available>=10:
            choices.append(dict(name="Gas with guaranteed fuel",type="gas",online_year=2030,units=1,unit_net_mw=100,
                                generation_land_ha=10,unit_land_ha=10,gas_supply_adequate=True))
    path=d/"expanded.yaml"
    path.write_text(yaml.safe_dump(c,sort_keys=False,allow_unicode=True))
    subprocess.run([sys.executable,str(ROOT/"code/run.py"),str(path),"--json",str(d/"expanded_result.json")],check=True,stdout=subprocess.DEVNULL)
    report=json.loads((d/"expanded_result.json").read_text()); rows=report["scenarios"]
    for row in rows: assert np.isclose(row["P_mw_it"],min(row[k] for k in LIMITS))
    renew=max(r["P_mw_it"] for r in rows if r["name"]!="Gas with guaranteed fuel")
    best=max(rows,key=lambda r:r["P_mw_it"])
    lines=[f"# {m['site']} · 场地重划压力测试","",f"允许重划用地后，电网与可再生候选的最高容量为 **{renew:.3f} MW IT**；把可容纳且燃料充足的假想燃机也列入后，最高为 **{best['P_mw_it']:.3f} MW IT**。","",
    "| 候选 | 发电新增用地 ha | 电力上限 | 取水上限 | 土地上限 | 联合容量 MW IT | 瓶颈 |","|---|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        lines.append("| "+r["name"]+" | "+f"{r['generation_land_ha']:.3f} | "+" | ".join(f"{r[k]:.4f}" for k in LIMITS+["P_mw_it"])+" | "+"、".join(r["binding"])+" |")
    lines+=["","Golden按既有建筑模块评估。其余场址检验10%、50%及理论最优连续面积。因光伏与储能按面积同比例缩放，可靠增供亦同比例；取供电上限首次触及水或土地上限的面积，并以原程序逐时复算。最优新增用地为零时由纯电网代表。地面光伏用地强度参照仓库的3.602 ha/MWac。小风机与屋顶光伏共用电池；风机额定95 kW、占地按30 ha/MW折2.85 ha，37 m轮毂风速由10 m、100 m逐时风速按高度对数插值，再查厂家功率曲线。取3.5 m/s切入、25 m/s切出，电池功率为合计装机的25%、时长4 h。均假定场地可连续布置，尚未核实机场净空、噪声、屋面承重和审批。模型采用厂商标准空气密度曲线。 [风机规格]("+WIND_URL+")",
    "","燃机按仓库的100 MW净功率、10 ha整机、干冷耗水量级0.02 L/kWh，保守按同值作取水代理；水仅按实际调用计。缺少燃气管道、燃料合同和排放许可。系检验输入边界的反事实，尤其冰岛不能据此声称能取得燃气。燃煤参考模块需20 ha，五地均放不下；水电缺可用水头、流量与受许河段。各候选分别占地，不合并不同方案的上限。 [原仓库设备依据](../geographic_case_abilene_20261122/10_geographic_case_report.md)"]
    (d/"扩展候选.md").write_text("\n".join(lines)+"\n")
    return [m["site"],rows[0]["P_mw_it"],renew,best["P_mw_it"],best["name"],"+".join(best["binding"])]

if __name__=="__main__":
    rows=[extended(p.parent) for p in sorted(DATA.glob("q1_*/parameters.json"))]
    table(DATA/"q1_five_sites"/"expanded_comparison.csv",["site","grid_MW_IT","best_nonfuel_MW_IT","best_including_hypothetical_gas_MW_IT","first_winner","binding"],rows)
    print(rows,flush=True)
