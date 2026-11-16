"""Prepare only plotted samples and original Blender crops from an experiment workspace."""
import argparse
import json
from pathlib import Path
import shutil
import numpy as np
from PIL import Image, ImageOps

here = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("workspace", type=Path)
root = parser.parse_args().workspace.resolve()
render = root / "work/surpriz_film"
run = root / "outputs/surpriz-denge"
shutil.copyfile(run / "Olcumler.json", here / "olcumler.json")
z = np.load(run / "Film-hareket-kaydi.npz")
m, ticks, dex = (z[k] for k in ("metrics","ticks","dex"))
np.savetxt(here / "yuruyus.csv", np.c_[m[::25,0],ticks[::25,-1],-m[::25,2]+m[0,2]], delimiter=",", fmt="%.7f", header="time_s,lateral_force_N,forward_displacement_m",comments="")
np.savetxt(here / "kalem.csv", np.c_[np.arange(len(dex))/60,dex[:,1],dex[:,4]], delimiter=",", fmt="%.7f",header="time_s,left_inclination_deg,right_inclination_deg",comments="")
# Crop boxes are fractions of the source frame (left, top, right, bottom).
spec = {}
for s in "LR":
    for f in [1050,1111,1210]:
        spec[f"{s}-{f}"]=(f"inset{s}",f,(.03,.12,.97,.89))
assets = here / "gorseller"
assets.mkdir(exist_ok=True)
for label,(folder,frame,box) in spec.items():
    with Image.open(render / folder / f"{frame:04}.jpg") as im:
        w,h=im.size
        im.crop(tuple(round(v*n) for v,n in zip(box,[w,h,w,h]))).save(assets / f"{label}.jpg",quality=94)
(here / "kareler.json").write_text(json.dumps(spec, ensure_ascii=False,indent=2))

# Keep the three synchronized first-page panels at a common aspect ratio.
with Image.open(render / "frames" / "1111.jpg") as im:
    im.crop((295,180,1545,1000)).resize((900,590)).save(assets / "teaser-body.jpg",quality=94)
for src, dest in [("L-1111", "teaser-left"),("R-1111", "teaser-right")]:
    with Image.open(assets/(src+".jpg")) as im:
        ImageOps.fit(im,(900,590)).save(assets/(dest+".jpg"),quality=94)
force = ticks[:, -1]
window = np.flatnonzero(np.diff(np.r_[False,abs(force)>0,False])).reshape(-1,2)
profiles = []
for j,(lo,hi) in enumerate(window):
    control = np.load(root / "work/itme_kiyas" / f"skip{j}.npz")["metrics"]
    np.testing.assert_array_equal(m[:lo], control[:lo])
    take = np.unique(np.r_[np.arange(lo,hi+1,10),hi])
    sg = np.sign(force[lo:hi][np.argmax(np.abs(force[lo:hi]))])
    profiles.extend(np.c_[np.full(len(take),j+1), (take-lo)/500,
                    100*sg*(m[take,1]-control[take,1])])
np.savetxt(here/"paired-traces.csv",profiles,delimiter=",",header="push,time_since_onset_s,signed_pelvis_delta_cm",comments="",fmt=["%d","%.3f","%.6f"])
