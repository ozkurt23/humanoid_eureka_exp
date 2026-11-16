from pathlib import Path
import bpy,numpy as np
from mathutils import Quaternion,Vector
W=Path(__file__).resolve().parent;S=bpy.context.scene;z=np.load(W/'final.npz');poses=z['poses'];names=list(z['names'])
S.timeline_markers.clear()
exec((W.parent/'studio/gpu.py').read_text());S.cycles.samples=10;S.render.use_persistent_data=True
S.render.resolution_x=448;S.render.resolution_y=252;S.render.resolution_percentage=100;S.render.image_settings.file_format='JPEG';S.render.image_settings.quality=95
S.frame_start=first;S.frame_end=first+239
for side in 'LR':
 indices=range(first-1,first+239,3)
 ao=[]
 for k in indices:
  wrist=Quaternion(poses[k,names.index(side+'v_mount'),3:].tolist())
  barrel=Quaternion(poses[k,names.index(side+'v_pen'),3:].tolist())
  ao.append(list(wrist.inverted()@(barrel@Vector((1,0,0)))))
 ao=np.array(ao);ii,jj=np.unravel_index(np.argmin(ao@ao.T),(len(ao),len(ao)));ks=[indices[ii],indices[jj]];T=poses[ks,names.index(side+'v_mount')];P=poses[ks,names.index(side+'v_pen')]
 wrists=[Quaternion(row[3:].tolist()) for row in T]
 centers=[q.inverted()@Vector((pen[:3]-mount[:3]).tolist()) for q,pen,mount in zip(wrists,P,T)]
 axes=[q.inverted()@(Quaternion(pen[3:].tolist())@Vector((1,0,0))) for q,pen in zip(wrists,P)]
 normal=axes[0].cross(axes[1]).normalized()
 if (wrists[0]@normal).y>0:normal=-normal
 orient=wrists[0].inverted()@(-(wrists[0]@normal)).to_track_quat('-Z','Y')
 center=(centers[0]+centers[1])/2;dc=bpy.data.cameras.new(side+' makro');cam=bpy.data.objects.new(side+' makro',dc);S.collection.objects.link(cam);dc.lens=54;dc.clip_start=.008
 cam.rotation_mode='QUATERNION'
 for frame in range(S.frame_start,S.frame_end+1):
  M=poses[frame-1,names.index(side+'v_mount')];q=Quaternion(M[3:].tolist())
  cam.rotation_quaternion=q@orient;cam.location=Vector(M[:3].tolist())+q@(center+normal*.35)
  cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame)
 S.camera=cam;dest=W/('inset'+side);dest.mkdir(exist_ok=True);S.render.filepath=str(dest)+'/';bpy.ops.render.render(animation=True)
