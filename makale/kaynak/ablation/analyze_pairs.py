#!/usr/bin/env python3
"""Evaluate same-seed conditional restart ablation using archived 500/60-Hz arrays."""
import argparse
import csv
import json
from pathlib import Path
import sys
import numpy as np

SEED_GROUPS = {
    'development (fixed loads)': [714,715,716,727],
    'development (random loads)': [905,924,1042,1051,1052],
    'held-out schedules': list(range(1071,1077)),
}
def criteria(d):
    steps = sum(any(x['shift_cm']>=3 and x['lift_cm']>=.5 for x in e['landings']) for e in d['events'])
    walking = sum(e['walk_cm']>=2 for e in d['events'])
    body = d['seconds']==55 and d['ground']==0 and len(d['events'])==5
    pen = bool(d['palm']==0 and min(d['opposed'])>=98 and all(min(e['shaft_deg'])>=15 for e in d['events']))
    return {
        'joint_success': bool(body and pen and steps==walking==5),
        'signed_qualified_landing_cm':[max((s['shift_cm'] for s in e['landings'] if s['lift_cm']>=.5),default=None) for e in d['events']],
        'duration_s': float(d['seconds']), 'forward_m':d['forward'],
        'body':bool(body),'fingertip':pen,'recovering_steps':int(steps),'forward_resumptions':int(walking),
        'opposed_left_percent': d['opposed'][0], 'opposed_right_percent': d['opposed'][1],
        'palm_contact':bool(d['palm']),'nonfoot_floor_contact':bool(d['ground']),
    }

def pair(on, off, measure):
    res = {'on':criteria(measure(on)),'off':criteria(measure(off))}
    with np.load(on) as a, np.load(off) as b:
        assert a.files==b.files and np.array_equal(a['names'],b['names'])
        n=min(len(a['ticks']),len(b['ticks']))
        force=a['ticks'][:n,-1]; assert np.array_equal(force,b['ticks'][:n,-1])
        onset=np.flatnonzero(np.abs(force)>0)[0];t=a['metrics'][:,0]
        mismatch=np.flatnonzero(np.any(a['metrics'][:n]!=b['metrics'][:n],axis=1) | np.any(a['ticks'][:n]!=b['ticks'][:n],axis=1))
        first=int(mismatch[0]) if len(mismatch) else n
        assert first>=onset
        identical=all(np.array_equal(a[k],b[k]) for k in a.files)
        res.update({'first_push_s':float(t[onset]),'common_force_samples':n,'identical_500hz_prefix_samples':first,
                    'first_logged_difference_s':None if first==n else float(t[first]),'identical_entire_trace':identical})
    return res

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--on',required=True,type=Path,help='Full-archive work/parmak_denge containing z*.npz')
    p.add_argument('--off',required=True,type=Path,help='Directory of off-*.npz and off-*.log')
    p.add_argument('--code',required=True,type=Path,help='Published work/parmak_denge with assess.py')
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    sys.path.insert(0,str(args.code.resolve()))
    from assess import measure
    rows=[]
    for group,seeds in SEED_GROUPS.items():
        for seed in seeds:
            row=pair(args.on/f'z{seed}.npz',args.off/f'off-{seed}.npz',measure)
            row.update(seed=seed,group=group)
            rows.append(row)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'paired-results.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (args.output/'paired-results.csv').open('w',newline='') as f:
        writer=None
        for row in rows:
            merged={k:v for k,v in row.items() if k not in ['on','off']}
            for arm in ('on','off'):merged.update({arm+'_'+k:v for k,v in row[arm].items()})
            if writer is None:
                writer=csv.DictWriter(f,fieldnames=merged.keys());writer.writeheader()
            writer.writerow(merged)
    for group in list(SEED_GROUPS)+['all']:
        r=[row for row in rows if group=='all' or row['group']==group]
        cells=[sum(row['on']['joint_success']==a and row['off']['joint_success']==b for row in r) for a,b in [(1,1),(1,0),(0,1),(0,0)]]
        print(group, len(r), 'both/on-only/off-only/neither',cells,'identical',sum(i['identical_entire_trace'] for i in r))
