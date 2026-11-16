import numpy as np
import mujoco as mj
def make(h):
    bar=h.barrel;js=[];maps=[];center=h.d.xpos[h.pen]
    for c in h.d.contact:
        if bar not in (c.geom1,c.geom2):continue
        g=c.geom1+c.geom2-bar
        if 'silicone_pad' not in h.m.geom(g).name:continue
        jac=np.zeros((3,h.m.nv));mj.mj_jac(h.m,h.d,jac,None,c.pos,h.m.geom_bodyid[g]);js.append(jac[:,:11].T)
        x,y,z=c.pos-center;maps.append(np.r_[np.eye(3),[[0,-z,y],[z,0,-x],[-y,x,0]]])
    return np.column_stack(js)@np.linalg.pinv(np.column_stack(maps),rcond=.002)
def control(mapping,center,goalpos,axis,angle,gravity,gain):
    rad=angle*np.pi/180
    fixed=np.array([np.cos(rad),0,np.sin(rad)])
    error=np.cross(axis,fixed)
    force=np.clip(25*(goalpos-center)-.009*gravity,-.6,.6)
    torque=np.clip(.030*error,-.02,.02)
    return gain*(mapping@np.r_[force,torque])/.864
