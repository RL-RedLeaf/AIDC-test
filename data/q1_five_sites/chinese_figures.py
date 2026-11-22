"""Localize the same Matplotlib figures and export UTF-8 BOM tables for Excel."""
import csv
import json
import runpy
from pathlib import Path
import matplotlib as mpl
from matplotlib import font_manager as fm
from matplotlib.text import Text
import reproduce as base

NAMES={"Huntingwood · SYD3":"澳大利亚 · 悉尼西部","Keflavík · Verne":"冰岛 · 凯夫拉维克",
       "Tanjong Kling · Meta":"新加坡 · 丹戎吉岭","Quilicura · Google":"智利 · 基利库拉",
       "Golden · ESIF":"美国 · 戈尔登"}
TEXT={"Which resource caps each site?":"五个场址的容量瓶颈","Power":"电力","Water":"取水","Land":"土地",
      "A   Three resource ceilings":"A   三项资源能支撑的容量","B   Binding resource":"B   瓶颈随电网与供水的变化",
      "Base":"基准","Sustainable IT load (MW)":"可持续 IT 负载（MW）","Grid delivery / base":"电网可持续交付功率 / 基准值",
      "Water allocation / base":"可分配水量 / 基准值","Resource ceiling (MW IT, logarithmic scale)":"各项容量上限（MW IT，对数刻度）",
      "A   Solar resource":"A   水平面总辐照量","B   Wind resource":"B   百米高空风速",
      "Month (UTC)":"月份（UTC）","Horizontal irradiation (kWh/m²/day)":"日均辐照量（kWh/m²）",
      "100 m wind speed (m/s)":"月平均风速（m/s）","10–90% across years":"十年间第 10–90 百分位","Median":"十年中位数","2025":"2025 年",
      "Capacity under the site scenario":"三项容量与限制条件","Seasonal resources, 2016–2025":"风光资源的季节变化（2016–2025）",**NAMES}
SCEN={"Grid":"纯电网","Roof PV + storage":"屋顶光伏＋储能","Roof PV + wind + storage":"屋顶光伏＋风机＋储能",
      "Ground PV 10% + storage":"地面光伏（可分配用地的10%）＋储能","Ground PV 50% + storage":"地面光伏（50%）＋储能",
      "Ground PV optimal area + storage":"地面光伏（连续面积最优）＋储能","Gas with guaranteed fuel":"燃气机组（假设燃料充足）"}
FILES={"fig1_capacity":"图1_三项容量与瓶颈","fig2_climate":"图2_风光资源季节变化","fig_global_constraints":"五地容量与瓶颈_中文"}
save_original=base.save

def localize(fig,d,name):
    for ax in fig.axes:
        labels=[item.get_text() for item in ax.get_yticklabels()]
        if labels and all(x in TEXT for x in labels):
            ax.set_yticks(ax.get_yticks(),labels=[TEXT[x] for x in labels])
    for artist in fig.findobj(Text):
        raw=artist.get_text()
        if "  |  " in raw:
            artist.set_text("  ·  ".join(TEXT.get(x,x) for x in raw.split("  |  ")))
        elif raw in TEXT:
            artist.set_text(TEXT[raw])
    save_original(fig,d,FILES[name])

def write_csv(path,header,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)

def build():
    fonts={f.name for f in fm.fontManager.ttflist}
    family=next((x for x in ["Arial Unicode MS","Microsoft YaHei","Noto Sans CJK SC","Hiragino Sans GB","PingFang SC"] if x in fonts),None)
    if not family: raise RuntimeError("请安装思源黑体或 Noto Sans CJK SC 后重跑。")
    mpl.rcParams["font.family"]=[family,"DejaVu Sans"]
    base.save=localize
    # The language variant reuses the same monthly data; the computation script owns its export.
    base.table=lambda *args: None
    summary=[]
    for path in sorted(base.DATA.glob("q1_*/result.json")):
        d=path.parent
        report=json.loads(path.read_text());ext=json.loads((d/"expanded_result.json").read_text())
        m=json.loads((d/"parameters.json").read_text());v={k:z["value"] for k,z in m["parameters"].items()}
        site=report["site"];t,s=base.load_weather(d)
        roof=report["scenarios"][1];limits=[roof[k] for k in base.LIMITS]
        base.charts(d,site,t,s,limits,v,roof["breakdown"]["self_generation_mw"],report["P_max_mw_it"])
        rows=[[NAMES[site],SCEN[r["name"]],r["generation_land_ha"],*[r[k] for k in base.LIMITS],r["P_mw_it"],"、".join(r["binding"])] for r in ext["scenarios"]]
        write_csv(d/"各方案容量对照_中文.csv",["场址","供电配置","发电新增独占用地（ha）","电力上限（MW IT）","取水上限（MW IT）","土地上限（MW IT）","可持续容量（MW IT）","限制条件"],rows)
        ren=max(r["P_mw_it"] for r in ext["scenarios"] if r["name"]!="Gas with guaranteed fuel")
        summary.append([NAMES[site],*limits,report["P_max_mw_it"],"、".join(roof["binding"]),ren,ext["P_max_mw_it"]," / ".join(SCEN[k] for k in ext["winners"])])
    write_csv(base.DATA/"q1_five_sites"/"五地容量对照_中文.csv",["场址","基准供电上限（MW IT）","基准取水上限（MW IT）","基准土地上限（MW IT）","基准可持续容量（MW IT）","基准瓶颈","允许重划土地的可再生方案最高容量（MW IT）","含假想燃机的最高容量（MW IT）","扩展集获胜候选"],summary)
    runpy.run_path(str(Path(__file__).with_name("overview_figure.py")))

if __name__=="__main__":
    build()
