from pathlib import Path
import json
import mujoco as mj
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).resolve().parent
class Hand:
    def __init__(self):
        self.m=mj.MjModel.from_binary_path(str(ROOT/'models/hand_v3_physics.mjb')); self.d=mj.MjData(self.m)
        self.pen=self.m.body('pen').id; self.barrel=self.m.geom('barrel').id
        self.sites=[self.m.site(s).id for s in ['Index','Middle','Ring','Thumb']]
        self.lo,self.hi=self.m.jnt_range[:11].T
    def fit(self,angle,center,start):
        slope=np.tan(angle)
        def residual(q):
            self.d.qpos[:11]=q; mj.mj_kinematics(self.m,self.d)
            p=self.d.site_xpos[self.sites]; signs=np.array([1,1,1,-1])
            vertical=p[:,2]-center[2]-(p[:,0]-center[0])*slope
            return np.r_[(p[:,1]-center[1])*100, (vertical-signs*.0115)*100, (q-start)*.018]
        return least_squares(residual,start,bounds=(self.lo,self.hi),max_nfev=120).x
    def initialize(self):
        start=np.array([.6,.8,.8]*3+[.8,1.])
        best=(1e9,None)
        for y in [-.039,-.048,-.057]:
            for z in [.071,.083,.095]:
                c=np.array([-.006,y,z]); q=self.fit(0,c,start);self.d.qpos[:11]=q;mj.mj_forward(self.m,self.d)
                p=self.d.site_xpos[self.sites]
                loss=np.linalg.norm(p[:,1]-y)+np.linalg.norm(p[:,2]-z-np.array([1,1,1,-1])*.0115)
                if loss<best[0]:best=(loss,(q,c))
        q,c=best[1]; angles=np.deg2rad(np.arange(-24,25,2)); qs=np.array([self.fit(a,c,q) for a in angles])
        np.savez(ROOT/'models/grasp.npz',center=c,angles=angles,qs=qs)
    def reset(self,seed):
        rng=np.random.default_rng(seed); self.sign=(-1)**(seed%2)
        data=np.load(ROOT/'models/grasp.npz');self.center=data['center'];self.angles=data['angles'];self.qs=data['qs']
        mj.mj_resetData(self.m,self.d); self.d.qpos[:11]=self.qs[12]
        self.d.qpos[11:14]=self.center+rng.uniform(-.0007,.0007,3)
        self.m.geom_size[self.barrel,0]=rng.uniform(.0047,.0053)
        mj.mj_forward(self.m,self.d)
    def pose(self,a):
        loc=np.clip(np.interp(a,self.angles,np.arange(len(self.angles))),0,len(self.angles)-1)
        i=int(loc);return self.qs[i]+(loc-i)*(self.qs[min(i+1,len(self.qs)-1)]-self.qs[i])
    def episode(self,seed,params,record=None,steps=425,refinement=None,planner=None):
        self.reset(seed); pos=self.d.qpos[11:14].copy(); frames=[]; sustained=0; phase=0; error_sum=0; trace=[]
        filtered=0.0
        phase_best=0.0
        longest_hold=0
        for k in range(steps):
            target=np.deg2rad([0,15*self.sign,-15*self.sign,0][phase])
            axis=self.d.xmat[self.pen].reshape(3,3)[:,0];angle=np.arctan2(axis[2],axis[0])
            cfg=params if params.ndim==1 else params[0 if phase==0 else (1 if target>0 else 2 if target<0 else 3)]
            err=target-angle
            desired=target*cfg[0]+cfg[1]*err
            filtered+=np.clip(desired-filtered,-.018,.018)
            command=self.pose(filtered)
            if len(cfg)==13:command+=cfg[2:]
            else:
                command[:9]+=np.tile(cfg[2:5],3);command[9:]+=cfg[5:7]
            if refinement is not None:
                command+=refinement[0 if phase==0 else 1 if target>0 else 2 if target<0 else 3]
            if planner is not None and phase>0:command=planner(self,phase,target,k,command)
            self.d.ctrl[:]=.006*np.clip(command,self.lo,self.hi)
            for _ in range(10):
                if k<15:
                    self.d.qpos[11:14]=pos;self.d.qpos[14:18]=[1,0,0,0];self.d.qvel[11:]=0
                mj.mj_step(self.m,self.d)
            if record is not None and k%2==0: record(self.m,self.d)
            if k<15:continue
            contacts=[{c.geom1,c.geom2} for c in self.d.contact]
            fingers={self.m.geom(next(iter(pair-{self.barrel}))).name.split('_')[0] for pair in contacts if self.barrel in pair and len(pair)==2 and 'silicone_pad' in self.m.geom(next(iter(pair-{self.barrel}))).name}
            ok='Thumb' in fingers and bool({'Index','Middle','Ring'}&fingers)
            if self.d.xpos[self.pen,2]<.01 or any({self.barrel,self.m.geom('floor').id}==p for p in contacts):break
            error_sum+=np.arccos(np.clip(axis@[np.cos(target),0,np.sin(target)],-1,1))
            trace.append((ok,abs(err),self.d.xpos[self.pen,2]))
            sustained=sustained+1 if ok and np.dot(axis,[np.cos(target),0,np.sin(target)])>np.cos(np.deg2rad(5)) else 0
            if phase==0:longest_hold=max(longest_hold,sustained)
            phase_best=max(phase_best,(np.exp(-9*np.arccos(np.clip(axis@[np.cos(target),0,np.sin(target)],-1,1))) if ok else 0)+min(1,sustained/25))
            if sustained>=(150 if phase==0 else 25):
                phase+=1;sustained=0;phase_best=0
                if phase==4:break
        return dict(stage=phase,seconds=len(trace)*.02,contact=np.mean([r[0] for r in trace]) if trace else 0,error=error_sum/max(1,len(trace)),stable=sustained,near=float(phase_best),longest_hold=longest_hold)
if __name__=='__main__':
    h=Hand();h.initialize();print(h.episode(0,np.array([1,.2,0,0,0,0,0])))
