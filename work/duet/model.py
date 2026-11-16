from pathlib import Path
import xml.etree.ElementTree as E
import numpy as np, mujoco as mj
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as R
import copy,json
W=Path(__file__).resolve().parent;O=W.parents[1]/'outputs';src=O/'deneyler/models/humanoid_train.xml';hand=O/'ikinci-tur/hand_repaired.xml'
def vec(x):return ' '.join(f'{v:.10g}' for v in x)
def build():
 m=mj.MjModel.from_xml_path(str(src));d=mj.MjData(m);r=E.parse(src).getroot();r.find('option').set('timestep','.002');r.find('compiler').attrib.pop('meshdir')
 a=r.find('actuator');handxml=E.parse(hand).getroot();ten=E.SubElement(r,'tendon');arm={}
 for si,s in enumerate('LR'):
    sign=2*si-1;pre=s+'v_';wname=s+'_wrist_roll';wrist=m.body(wname).id;elb=m.body(f'body_{si*5+3:02d}').id
    names=[f'body_{si*5+i:02d}' for i in range(5)];ix=[m.joint(n).qposadr[0] for n in names]
    def res(q):
        d.qpos[ix]=q;mj.mj_kinematics(m,d);rel=d.xpos[[wrist,elb]]-d.xpos[m.body('body_20').id]
        return np.r_[(rel[0]-[sign*.188,-.33,-.187])*7,(rel[1]-[sign*.285,-.01,-.323])*6,.02*q]
    q=least_squares(res,[0,0,0,-1.7,0],bounds=(-3.1,3.1)).x;res(q);arm.update(zip(names,q))
    z=np.array([-sign*.17,-.94,.29]);z/=np.linalg.norm(z);norm=np.array([-sign*.30,.17,1.]);y=-norm+z*(norm@z);y/=np.linalg.norm(y)
    mat=d.xmat[wrist].reshape(3,3).T@np.column_stack((np.cross(y,z),y,z))
    wr=r.find(f".//body[@name='{wname}']")
    for o in list(wr):
        if o.tag in ('body','geom'):wr.remove(o)
    p=E.SubElement(wr,'body',name=pre+'mount',quat=vec(np.roll(R.from_matrix(mat).as_quat(),1)))
    for el in list(a):
        j=el.get('joint','')
        if j.startswith(s+'_') and any(k in j.lower() for k in ('thumb','ring','index','middle')):a.remove(el)
    def cp(o):
        n=copy.deepcopy(o)
        for e in n.iter():
            for k in ('name','mesh','joint','tendon'):
                if k in e.attrib:e.set(k,pre+e.get(k))
            if e.tag=='mesh':
                e.set('file',str((hand.parent/e.get('file')).resolve()))
                if si:e.set('scale','-1 1 1')
            if si:
                for k in ('pos','fromto','axis'):
                    if k in e.attrib:
                        v=np.fromstring(e.get(k),sep=' ').reshape(-1,3);v*=([1,-1,-1] if k=='axis' else [-1,1,1]);e.set(k,vec(v.ravel()))
            if e.tag=='geom':
                ct=int(e.get('contype','1'));ca=int(e.get('conaffinity','1'))
                e.set('contype',str(ct<<2));e.set('conaffinity',str((ca<<2) | (2 if ct else 0)))
        return n
    for mesh in handxml.find('asset'):r.find('asset').append(cp(mesh))
    for ob in handxml.find('worldbody'):
        if ob.tag=='light' or ob.get('name')=='floor':continue
        if ob.get('name')=='pen':r.find('worldbody').append(cp(ob))
        else:p.append(cp(ob))
    for ob in handxml.find('tendon'):ten.append(cp(ob))
    for ob in handxml.find('actuator'):a.append(cp(ob))
 E.ElementTree(r).write(W/'duet.xml');(W/'arm.json').write_text(json.dumps(arm));m=mj.MjModel.from_xml_path(str(W/'duet.xml'));print(m.nq,m.nv,m.nu)
if __name__=='__main__':build()
