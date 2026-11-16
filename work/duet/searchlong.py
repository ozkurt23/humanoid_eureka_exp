from search import *
from scipy.ndimage import gaussian_filter1d
@lru_cache
def local():
 h,st,n,bias,pre,gr,co=context()
 z=np.load(W/'g3.npz');p=z['poses'][:,list(z['names']).index('Lv_mount')]
 acc=gaussian_filter1d(p[:,:3],1.7,order=2,axis=0,mode='nearest')*3600
 # Differentiate velocity to avoid Gaussian truncation error on a travelling trajectory.
 acc=np.gradient(np.gradient(gaussian_filter1d(p[:,:3],1.4,axis=0),axis=0),axis=0)*3600
 grav=R.from_quat(p[:,[4,5,6,3]]).inv().apply(np.array([0,0,-9.81])-acc)
 grav=np.clip(grav,-16,16)
 mj.mj_setState(h.m,h.d,st,mj.mjtState.mjSTATE_INTEGRATION);mj.mj_forward(h.m,h.d)
 ny=np.zeros(11);bar=h.barrel
 for c in h.d.contact:
    if bar not in (c.geom1,c.geom2): continue
    g=c.geom1+c.geom2-bar
    if 'silicone_pad' not in h.m.geom(g).name: continue
    jac=np.zeros((3,h.m.nv));mj.mj_jac(h.m,h.d,jac,None,c.pos,h.m.geom_bodyid[g]);ids=np.flatnonzero(np.max(np.abs(jac[:,:11]),axis=0)>1e-8)
    jj=jac[:,ids];ny[ids]=jj.T@np.linalg.solve(jj@jj.T+1e-4*np.eye(3),[0,1,0])
 return h,st,n,bias,pre,grav,co,ny
def run(job):
 par,yg,roll,sec=job;h,st,n,bias,pre,grav,co,ny=local();bar=h.barrel
 for g in range(h.m.ngeom):
    if g==bar or 'silicone_pad' in h.m.geom(g).name:h.m.geom_condim[g]=6;h.m.geom_friction[g]=[1.15,.003,roll]
 mj.mj_setState(h.m,h.d,st,mj.mjtState.mjSTATE_INTEGRATION);h.m.opt.gravity[:]=grav[0];mj.mj_forward(h.m,h.d);start=h.d.qpos[11:14].copy();angles=[];both=0
 for k in range(int(sec*50)):
    t=k*.02; a=(6*np.sin(2*np.pi*t/4.8)-2.5)*min(t,1)
    h.m.opt.gravity[:]=grav[min(len(grav)-1,round(t*60))]
    h.d.ctrl[:]=.006*(n+par[:3]@pre+par[3]*(h.d.qfrc_bias[:11]-bias)/.864+par[4:]+ny*np.clip(yg*(start[1]-h.d.qpos[12]),-.012,.012)+abs(a)/15*co[int(a>0)])
    mj.mj_step(h.m,h.d,nstep=10)
    if np.linalg.norm(h.d.qpos[11:14]-start)>.021:break
    digits={h.m.geom(c.geom1+c.geom2-bar).name.split('_')[0] for c in h.d.contact if bar in (c.geom1,c.geom2) and 'silicone_pad' in h.m.geom(c.geom1+c.geom2-bar).name}
    both+=int('Thumb' in digits and len(digits)>1)
    ax=h.d.xmat[h.pen].reshape(3,3)[:,0];angles.append(np.rad2deg(np.arctan2(ax[2],ax[0])))
 a=np.percentile(angles or [0],[10,90]);score=(both+len(angles))/(sec*50)*5+.04*min(10,a[1]-a[0])-.008*abs(np.mean(a)) - 20*np.linalg.norm(start-h.d.qpos[11:14])
 return [float(score),len(angles),both,a.tolist(),float(yg),float(roll),par.tolist()]
if __name__=='__main__':
 rng=np.random.default_rng(919);num=int(sys.argv[1]);sec=float(sys.argv[2]);p=W/'long.json'
 base=json.loads((W/'first.json').read_text())+json.loads((W/'elite.json').read_text())
 rows=[];old=json.loads(p.read_text())[:32] if p.exists() else []
 for i in range(num):
    if old and i<32:
        row=old[i%len(old)]; par=np.array(row[-1]);yg=row[4];roll=row[5]
    else:
        row=(old or base)[rng.integers(len(old or base))];par=np.array(row[-1])+rng.normal(0,[.08]*3+[.05]+[.018]*11)
        yg=rng.uniform(-1,3) if not old else np.clip(row[4]+rng.normal(0,.45),-1,4)
        roll=rng.choice([.0001,.0006,.0015,.003])
    rows.append((par,yg,roll,sec))
 with ProcessPoolExecutor(15) as pool:best=sorted(pool.map(run,rows,chunksize=1),reverse=True)
 p.write_text(json.dumps(best[:50]));print(best[0],flush=True)
