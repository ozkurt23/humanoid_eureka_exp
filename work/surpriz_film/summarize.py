"""Write the timing, support, grip and resumption measurements from completed runs."""
from pathlib import Path
import sys,json
import numpy as np
w=Path(__file__).resolve().parent
sys.path.insert(0,str(w.parent/'surpriz'))
from assess import measure
if __name__=='__main__':
    data=[measure(f) for f in sys.argv[1:]]
    print(json.dumps(data,ensure_ascii=False,indent=2))
