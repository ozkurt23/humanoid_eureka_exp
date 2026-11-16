from grip import *
from power import trial
class PowerGrip:
 def __init__(self,m,d):
    row=json.loads((W/os.environ.get('GRIP','power4.json')).read_text())[int(os.environ.get('CAND',0))];p=np.array(row[-1]);q=np.r_[np.tile(p[2:5],3),p[5:7]];q[[0,6]]+=p[7];q[[2,8]]+=p[8];self.q=q
    self.delta=np.array([.11,.07,-.06,0,.02,0,-.11,-.07,.06,.03,.04])
    initialq=trial((p,2),True)
    h=initial(162000)[0];self.data=[];self.m=m;self.d=d
    for i,s in enumerate('LR'):
        pre=s+'v_';mount=m.body(pre+'mount').id;pen=m.body(pre+'pen').id;bar=m.geom(pre+'barrel').id
        adr=m.jnt_qposadr[m.body_jntadr[pen]];ac=[m.actuator(pre+h.m.joint(j).name).id for j in range(11)]
        j=[m.joint(pre+h.m.joint(j).name).qposadr[0] for j in range(11)]
        d.qpos[j]=initialq[:11];mj.mj_kinematics(m,d)
        rot=R.from_matrix(d.xmat[mount].reshape(3,3));F=np.diag([(-1 if i else 1),1,1])
        d.qpos[adr:adr+3]=d.xpos[mount]+rot.apply(F@initialq[11:14]);rel=R.from_quat(np.roll(initialq[14:],-1)).as_matrix()
        d.qpos[adr+3:adr+7]=np.roll((rot*R.from_matrix(F@rel@F)).as_quat(),1)
        m.geom_size[bar,0]=h.m.geom_size[h.barrel,0]
        pads={g:m.geom(g).name[len(pre):].split('_')[0] for g in range(m.ngeom) if m.geom(g).name.startswith(pre)}
        for g in pads:
            if g==bar or 'silicone_pad' in m.geom(g).name:m.geom_condim[g]=6;m.geom_friction[g]=[1.15,.003,.0008]
        self.data.append((mount,pen,ac,bar,pads))
    mj.mj_forward(m,d)
 def control(self,t):
    for i,(_,_,ac,_,_) in enumerate(self.data):
        self.d.ctrl[ac]=.006*(self.q+self.delta*np.sin(2*np.pi*(.92+t)/(4.8+i*.47)))
 def measure(self):
    result=[]
    for mount,pen,ac,bar,pads in self.data:
        contact={pads.get(c.geom1+c.geom2-bar,'other') for c in self.d.contact if bar in (c.geom1,c.geom2)}
        rot=self.d.xmat[mount].reshape(3,3);p=rot.T@(self.d.xpos[pen]-self.d.xpos[mount]);ax=rot.T@self.d.xmat[pen].reshape(3,3)[:,0]
        result.extend([np.linalg.norm(p),np.rad2deg(np.arctan2(ax[2],ax[0])),int(len(contact)>=2 and ('fixed' in contact or 'Thumb' in contact))])
    return result
