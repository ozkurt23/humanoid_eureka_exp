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
np.savetxt(here / "yuruyus.csv", np.c_[m[::25,0],ticks[::25,-1],-m[::25,2]+m[0,2]], delimiter=",", fmt="%.7f", header="saniye,yanal_kuvvet_N,ileri_konum_m",comments="")
np.savetxt(here / "kalem.csv", np.c_[np.arange(len(dex))/60,dex[:,1],dex[:,4]], delimiter=",", fmt="%.7f",header="saniye,sol_egim_deg,sag_egim_deg",comments="")
# Crop boxes are fractions of the source frame (left, top, right, bottom).
spec = {
    "govde":("frames",1111,(.27,.02,.69,.985)),
    "eller":("frames",1450,(0,.14,1,.90)),
    "sol-makro":("frames",780,(.05,.08,.93,.72)),
    "sag-makro":("frames",2050,(.04,.04,.98,.68)),
    "ayak":("frames",1111,(.34,.52,.66,.94)),
    "yuruyus":("frames",165,(.26,.03,.71,.98)),
}
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

# Reshape the cover details and horizontal macro plates by cropping, preserving scale.
for src, dest, size in [
    ("L-1111", "kapak-sol", (630,177)), ("R-1111", "kapak-sag", (630,177)),
    ("sol-makro","makro-sol-yatay",(900,260)), ("sag-makro","makro-sag-yatay",(900,260))]:
    with Image.open(assets/(src+".jpg")) as im:
        ImageOps.fit(im, size).save(assets/(dest+".jpg"),quality=94)
