"""Report specific failure conditions, including stance sliding and object drops."""
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'surpriz'))
from assess import measure
def summarize(file):
    a=measure(file)
    def foot(e):
        steps=[s['shift_cm'] for s in e['landings'] if s['lift_cm']>=.5]
        return max([0]+steps)
    events=a['events']
    full=(a['seconds']==55 and len(events)==5)
    grip=(a['palm']==0 and a['ground']==0 and min(a['opposed'])>98
          and min(min(e['shaft_deg']) for e in events)>15)
    return a['name'],full,grip, [round(foot(e)) for e in events], [round(e['walk_cm']) for e in events], [round(e['roll_range_deg']) for e in events]
if __name__=='__main__':
    for f in sys.argv[1:]:
        print(*summarize(f))
