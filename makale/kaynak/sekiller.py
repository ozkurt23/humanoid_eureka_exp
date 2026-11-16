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
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,"text.color":ink,"axes.labelcolor":ink,
                     "axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,
                     "axes.edgecolor":"#9CABA9","xtick.color":grey,"ytick.color":grey,
                     "pdf.fonttype":42,"axes.axisbelow":True})
def tr(v,n=1):return f"{v:.{n}f}".replace(".",",")
def style(ax):
    ax.grid(axis="y",color="#D9E0DE",lw=.6)
    ax.tick_params(axis="y",length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y,_:tr(y,0 if y==int(y) else 1)))
def save(fig,name):
    fig.savefig(OUT/(name+'.pdf'),bbox_inches="tight",pad_inches=.06)
    plt.close(fig)
starts=np.flatnonzero(np.diff(np.r_[False,np.abs(walk[1])>.002,False])).reshape(-1,2)
fig,axes=plt.subplots(2,1,figsize=(7.1,2.52),sharex=True,layout="constrained")
for ax,y,c,label in zip(axes,walk[1:],(red,teal),("Yanal kuvvet (N)","İleri yol (m)")):
    for a,b in starts:ax.axvspan(walk[0][a],walk[0][b],facecolor="#E7EFEB",edgecolor="none")
    ax.plot(walk[0],y,color=c,lw=1.7);style(ax);ax.set_ylabel(label);ax.set_xlim(0,55)
axes[1].set_xlabel("Zaman (s)");axes[1].set_xticks([0,10,20,30,40,50,55]);save(fig,"yuk-ve-yuruyus")
fig,ax=plt.subplots(figsize=(7,1.80),layout="constrained")
ys=np.arange(5)
for offset,key,c,label in [(-.18,"foot_cm",teal,"İtme yönünde basış"),(.18,"walk_cm",red,"Sonraki ileri yol")]:
    v=[e[key] for e in events];bars=ax.barh(ys+offset,v,.30,color=c,label=label)
    ax.bar_label(bars,[tr(a) for a in v],padding=3,fontsize=8.3)
ax.set_yticks(ys,[f"İtme {i+1}" for i in ys]);ax.invert_yaxis();ax.set_xlim(0,45)
ax.set_xlabel("Yer değiştirme (cm)");ax.grid(axis="x",color="#D9E0DE",lw=.6)
ax.legend(frameon=False,loc="upper right",bbox_to_anchor=(1,1.35),ncol=2,fontsize=8);save(fig,"adimlar")
fig,ax=plt.subplots(figsize=(7.0,1.9),layout="constrained")
a,b=starts[1];ax.axvspan(walk[0][a],walk[0][b],facecolor="#E7EFEB",edgecolor="none")
for sig,c,l in zip(pens[1:],(red,teal),("Sol el","Sağ el")):ax.plot(pens[0],sig,c=c,label=l,lw=1.65)
ax.set(xlim=(16,24),ylim=(-40,40),ylabel="Bileğe göre eğim (°)",xlabel="Zaman (s)")
style(ax);ax.legend(frameon=False,loc="upper right",ncol=2,bbox_to_anchor=(1,1.26));save(fig,"kalemler")
fig,ax=plt.subplots(figsize=(6.6,2.22),layout="constrained")
val=np.array([e["paired"] for e in events])
cm=LinearSegmentedColormap.from_list("paired",["#CB7D77","#FCFAF5","#57A29C"])
ax.imshow(val,aspect="auto",norm=TwoSlopeNorm(vmin=-8,vcenter=0,vmax=40.01),cmap=cm)
ax.set_xticks(range(4),["0,5 s","1,0 s","Tepe yükü sonu","Kuvvetin sonu"]);ax.xaxis.tick_top()
ax.set_yticks(range(5),[f"İtme {i+1}" for i in range(5)]);ax.tick_params(length=0)
for (i,j),v in np.ndenumerate(val):ax.text(j,i,("+" if v>=0 else "")+tr(v),ha="center",va="center",fontweight="bold")
for edge in ax.spines.values():edge.set_visible(False)
for i in range(1,5):ax.axhline(i-.5,color="white",lw=2)
for j in range(1,4):ax.axvline(j-.5,color="white",lw=2)
save(fig,"eslenmis")
rows=[]
for r in data['trials']:
    d=r['data'];ident=d['name'][1:]
    if not r['all_ok']:ident=r'\textcolor{accent}{\bfseries '+ident+'}'
    row=[ident,tr(d['seconds'],3),tr(d['forward'],2),f"{r['steps']}/5",f"{r['walks']}/5","Var" if d["palm"] else "Yok","Geçti" if r["all_ok"] else "Eksik"]
    rows.append(" & ".join(row)+r" \\")
(OUT/'kosular.tex').write_text("\n".join(rows)+"\n")
