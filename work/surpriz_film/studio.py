import sys, math, os, json
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
W=Path(__file__).resolve().parent;O=W.parents[1]/'outputs';S=bpy.context.scene
source=os.environ.get('TAKE','final')
z=np.load(W/(source+'.npz'));poses=z['poses'][:3300];names=list(z['names']);N=len(poses)
def xyz(n):return poses[:,names.index(n),:3]
def animate(ob,j,mirrored=False):
    ob.animation_data_clear();ob.rotation_mode='QUATERNION'
    a=poses[:,j].copy();q=a[:,3:];q[1:]*=np.cumprod(np.where(np.sum(q[:-1]*q[1:],axis=1)<0,-1,1))[:,None]
    action=bpy.data.actions.new(ob.name+'_physics');ob.animation_data_create();ob.animation_data.action=action
    for path,base,width in [('location',0,3),('rotation_quaternion',3,4)]:
        for k in range(width):
            fc=action.fcurves.new(path,index=k);fc.keyframe_points.add(N)
            fc.keyframe_points.foreach_set('co',np.column_stack((np.arange(1,N+1),a[:,base+k])).astype('f').ravel())
            fc.update()
    ob.animation_data.action_slot=action.slots[0]
    if mirrored:ob.scale.x=-1
# Retire the existing hand CAD at the exact wrist joint, and keep the original robot links.
for ob in list(S.objects):
    if ob.type=='MESH' and ob.name.startswith(('L_Hand_','R_Hand_')):bpy.data.objects.remove(ob,do_unlink=True)
for j,n in enumerate(names):
    if not n.startswith(('Lv_','Rv_')) and n!='world':animate(bpy.data.objects[n],j)
with bpy.data.libraries.load(str(O/'hareket/hand.blend'),link=False) as (avail,lib):
    importnames=[n for n in avail.objects if n.startswith(('cad_','Cylinder','Sphere')) or n in [v[3:] for v in names if v.startswith('Lv_')]+['world']]
    lib.objects=importnames.copy()
imported=dict(zip(importnames,lib.objects))
def metal(name,color,roughness,metallic):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    b=mat.node_tree.nodes.get('Principled BSDF')
    for key,v in [('Base Color',(*color,1)),('Roughness',roughness),('Metallic',metallic)]:b.inputs[key].default_value=v
    return mat
nib=metal('Bilyeli kalem ucu',(.25,.28,.30),.22,.87)
ink=metal('Yazma bilyesi',(.014,.019,.025),.18,.62)
for prefix in ('Lv_','Rv_'):
    for j,n in enumerate(names):
        if not n.startswith(prefix):continue
        src=imported['world' if n.endswith('mount') else n[3:]]
        anchor=bpy.data.objects.new(n,None);S.collection.objects.link(anchor);animate(anchor,j,prefix=='Rv_')
        for child in src.children:
            if child.type!='MESH':continue
            ob=child.copy();ob.name=n+'_'+child.name;S.collection.objects.link(ob);ob.parent=anchor
            if n.endswith('_pen'):
                if child.name.startswith('Sphere') and ob.location.x>0:ob.hide_render=True
                if child.name.startswith('Cylinder') and child.dimensions.length>.07:
                    ob.scale.z*=.95;ob.location.x-=.00375
            if n=='Rv_pen' and child.name.startswith('Cylinder') and child.dimensions.length>.07:
                ob.data=ob.data.copy()
                for slot in ob.material_slots:
                    if slot.material:
                        mat=slot.material.copy();slot.material=mat
                        if mat.use_nodes:mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.032,.26,.27,1)
        if n.endswith('_pen'):
            bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.005,radius2=.0007,depth=.010)
            tip=bpy.context.object;tip.parent=anchor;tip.location=(.0725,0,0);tip.rotation_euler=(0,math.pi/2,0);tip.data.materials.append(nib)
            for poly in tip.data.polygons:poly.use_smooth=True
            bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=.00072)
            ball=bpy.context.object;ball.parent=anchor;ball.location=(.0774,0,0);ball.data.materials.append(ink)
for ob in list(S.objects):
    if ob.name.startswith(('Porcelain','Grout bed','Plaster wall','Stone skirting','Side stile','Side rail')):
        for i in [1,2]:
            c=ob.copy();S.collection.objects.link(c);c.location.y-=i*(11.4 if ob.name.startswith('Porcelain') else 11)
    if ob.name.startswith(('Far wall','Far skirting','Panel stiles','Panel rails')):
        c=ob.copy();S.collection.objects.link(c);c.location.y=-24-(ob.location.y-4.35)
    if ob.type=='LIGHT' and ob.data.type=='AREA':
        for y in (-6,-12,-18):
            c=ob.copy();S.collection.objects.link(c);c.location.y+=y
# Camera cuts at exact frame boundaries. Each lens has a dedicated, continuous camera track.
root=xyz('base_link');L=xyz('Lv_pen');R=xyz('Rv_pen');mid=(L+R)/2
def smooth(a,r):
    padded=np.pad(a,((r,r),(0,0)),mode='edge');kernel=np.hanning(2*r+1);kernel/=kernel.sum()
    return np.column_stack([np.convolve(padded[:,i],kernel,'valid') for i in range(3)])
base=smooth(root,32);base[:,0]=np.repeat([np.mean(root[int(i*330):int((i+1)*330),0]) for i in range(10)],330);base[:,2]=base[0,2]; hands=smooth(mid,8);left=smooth(xyz('Lv_mount'),5)+np.mean(L-xyz('Lv_mount'),axis=0);right=smooth(xyz('Rv_mount'),5)+np.mean(R-xyz('Rv_mount'),axis=0)
wide=base+np.array([0,0,-.22]);upper=base+np.array([0,-.17,.12])
# Lens (mm), subject, camera displacement, horizontal drift, f-stop.
shots=[
 ('01 Genel',39,wide,(-2.75,-3.35,.64),.52,0),
 ('02 Karsidan takip',37,wide,(.12,-3.85,.29),.04,0),
 ('03 Sol parmaklar',62,left,(.18,.33,.18),.075,8),
 ('04 Capraz denge',38,wide,(2.05,-3.75,.30),-.12,0),
 ('05 Cift kalem',49,hands,(.45,.34,.90),.21,9),
 ('06 Yukaridan denge',37,wide,(-1.52,-3.55,1.60),.20,0),
 ('07 Sag parmaklar',54,right,(-.14,.283,.148),-.08,8),
 ('08 Alcak genel',39,wide,(-1.85,-3.35,-.19),.17,0),
 ('09 Uzun itme',39,wide,(1.08,-3.74,.30),.30,0),
 ('10 Genel kapanis',41,wide,(1.64,-3.02,.45),1.0,0)]
cuts=np.rint(np.arange(11)*5.5*60).astype(int)
for i,(lab,lens,subject,dis,drift,fstop) in enumerate(shots):
    data=bpy.data.cameras.new(lab);cam=bpy.data.objects.new(lab,data);S.collection.objects.link(cam);data.lens=lens;data.clip_start=.015
    data.dof.use_dof=bool(fstop);data.dof.aperture_fstop=fstop or 8
    start=cuts[i];end=min(cuts[i+1]-1,N-1)
    for frame in list(range(start,end+1,3))+[end]:
        if frame<0 or frame>=N:continue
        t=(frame-start)/(end-start);off=np.array(dis)+np.array([drift*(t-.5),0,0])
        if i==9:off*=1+.38*t
        cam.location=Vector(subject[frame]+off);cam.rotation_euler=Vector(-off).to_track_quat('-Z','Y').to_euler()
        cam.keyframe_insert('location',frame=frame+1);cam.keyframe_insert('rotation_euler',frame=frame+1)
        data.dof.focus_distance=np.linalg.norm(off);data.dof.keyframe_insert('focus_distance',frame=frame+1)
    marker=S.timeline_markers.new(lab,frame=start+1);marker.camera=cam
    if i==0:S.camera=cam
S.view_settings.exposure-=.45
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
force=z['ticks'][:,-1]
arrow={}
for frame in range(N):
        strength=force[round(frame*500/60)]
        if abs(strength)<2:continue
        S.frame_set(frame+1)
        target=xyz(os.environ.get('PUSHBODY','base_link'))[frame].copy()
        def project(x):
            p=world_to_camera_view(S,S.camera,Vector(x))
            return [round(p.x*1920,2),round((1-p.y)*1080,2)]
        arrow[str(frame)]=[project(target-np.array([np.sign(strength)*(.18+abs(strength)*.0045),0,0])),project(target)]
(W/'arrows.json').write_text(json.dumps(arrow))
S.frame_start=1;S.frame_end=N;S.render.fps=60;S.render.fps_base=1
exec((W.parent/'studio/gpu.py').read_text());S.cycles.samples=int(os.environ.get('SPP','8'));S.cycles.max_bounces=4
S.render.use_persistent_data=True;S.render.resolution_x=1920;S.render.resolution_y=1080;S.render.resolution_percentage=100
S.render.image_settings.file_format='JPEG';S.render.image_settings.quality=94
if 'insets' in sys.argv:
    for first in (1034,1651):
        exec((W/'insets.py').read_text())
elif 'save' in sys.argv:
    S.frame_set(1)
    S.render.image_settings.file_format='FFMPEG'
    S.render.ffmpeg.format='MPEG4';S.render.ffmpeg.codec='H264'
    S.render.filepath='//Habersiz-Itmeler.mp4'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(O/'tepkisel/habersiz/Habersiz-Itmeler.blend'),compress=True)
elif 'preview' in sys.argv:
    S.render.resolution_percentage=45
    for i in range(10):
        f=min(N,165+i*330);S.frame_set(f);S.render.filepath=str(W/f'p{i}.jpg');bpy.ops.render.render(write_still=True)
else:
    dest=W/'frames';dest.mkdir(exist_ok=True);S.render.use_overwrite=False;S.render.filepath=str(dest)+'/';bpy.ops.render.render(animation=True)
