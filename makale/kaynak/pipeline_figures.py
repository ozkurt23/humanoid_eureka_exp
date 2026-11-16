"""Reconstruct the recorded 18.5 s pose in MuJoCo and collect its production views."""
from pathlib import Path
import argparse
import os
os.environ.setdefault("MUJOCO_GL","egl")
import mujoco
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("workspace", type=Path)
root=parser.parse_args().workspace.resolve()
z=np.load(root / "outputs/surpriz-denge/Film-hareket-kaydi.npz")
model=mujoco.MjModel.from_xml_path(str(root/"work/duet/duet.xml"))
data=mujoco.MjData(model)
data.qpos[:]=z["qs"][1110]
mujoco.mj_forward(model,data)
camera=mujoco.MjvCamera()
camera.lookat[:]=[data.qpos[0],data.qpos[1],0.86]
camera.distance=2.75;camera.azimuth=108;camera.elevation=-8
model.vis.headlight.ambient[:]=0.65;model.vis.headlight.diffuse[:]=0.75
model.vis.global_.offwidth=900;model.vis.global_.offheight=560
with mujoco.Renderer(model,height=560,width=900) as renderer:
    renderer.update_scene(data,camera=camera)
    Image.fromarray(renderer.render()).save(here/"gorseller/physics-state.jpg",quality=94)
for path,name in [(root/"work/surpriz_film/frames/1111.jpg","blender-state"),(root/"outputs/surpriz-denge/Itme-aninda-iki-el.jpg","encoded-frame")]:
    with Image.open(path) as im:
        im.thumbnail((1000,600));im.save(here/f"gorseller/{name}.jpg",quality=94)
