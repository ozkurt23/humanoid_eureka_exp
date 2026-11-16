from pathlib import Path
import sys,numpy as np
from scipy.spatial.transform import Rotation
def inspect(file):
    z=np.load(file);p=z['poses'];names=list(z['names']);triggers=[]
    for side in 'LR':
        m=p[:,names.index(side+'v_mount')];b=p[:,names.index(side+'v_pen')]
        xyz=Rotation.from_quat(m[:,[4,5,6,3]]).inv().apply(b[:,:3]-m[:,:3])
        active=(xyz[:,2]<xyz[0,2]-.0068)|(abs(xyz[:,0])>abs(xyz[0,0])+.010)
        onset=np.flatnonzero(active)
        triggers.append(round(int(onset[0])/60,3) if len(onset) else None)
    return triggers
if __name__=='__main__':
    for f in sys.argv[1:]: print(Path(f).name,inspect(f))
