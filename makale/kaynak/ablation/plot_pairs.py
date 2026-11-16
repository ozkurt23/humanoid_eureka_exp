#!/usr/bin/env python3
"""Draw the paired ablation outcomes and the prespecified historical example."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('results',type=Path)
p.add_argument('enabled',type=Path,help='z714.npz')
p.add_argument('disabled',type=Path,help='off-714.npz')
p.add_argument('out',type=Path)
a=p.parse_args()
rows=json.loads(a.results.read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.labelsize':8,'xtick.labelsize':7,
                     'ytick.labelsize':7,'axes.spines.top':False,'axes.spines.right':False,
                     'axes.linewidth':.65,'pdf.fonttype':42,'ps.fonttype':42})
fig=plt.figure(figsize=(7.1,3.35),layout='constrained')
grid=fig.add_gridspec(2,2,width_ratios=[1.02,1.2],hspace=.13,wspace=.07)
left=fig.add_subplot(grid[:,0]);width=fig.add_subplot(grid[0,1]);landing=fig.add_subplot(grid[1,1])
colors={'on':'#17665c','off':'#ae4b27'}
positions=[0,1.3,2.6,3.9]
labels=['Task','Body','Fingers','All steps']
for j,row in enumerate(rows):
    for col,key in enumerate(['joint_success','body','fingertip','recovering_steps']):
        for arm,dx,mk in [('on',-.16,'o'),('off',.16,'s')]:
            v=row[arm][key]
            ok=(v==5) if key=='recovering_steps' else bool(v)
            left.scatter(positions[col]+dx,j,s=17,marker=mk,linewidth=.8,edgecolor=colors[arm],
                         facecolor=colors[arm] if ok else 'white',zorder=3)
left.axhline(3.5,color='.8',lw=.6);left.axhline(8.5,color='.8',lw=.6)
left.set_yticks(np.arange(len(rows)),[r['seed'] for r in rows])
left.invert_yaxis();left.set_xlim(-.55,4.45);left.set_xticks(positions,labels);left.set_ylabel('Schedule')
left.set_xlabel('Filled = criterion met',labelpad=3)
left.set_title('(a) Matched outcomes',loc='left',fontweight='semibold',fontsize=9)
for arm,path in [('off',a.disabled),('on',a.enabled)]:
    with np.load(path) as z:
        p60=z['poses'];names=z['names'].tolist()
        step=np.abs(p60[:,names.index('R_ankle_roll'),0]-p60[:,names.index('L_ankle_roll'),0])*100
        m=z['metrics']; t=m[:,0]; t60=np.arange(len(p60))/60
        style='-' if arm=='on' else '--'
        width.plot(t60,step,style,color=colors[arm],lw=1.1)
        # Signed maximum among qualified, genuinely unloaded and lifted landings.
        # Landing values are saved by analyze_pairs alongside the compound score.
        row = next(t for t in rows if t['seed']==714)
        distance = row[arm]['signed_qualified_landing_cm']
        positions = np.arange(1,len(distance)+1)+(-.13 if arm=='on' else .13)
        landing.bar(positions,distance,.23,color=colors[arm],alpha=.9)
        if arm=='on':
            force=np.abs(z['ticks'][:,-1])>.002
            for first,last in np.flatnonzero(np.diff(np.r_[False,force,False])).reshape(-1,2):
                width.axvspan(t[first],t[last-1],color='#a4a5a6',alpha=.21,lw=0,zorder=0)
width.set_title('(b) Historical schedule 714',loc='left',fontweight='semibold',fontsize=9)
width.set_xlim(36,55);width.set_xticks([36,40,44,48,52,55]);width.set_xlabel('Simulation time (s)')
width.set_ylabel('Ankle span (cm)')
landing.set_title('(c) Qualified lateral landings · schedule 714',loc='left',fontweight='semibold',fontsize=8.5)
landing.axhline(0,color='.4',lw=.7);landing.axhline(3,color='.5',lw=.65,ls=':')
landing.set_xticks(range(1,6));landing.set_ylabel('Downwind (cm)');landing.set_xlabel('Push number')
leg=[Line2D([],[],color=colors['on'],lw=1.2,marker='o',markersize=3.5,label='Enabled'),
     Line2D([],[],color=colors['off'],linestyle='--',lw=1.2,marker='s',markersize=3.5,label='Disabled')]
left.legend(handles=leg,loc='upper center',bbox_to_anchor=(.5,-.11),frameon=False,fontsize=7,ncol=2,handlelength=1.6,columnspacing=1)
for ax in [width,landing]:ax.grid(axis='x',color='.9',lw=.5);ax.set_axisbelow(True)
a.out.parent.mkdir(parents=True,exist_ok=True)
fig.savefig(a.out.with_suffix('.pdf'),bbox_inches='tight',pad_inches=.025)
fig.savefig(a.out.with_suffix('.png'),dpi=200,bbox_inches='tight',pad_inches=.025)
