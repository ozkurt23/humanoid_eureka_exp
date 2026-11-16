from model import *
import sys,os
sys.path.insert(0,str(O/'hareket'))
from hand_flow import initial
PUSH=[(6.55,28),(16.80,-42),(28.22,56),(39.70,-70),(47.12,98)]
if os.environ.get('TIMES'):
 PUSH=list(zip(map(float,os.environ['TIMES'].split(',')),[28,-42,56,-70,98]))
from wrench import make,control
if os.environ.get("FORCES"):
 PUSH=list(zip([a for a,_ in PUSH],map(float,os.environ["FORCES"].split(","))))
class Grip:
 def __init__(self,m,d):
    self.m=m;self.d=d;self.data=[];self.comp=[]
    h,st,neutral,_=initial(162000);mj.mj_setState(h.m,h.d,st,mj.mjtState.mjSTATE_INTEGRATION)
    self.co=np.load(O/'hareket/demo_tendons.npy');self.neutral=neutral
    mj.mj_forward(h.m,h.d)
    oldbias=h.d.qfrc_bias[:11].copy()
    preload=np.zeros((3,11));ny=np.zeros(11);target=h.d.qpos[11:14].copy()
    for c in h.d.contact:
        if h.barrel not in (c.geom1,c.geom2):continue
        g=c.geom1+c.geom2-h.barrel
        if 'silicone_pad' not in h.m.geom(g).name:continue
        jac=np.zeros((3,h.m.nv));mj.mj_jac(h.m,h.d,jac,None,c.pos,h.m.geom_bodyid[g])
        normal=c.frame[:3]*(1 if g==c.geom1 else -1)
        ids=np.flatnonzero(np.max(np.abs(jac[:,:11]),axis=0)>1e-8)
        jj=jac[:,ids];corr=jj.T@np.linalg.solve(jj@jj.T+1e-4*np.eye(3),[0,1,0])
        ny[ids]=corr
        preload[['Index','Ring','Thumb'].index(h.m.geom(g).name.split('_')[0])]+=jac[:,:11].T@normal
    self.par=np.array(json.loads((W/os.environ.get('CONFIG','first.json')).read_text())[int(os.environ.get('CAND','0'))][-1])
    self.wmap=make(h);self.ny=ny;self.start=target.copy();self.start[0]+=float(os.environ.get('XC',.010));self.oldbias=oldbias;self.preload=preload
    for si,s in enumerate('LR'):
        pre=s+'v_';j=[m.joint(pre+h.m.joint(i).name).qposadr[0] for i in range(11)]
        ac=[m.actuator(pre+h.m.joint(i).name).id for i in range(11)]
        mount=m.body(pre+'mount').id;pen=m.body(pre+'pen').id;adr=m.jnt_qposadr[m.body_jntadr[pen]]
        d.qpos[j]=h.d.qpos[:11];mj.mj_kinematics(m,d);rot=R.from_matrix(d.xmat[mount].reshape(3,3));F=np.diag([(-1 if si else 1),1,1])
        pos=d.xpos[mount]+rot.apply(F@self.start);d.qpos[adr:adr+3]=pos
        rel=R.from_quat(np.roll(h.d.qpos[14:18],-1)).as_matrix()
        d.qpos[adr+3:adr+7]=np.roll((rot*R.from_matrix(F@rel@F)).as_quat(),1)
        barrel=m.geom(pre+'barrel').id;m.geom_size[barrel,0]=h.m.geom_size[h.barrel,0] if m.geom_type[barrel]!=mj.mjtGeom.mjGEOM_MESH else m.geom_size[barrel,0]
        tips={g:m.geom(g).name[len(pre):].split('_')[0] for g in range(m.ngeom) if m.geom(g).name.startswith(pre) and 'silicone_pad' in m.geom(g).name}
        roll=float(os.environ.get('ROLL',.0015))
        for g in [barrel,*tips]:
            m.geom_condim[g]=6
            m.geom_friction[g]=[1.15,.003,roll]
        self.data.append((mount,pen,ac,barrel,tips));self.comp.append([m.jnt_dofadr[m.joint(pre+h.m.joint(i).name).id] for i in range(11)])
    mj.mj_forward(m,d)
 def control(self,t):
    for i,(mount,pen,ac,_,_) in enumerate(self.data):
        a=(6.0*np.sin(2*np.pi*t/(4.8+i*.55)+i*.7)-2.5)*min(t,1)
        y=(self.d.xmat[mount].reshape(3,3).T@(self.d.xpos[pen]-self.d.xpos[mount]))[1]
        rot=self.d.xmat[mount].reshape(3,3)
        F=np.array([(-1 if i else 1),1.,1.]);center=(rot.T@(self.d.xpos[pen]-self.d.xpos[mount]))*F
        axis=(rot.T@self.d.xmat[pen].reshape(3,3)[:,0])*F*F[0]
        ff=control(self.wmap,center,self.start,axis,a,(rot.T@self.m.opt.gravity)*F,float(os.environ.get('WGAIN',1)))
        feedback=ff+self.ny*np.clip(float(os.environ.get('YGAIN',0))*(self.start[1]-y),-.012,.012)
        self.d.ctrl[ac]=.006*(self.neutral+feedback+(self.par[3]*(self.d.qfrc_bias[self.comp[i]]-self.oldbias)+self.par[:3]@self.preload)/.864+self.par[4:]+abs(a)/15*self.co[int(a>0)])
 def measure(self):
    out=[]
    for i,(mount,pen,ac,barrel,tips) in enumerate(self.data):
        other=[c.geom1+c.geom2-barrel for c in self.d.contact if barrel in (c.geom1,c.geom2)]
        digits={tips[g] for g in other if g in tips}
        rot=self.d.xmat[mount].reshape(3,3);p=rot.T@(self.d.xpos[pen]-self.d.xpos[mount]);ax=rot.T@self.d.xmat[pen].reshape(3,3)[:,0]
        out.extend([np.linalg.norm(p),np.rad2deg(np.arctan2(ax[2],ax[0])),int('Thumb' in digits and len(digits)>1)])
    return out
