from grip import *
EVENTS=list(zip([6.42,16.66,28.18,39.70,47.38],[1.,1.25,1.50,1.75,2.],map(float,os.environ.get('LOADS','60,-75,85,-100,115').split(','))))
class Tip(Grip):
 def __init__(self,m,d):
    super().__init__(m,d)
    self.integ=np.zeros(2);self.u=np.zeros(2);self.padlist=[]
    for s,(_,_,ac,bar,tips) in zip('LR',self.data):
        self.padlist.append({g: (1 if 'Thumb_J2' in m.geom(g).name else 2 if '_J3_' in m.geom(g).name else 0) for g in tips})
    if os.environ.get('READY'):
        prior=np.load(Path(__file__).parent/(os.environ['READY']+'.npz'));k=int(os.environ.get('STARTFRAME',300));tr=prior['poses'][k];names=list(prior['names'])
        for i,(mount,pen,ac,bar,_) in enumerate(self.data):
            arm=tr[names.index(m.body(mount).name)];prev=tr[names.index(m.body(pen).name)]
            rr=R.from_quat(arm[[4,5,6,3]]);pr=R.from_quat(prev[[4,5,6,3]])
            local=rr.inv().apply(prev[:3]-arm[:3]);local[0]+=float(os.environ.get('SLIDEPEN',0))*(-1)**i
            base=R.from_matrix(d.xmat[mount].reshape(3,3));pa=m.jnt_qposadr[m.body_jntadr[pen]]
            d.qpos[pa:pa+3]=d.xpos[mount]+base.apply(local);d.qpos[pa+3:pa+7]=np.roll((base*rr.inv()*pr).as_quat(),1)
            for aa in ac:
                tendon=m.actuator_trnid[aa,0];adr=m.tendon_adr[tendon];j=m.wrap_objid[adr];qa=m.jnt_qposadr[j]
                d.qpos[qa]=prior['qs'][k,qa]
        mj.mj_forward(m,d)
    self.motion=[]
    for mount,pen,ac,bar,_ in self.data:
        joints=[m.wrap_objid[m.tendon_adr[m.actuator_trnid[u,0]]] for u in ac]
        dofs=m.jnt_dofadr[joints];delta=np.zeros(11)
        seen=set()
        for con in d.contact:
            if bar not in (con.geom1,con.geom2):continue
            g=con.geom1+con.geom2-bar;nm=m.geom(g).name
            if 'silicone_pad' not in nm or g in seen:continue
            seen.add(g);jac=np.zeros((3,m.nv));mj.mj_jac(m,d,jac,None,con.pos,m.geom_bodyid[g])
            J=jac[:,dofs];ii=np.flatnonzero(np.max(abs(J),axis=0)>1.e-7)
            if not len(ii):continue
            J=J[:,ii];axis=-d.xmat[mount].reshape(3,3)[:,1];vel=np.cross(axis,con.pos-d.xpos[pen])
            delta[ii]=J.T@np.linalg.solve(J@J.T+np.eye(3)*.0001,vel)
        self.motion.append(delta)
    if os.environ.get('ORIG'):
        for _,_,_,b,tips in self.data:
            for g in [b,*tips]:
                m.geom_condim[g]=3;m.geom_friction[g]=[1,.005,.0001]
 def control(self,t):
    for i,(mount,pen,ac,_,_) in enumerate(self.data):
        rot=self.d.xmat[mount].reshape(3,3)
        ax=rot.T@self.d.xmat[pen].reshape(3,3)[:,0];pitch=np.rad2deg(np.arctan2(ax[2],ax[0]))*(-1)**i
        dest=float(os.environ.get('AMPL','7'))*np.sin(t*2*np.pi/(4.8+i*.55)+.7*i)*min(1,t)
        error=dest-pitch;self.integ[i]=np.clip(self.integ[i]+.002*error,-55,55)
        drive=float(os.environ.get('SIGN','1'))*dest +float(os.environ.get('KP','0'))*error+float(os.environ.get('KI','0'))*self.integ[i]+float(os.environ.get('BIASANG','-2.5'))
        drive+=float(os.environ.get("TRIM",0))*max(0,pitch-float(os.environ.get("LIMIT",12)))
        self.u[i]+=np.clip(drive-self.u[i],-.05,.05)
        a=np.clip(self.u[i],-24,24)
        if os.environ.get('BARE'):
            self.d.ctrl[ac]=.006*(self.neutral+abs(a)/15*self.co[int(a>0)])
        else:
            bias=(self.par[3]*(self.d.qfrc_bias[self.comp[i]]-self.oldbias)+self.par[:3]@self.preload)/.864
            self.d.ctrl[ac]=.006*(self.neutral+bias+self.par[4:]+abs(a)/15*self.co[int(a>0)]+float(os.environ.get("IK",0))*self.motion[i]*np.deg2rad(dest)*(-1)**i)
 def contacts(self):
    flags=[0,0];palm=[0,0];prox=[0,0];forbidden=0
    for c in self.d.contact:
        pair=(c.geom1,c.geom2)
        if 0 in pair and 'Foot_' not in self.m.geom(sum(pair)).name:forbidden=1
        for i,(_,_,_,b,tips) in enumerate(self.data):
            if b in pair:
                g=sum(pair)-b; flags[i]|=self.padlist[i].get(g,0)
                nm=self.m.geom(g).name
                if not any(v in nm for v in ('Thumb_J2_','Index_J3_','Ring_J3_','Middle_J3_')):prox[i]=1
                if 'fixed_Palm' in self.m.geom(g).name:palm[i]=1
    return flags+palm+[forbidden]+prox
