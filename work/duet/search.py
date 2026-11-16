from grip import *
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
@lru_cache
def context():
 h,st,neutral,_=initial(162000)
 mj.mj_setState(h.m,h.d,st,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_forward(h.m,h.d)
 bias=h.d.qfrc_bias[:11].copy()
 pre=np.zeros((3,11));bar=h.barrel
 for c in h.d.contact:
    if bar not in (c.geom1,c.geom2):continue
    g=c.geom1+c.geom2-bar;gn=h.m.geom(g).name
    if 'silicone_pad' not in gn:continue
    jac=np.zeros((3,h.m.nv));mj.mj_jac(h.m,h.d,jac,None,c.pos,h.m.geom_bodyid[g])
    pre[['Index','Ring','Thumb'].index(gn.split('_')[0])]+=jac[:,:11].T@(c.frame[:3]*(1 if g==c.geom1 else -1))/.864
 m=mj.MjModel.from_xml_path(str(W/'duet.xml'));d=mj.MjData(m)
 for n,q in json.loads((W/'arm.json').read_text()).items():d.qpos[m.joint(n).qposadr]=q
 mj.mj_kinematics(m,d);gravity=d.xmat[m.body('Lv_mount').id].reshape(3,3).T@np.array([0,0,-9.81])
 return h,st,neutral,bias,pre,gravity,np.load(O/'hareket/demo_tendons.npy')
def fit(job):
 idx,par,seconds=job;h,st,n,bias,pre,gr,co=context()
 mj.mj_setState(h.m,h.d,st,mj.mjtState.mjSTATE_INTEGRATION);h.m.opt.gravity[:]=gr
 mj.mj_forward(h.m,h.d);p0=h.d.qpos[11:14].copy();errs=[];angles=[];contact=0
 for k in range(round(seconds*50)):
    t=k*.02; a=(6*np.sin(2*np.pi*t/4.8)-2.5)*min(t,1)
    h.m.opt.gravity[:]=gr+(.85*np.sin(t*4.9)*np.array([1.,.6,1.]))
    h.d.ctrl[:]=.006*(n+par[:3]@pre+par[3]*(h.d.qfrc_bias[:11]-bias)/.864+par[4:15]+abs(a)/15*co[int(a>0)])
    mj.mj_step(h.m,h.d,nstep=10)
    ds=np.linalg.norm(h.d.qpos[11:14]-p0)
    if ds>.022:break
    digits={h.m.geom(c.geom1+c.geom2-h.barrel).name.split('_')[0] for c in h.d.contact if h.barrel in (c.geom1,c.geom2) and 'silicone_pad' in h.m.geom(c.geom1+c.geom2-h.barrel).name}
    contact+=int('Thumb' in digits and len(digits)>1)
    ax=h.d.xmat[h.pen].reshape(3,3)[:,0];pitch=np.rad2deg(np.arctan2(ax[2],ax[0]));angles.append(pitch);errs.append(abs(pitch-a))
 size=len(errs);score=(size+0.7*contact)/(seconds*50)-.012*np.mean(errs or [60])-.05*abs(np.mean(angles or [0]))/10
 return [round(float(score),5),size,contact,np.round(np.percentile(angles or [0],[5,95]),1).tolist(),par.tolist()]
if __name__=='__main__':
 rng=np.random.default_rng(141);num=int(sys.argv[1]);sec=float(sys.argv[2])
 samples=[]
 elitep=W/'elite.json';elite=json.loads(elitep.read_text())[:14] if elitep.exists() else []
 for i in range(num):
    par=np.r_[rng.uniform(.06,1.2,3),rng.uniform(.5,1.1),rng.normal(0,.035,11)]
    if elite and i%8:
        par=np.array(elite[rng.integers(len(elite))][-1])+rng.normal(0,[.09]*3+[.08]+[.015]*11)
    samples.append((i,par,sec))
 with ProcessPoolExecutor(12) as pool:rows=sorted(pool.map(fit,samples,chunksize=2),reverse=True)
 elitep.write_text(json.dumps(rows[:30]));print(rows[:2],flush=True)
