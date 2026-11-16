"""Generate vector figures and LaTeX table rows from recorded measurements."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
HERE = Path(__file__).resolve().parent
OUT = HERE / "sekiller"
OUT.mkdir(exist_ok=True)
data = json.loads((HERE / "olcumler.json").read_text())
events = data["paired"]
walk = np.loadtxt(HERE/"yuruyus.csv", delimiter=",",skiprows=1).T
pens = np.loadtxt(HERE/"kalem.csv",delimiter=",",skiprows=1).T
red,teal,ink,grey="#943B42","#287570","#20282B","#546365"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":8,"text.color":ink,"axes.labelcolor":ink,
                     "axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,
                     "axes.edgecolor":"#9CABA9","xtick.color":grey,"ytick.color":grey,
                     "pdf.fonttype":42,"axes.axisbelow":True})
def tr(v,n=1):return f"{v:.{n}f}"
def style(ax):
    ax.grid(axis="y",color="#D9E0DE",lw=.6)
    ax.tick_params(axis="y",length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_:tr(y,0 if y==int(y) else 1)))
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches="tight",pad_inches=.06)
    plt.close(fig)
starts=np.flatnonzero(np.diff(np.r_[False,np.abs(walk[1])>.002,False])).reshape(-1,2)
fig,axes=plt.subplots(2,1,figsize=(3.58,2.75),sharex=True,layout="constrained")
for ax,y,c,label in zip(axes,walk[1:],(red,teal),("Lateral force (N)","Forward travel (m)")):
    for a,b in starts:ax.axvspan(walk[0][a],walk[0][b],facecolor="#E7EFEB",edgecolor="none")
    ax.plot(walk[0],y,color=c,lw=1.7);style(ax);ax.set_ylabel(label);ax.set_xlim(0,55)
axes[1].set_xlabel("Time (s)");axes[1].set_xticks([0,10,20,30,40,50]);save(fig,"yuk-ve-yuruyus")
fig,ax=plt.subplots(figsize=(3.6,2.05),layout="constrained")
ys=np.arange(5)
for offset,key,c,label in [(-.18,"foot_cm",teal,"Catch step"),(.18,"walk_cm",red,"Walking after release")]:
    v=[e[key] for e in events];bars=ax.barh(ys+offset,v,.30,color=c,label=label)
    ax.bar_label(bars,[tr(a) for a in v],padding=3,fontsize=8.3)
ax.set_yticks(ys,[f"Push {i+1}" for i in ys]);ax.invert_yaxis();ax.set_xlim(0,47)
ax.set_xlabel("Displacement (cm)");ax.grid(axis="x",color="#D9E0DE",lw=.6)
ax.legend(frameon=False,loc="upper right",bbox_to_anchor=(1,1.35),ncol=2,fontsize=8);save(fig,"adimlar")
fig,ax=plt.subplots(figsize=(3.6,1.9),layout="constrained")
a,b=starts[1];ax.axvspan(walk[0][a],walk[0][b],facecolor="#E7EFEB",edgecolor="none")
for sig,c,l in zip(pens[1:],(red,teal),("Left hand","Right hand")):ax.plot(pens[0],sig,c=c,label=l,lw=1.65)
ax.set(xlim=(16,24),ylim=(-40,40),ylabel="Angle (deg)",xlabel="Time (s)")
style(ax);ax.legend(frameon=False,loc="upper right",ncol=2,bbox_to_anchor=(1,1.26));save(fig,"kalemler")
fig,ax=plt.subplots(figsize=(3.62,2.05),layout="constrained")
val=np.array([e["paired"] for e in events])
cm=LinearSegmentedColormap.from_list("paired",["#CB7D77","#FCFAF5","#57A29C"])
ax.imshow(val,aspect="auto",norm=TwoSlopeNorm(vmin=-8,vcenter=0,vmax=40.01),cmap=cm)
ax.set_xticks(range(4),["0.5 s","1.0 s","End of plateau","Release"]);ax.xaxis.tick_top();ax.tick_params(axis="x",labelsize=6.9)
ax.set_yticks(range(5),[f"Push {i+1}" for i in range(5)]);ax.tick_params(length=0)
for (i,j),v in np.ndenumerate(val):ax.text(j,i,("+" if v>=0 else "")+tr(v),ha="center",va="center",fontsize=8.5,fontweight="bold")
for edge in ax.spines.values():edge.set_visible(False)
for i in range(1,5):ax.axhline(i-.5,color="white",lw=2)
for j in range(1,4):ax.axvline(j-.5,color="white",lw=2)
save(fig,"eslenmis")
rows=[]
for r in data['trials']:
    d=r['data'];ident=d['name'][1:]
    if not r['all_ok']:ident=r'\textcolor{accent}{\bfseries '+ident+'}'
    row=[ident,tr(d['seconds'],3),tr(d['forward'],2),f"{r['steps']}/5",f"{r['walks']}/5","Yes" if d["palm"] else "No","Pass" if r["all_ok"] else "Fail"]
    rows.append(" & ".join(row)+r" \\")
(OUT/'kosular.tex').write_text("\n".join(rows)+"\n")

# Signal paths in the deployed model-based controller. The external schedule is
# deliberately drawn outside the observation and candidate-simulation branches.
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, ax = plt.subplots(figsize=(3.76, 1.68))
ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")
def box(x,y,w,h,label,fc,ec):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.06,rounding_size=0.12",lw=.9,edgecolor=ec,facecolor=fc))
    ax.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=7.3,color=ink)
def arrow(points,col=grey):
    for a,b in zip(points[:-2],points[1:-1]):ax.plot([a[0],b[0]],[a[1],b[1]],c=col,lw=.9)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],lw=.9,color=col,arrowstyle="-|>",mutation_scale=9))
box(.10,3.55,3.15,.92,"Independent load\ngenerator","#F5E9E6","#A77671")
box(6.05,3.55,3.77,.92,"Articulated MuJoCo state\n+ two free pens","#ECF0EE","#738782")
box(.10,1.75,3.15,.92,"Dynamics residual\n→ load estimate","#F3F4F3","#899592")
box(.10,.12,3.15,.92,"Candidate footfalls\n+ release hypotheses","#E2EFEB","#55887D")
box(6.05,.12,3.77,.92,"Inverse dynamics\n+ tendon actuation","#E2EFEB","#55887D")
arrow([(3.28,4.02),(6.03,4.02)],red)
arrow([(6.0,3.76),(4.5,3.76),(4.5,2.22),(3.28,2.22)])
arrow([(1.69,1.73),(1.69,1.06)])
arrow([(3.29,.58),(6.03,.58)])
arrow([(8.02,1.08),(8.02,3.51)])
arrow([(6.8,3.52),(6.8,1.06)])
ax.text(6.64,2.24,"pen\npose",fontsize=6.3,va="center",ha="right",color=grey)
ax.text(8.12,2.24,"torques /\ntendons",fontsize=6.3,va="center",ha="left",color=grey)
fig.subplots_adjust(left=.01,bottom=.01,right=.99,top=.99);save(fig,"controller")
matched = np.loadtxt(HERE / "paired-traces.csv", delimiter=",", skiprows=1)
fig,ax=plt.subplots(figsize=(3.62,2.11),layout="constrained")
palette=["#466A8E","#963F42","#33766A","#9A6A32","#68578C"]
for j,(c,stylecode) in enumerate(zip(palette,["-","-","--","-.",":"]),1):
    rows=matched[matched[:,0]==j]
    ax.plot(rows[:,1],rows[:,2],color=c,ls=stylecode,lw=1.45,label=str(j))
    ax.scatter(*rows[-1,1:],s=8,color=c,marker="o")
style(ax);ax.axhline(0,c="#819091",lw=.75)
ax.set(xlabel="Time since onset (s)",ylabel="Pelvis difference (cm)")
ax.legend(frameon=False,loc="upper left",ncol=5,fontsize=7,title="Push",title_fontsize=7,handlelength=1.1,columnspacing=.6,bbox_to_anchor=(0,1.25))
save(fig,"matched-traces")
