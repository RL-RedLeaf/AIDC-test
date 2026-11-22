"""Export auxiliary chart and sensitivity tables with Chinese headers and scenario names."""
import csv
from pathlib import Path
from chinese_figures import write_csv

DATA=Path(__file__).resolve().parents[1]
VAR=dict(grid="电网功率",k="设施倍率",Q="可用取水流量",wue="取水强度",A="有效用地",a="单位IT用地")
TEST={"Base":"基准","Water frozen at historical 9500 m3/year":"年度取水冻结在历史9500立方米","6 MW interpreted as IT-side":"6 MW按IT侧解读",
      "Cooling tower with heat recovery":"热回收配冷却塔","240 MW planned station fully deliverable":"规划240 MW全部可持续交付",
      "Closed-loop water allowance reduced":"闭式冷却配水缩减","Legacy low-density land proxy":"较低密度的用地代理","No separate common substation deduction":"共享变电站用地不单列",
      "Equivalent 200 mm pipe":"等效管径200毫米","Equivalent 300 mm pipe":"等效管径300毫米","PUB sector benchmark":"采用新加坡公用事业局行业基准",
      "Wells at planned average 15 L/s":"两井按设计平均15升/秒供水","2025 actual withdrawal as fixed budget":"以2025全年取水实绩作为固定预算",
      "2025 mean facility load at 50% of 65 MW":"由2025平均负载为65 MW的50%反推取水强度",
      "2025 mean facility load at 100% of 65 MW":"由2025平均负载为65 MW的100%反推取水强度",
      "Withdraw 25% of existing main maximum":"取既有主管最大流量的25%","Framework WUE 0.7":"取水强度取框架低值0.7",
      "350 MW IT on same parcel (alternative density)":"同地块可容纳350 MW IT的布局"}
def local_case(name):
    if name in TEST:return TEST[name]
    key,factor=name.split(" × ")
    return VAR[key]+" × "+factor

if __name__=="__main__":
    for d in DATA.glob("q1_*/parameters.json"):
        d=d.parent
        with (d/"sensitivity.csv").open() as f:
            rows=list(csv.reader(f))[1:]
        for r in rows:
            r[0]=local_case(r[0])
            r[-1]={"Power":"电力","Water":"取水","Land":"土地"}[r[-1]]
        write_csv(d/"敏感性分析_中文.csv",["情景","电网功率 MW","设施倍率","可用取水 m³/h","取水强度 L/kWh IT","有效用地 ha","固定设施用地 ha","单位IT用地 ha/MW","供电上限 MW IT","取水上限 MW IT","土地上限 MW IT","可持续容量 MW IT","限制资源"],rows)
        with (d/"weather_check.csv").open() as f:rows=list(csv.reader(f))[1:]
        rows[0][0]="2025全年";rows[1][0]="十年光伏总出力最低的连续七天"
        write_csv(d/"弱光压力测试_中文.csv",["时间窗口","起始时间 UTC","结束时间 UTC","光储可靠增供 MW","最高IT容量 MW","光储方案瓶颈"],rows)
        with (d/"fig2_data.csv").open() as f:rows=list(csv.reader(f))[1:]
        for r in rows:r[0]={"shortwave_radiation_W_m2":"日均水平面辐照 kWh/m²","wind_speed_100m_m_s":"百米平均风速 m/s"}[r[0]]
        write_csv(d/"图2数据_中文.csv",["指标","月份","第10百分位","中位数","第90百分位","2025年"],rows)
