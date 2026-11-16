from searchlong import local
from grip import *
from concurrent.futures import ProcessPoolExecutor
def trial(job,export=False):
 params,seconds=job;p=np.array(params);h,st,n,bias,pre,grav,co,ny=local();m=h.m;d=h.d;mj.mj_resetData(m,d)
 y,z=p[:2];q=np.r_[np.tile(p[2:5],3),p[5:7]]
 q[[0,6]]+=p[7];q[[2,8]]+=p[8];center=np.array([p[9],y,z])
 d.qpos[:11]=q;d.qpos[11:14]=center;d.qpos[14:]=[1,0,0,0];m.opt.gravity[:]=grav[0];mj.mj_forward(m,d)
 bar=h.barrel
 for g in range(m.ngeom):
    if g==bar or 'silicone_pad' in m.geom(g).name:m.geom_condim[g]=6;m.geom_friction[g]=[1.15,.003,.0008]
 stable=0;contacts=0;angles=[];worst=0;ang3=[]
 pulse=np.array([.11,.07,-.06,0,.02,0,-.11,-.07,.06,.03,.04])
 for k in range(-15,int(seconds*50)):
    t=max(0,k*.02);m.opt.gravity[:]=grav[min(len(grav)-1,round(t*60))]
    d.ctrl[:]=.006*(q+pulse*np.sin(2*np.pi*t/4.8))
    if k<0:
        for _ in range(10):
            d.qpos[11:14]=center;d.qpos[14:]=[1,0,0,0];d.qvel[11:]=0;mj.mj_step(m,d)
        continue
    mj.mj_step(m,d,nstep=10)
    ds=np.linalg.norm(d.qpos[11:14]-center)
    if ds>.025:break
    worst=max(worst,ds)
    digits={m.geom(c.geom1+c.geom2-bar).name.split('_')[0] for c in d.contact if bar in (c.geom1,c.geom2)}
    contacts+=int(len(digits)>=2 and ('fixed' in digits or 'Thumb' in digits));stable+=1
    ax=d.xmat[h.pen].reshape(3,3)[:,0];angles.append(np.rad2deg(np.arctan2(ax[2],ax[0])));ang3.append(np.rad2deg(np.arccos(np.clip(ax[0],-1,1))))
    if export and k==45:return d.qpos.copy()
 a=np.percentile(angles or [0],[5,95]);yaw=np.mean(ang3 or [90])
 score=(stable+.8*contacts)/(seconds*50)*8+max(0, min(1,(a[1]-a[0])/12))-.01*yaw-20*worst
 return [round(float(score),5),stable,contacts,np.round(a,2).tolist(),p.tolist()]
if __name__=='__main__':
 rng=np.random.default_rng(721);num=int(sys.argv[1]);sec=float(sys.argv[2]);out=W/'power.json';old=json.loads(out.read_text())[:40] if out.exists() else [];jobs=[]
 for i in range(num):
    if old and i<40:p=np.array(old[i%len(old)][-1])
    elif old and i%8:
        p=np.array(old[rng.integers(len(old))][-1])+rng.normal(0,[.002,.003,.06,.06,.07,.08,.07,.07,.05,.004])
    else:p=rng.uniform([-.006,.049,.95,1.0,.9,.25,.15,-.19,-.15,-.014],[.011,.083,1.54,1.55,1.55,1.04,1.25,.18,.12,.004])
    jobs.append((p,sec))
 with ProcessPoolExecutor(14) as pool:rows=sorted(pool.map(trial,jobs,chunksize=2),reverse=True)
 out.write_text(json.dumps(rows[:60]));print(rows[:2])
