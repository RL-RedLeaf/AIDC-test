"""Render the comparison using the native JSON products (no model assumptions here)."""
from reproduce import DATA, LABELS, COLORS, plt, save
from matplotlib.lines import Line2D
import json

cases=[]
for d in DATA.glob("q1_*/result.json"):
    report=json.loads(d.read_text())
    base=report["scenarios"][1]
    cases.append((report["P_max_mw_it"],report["site"],base))
cases.sort(reverse=True)
fig,ax=plt.subplots(figsize=(8.2,3.9),layout="constrained")
keys=["P_E_mw_it","P_W_mw_it","P_L_mw_it"]
markers=["o","s","^"]
for i,(capacity,name,base) in enumerate(cases):
    limits=[base[k] for k in keys]
    ax.plot([min(limits),max(limits)],[i,i],color="#C5CFD0",lw=2,zorder=0)
    for j,x in enumerate(limits):
        ax.scatter(x,i,s=65,c=COLORS[j],marker=markers[j],zorder=3,edgecolors="white",linewidth=.65)
    ax.annotate(f"{capacity:.2f}",(capacity,i),xytext=(-7,-3),textcoords="offset points",ha="right",weight="bold",fontsize=9)
ax.set_xscale("log");ax.set_xlim(2.6,1100)
ax.set_xticks([5,10,20,50,100,200,500,1000],labels=["5","10","20","50","100","200","500","1,000"])
ax.set_yticks(range(len(cases)),labels=[v[1] for v in cases]);ax.set_ylim(len(cases)-.5,-.7)
ax.set_xlabel("Resource ceiling (MW IT, logarithmic scale)")
ax.grid(axis="x",which="major",alpha=.16)
ax.set_title("Which resource caps each site?",fontsize=15,pad=15)
fig.legend(handles=[Line2D([],[],marker=m,color=c,ls="",label=l) for c,m,l in zip(COLORS,markers,LABELS)],
           loc="outside upper right",ncol=3,frameon=False)
save(fig,DATA/"q1_five_sites","fig_global_constraints")
