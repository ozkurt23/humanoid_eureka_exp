from pathlib import Path
import json,subprocess,os
import numpy as np
from scipy.spatial.transform import Rotation as R
import imageio.v2 as io
import imageio_ffmpeg
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parent;O=W.parents[1]/'outputs/surpriz-denge'
z=np.load(W/'final.npz');marks=json.loads((W/'arrows.json').read_text())
p=z['poses'];n=list(z['names']);r=R.from_quat(p[:,n.index('base_link'),:][:,[4,5,6,3]])
angle=r.as_euler('xyz',degrees=True)[:,1]
f=z['ticks'][:,-1];events=np.flatnonzero(np.diff(np.r_[False,abs(f)>0,False])).reshape(-1,2);ass=W/'telemetry.ass'
header='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Info,Lato,34,&H00F7F4EF,&H000000FF,&H30272320,&H70272320,-1,0,0,0,100,100,0,0,3,10,0,7,68,60,59,1
Style: Arrow,Lato,20,&H00FFFFFF,&H000000FF,&H00272320,&HFF000000,0,0,0,0,100,100,0,0,1,1,0,7,0,0,0,1
[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
'''
def stamp(i):
 cs=round(i*100/60);return f'0:{cs//6000:02}:{cs//100%60:02}.{cs%100:02}'
rows=[]
def add(i,end,line,layer=0):rows.append(f'Dialogue: {layer},{stamp(i)},{stamp(end)},{"Arrow" if layer else "Info"},,0,0,0,,{line}\n')
met=z['metrics'];dex=z['dex']
for i in range(0,3300,4):
 k=round(i*500/60);e=next(((j,lo,hi) for j,(lo,hi) in enumerate(events,1) if lo<=k<hi+400),None)
 if e:
  j,lo,hi=e
  msg=f'{j}. itme   {abs(round(f[k]))} N' if k<hi else 'Toparlanma'
  add(i,i+4,f'{msg}   ·   Gövde {angle[i]:+.0f}°')
  if k<lo+500:
   contact=met[lo,10:12].astype(bool)
   support={(True,True):'iki ayak yerde',(True,False):'sol ayak yerde',(False,True):'sağ ayak yerde',(False,False):'iki ayak havada'}[tuple(contact)]
   add(i,i+4,r'{\pos(68,129)}'+'Başlangıçta '+support)
 if 11<=i/60<16.5 or 22<=i/60<27.5 or 33<=i/60<38.5:
  l,rt=dex[i,[1,4]]
  add(i,i+4,r'{\an1\pos(70,1000)}'+f'Ele göre kalem eğimi     Sol {l:+.0f}°     Sağ {rt:+.0f}°')
for k,(tail,tip) in marks.items():
 i=int(k);a=np.array(tail);b=np.array(tip);v=b-a;norm=np.linalg.norm(v)
 if norm<15 or not (15<b[0]<1905 and 20<b[1]<1060):continue
 v/=norm;q=np.array([-v[1],v[0]]);b-=v*9
 pts=[a+q*3,b-v*21+q*3,b-v*21+q*10,b,b-v*21-q*10,b-v*21-q*3,a-q*3]
 draw='m '+' l '.join(' '.join(map(str,np.rint(x).astype(int))) for x in pts)
 add(i,i+1,r'{\an7\pos(0,0)\p1\bord1\shad0\1c&H67BBFF&\3c&H314053&}'+draw,1)
ass.write_text(header+''.join(rows))
seq=sorted((W/'frames').glob('*.jpg'));assert [int(p.stem) for p in seq]==list(range(1,3301))
mp4=O/'Beklenmedik-Itmeler-Iki-Kalem-1080p60.mp4'
# Both small cameras are locked to their own wrist and share the main simulation clock.
panels=W/'panels';panels.mkdir(exist_ok=True)
font=ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Bold.ttf',23)
blank=panels/'clear.png';Image.new('RGBA',(410,554)).save(blank)
starts=(1034,1651)
for frame in range(starts[0],starts[-1]+240):
    i=frame-starts[0];which=next((start for start in starts if start<=frame<start+240),None)
    dest=panels/f'{i:04}.png'
    if which is None:
        if not dest.exists():os.link(blank,dest)
        continue
    card=Image.new('RGBA',(410,554),(0,0,0,0));draw=ImageDraw.Draw(card)
    for si,side in enumerate('LR'):
        y=si*279
        draw.rounded_rectangle((0,y,409,y+270),radius=8,fill=(37,34,32,233))
        title='Sol el' if si==0 else 'Sağ el'
        pitch=dex[frame-1,1+3*si]
        draw.text((12,y+6),title,font=font,fill='#f5f0e8')
        draw.text((397,y+6),f'{pitch:+.0f}°',anchor='ra',font=font,fill='#f4ce91')
        with Image.open(W/('inset'+side)/f'{frame:04}.jpg') as photo:
            card.paste(photo.resize((400,225),Image.Resampling.LANCZOS),(5,y+40))
    age=frame-which;fade=min(1,(age+1)/10,(240-age)/12)
    if fade<1:card.putalpha(card.getchannel('A').point(lambda a:round(a*fade)))
    card.save(dest,compress_level=1)
filters=f'[1:v]format=rgba,setpts=PTS-STARTPTS+{(starts[0]-1)/60}/TB[inset];[0:v][inset]overlay=1455:172:eof_action=pass:repeatlast=0,ass={ass},scale=out_color_matrix=bt709,format=yuv420p[out]'
cuts=np.arange(11)*5.5
names=['Yürüyüş','Önden takip','Sol parmak uçları','Çapraz geniş açı','İki kalem','Üst açı','Sağ parmak uçları','Alçak açı','Önden denge','Yürüyüşe devam']
meta=W/'chapters.ffmeta'
meta.write_text(';FFMETADATA1\n'+''.join(f'[CHAPTER]\nTIMEBASE=1/60\nSTART={round(cuts[j]*60)}\nEND={round(cuts[j+1]*60)}\ntitle={name}\n' for j,name in enumerate(names)))
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-framerate','60','-i',str(W/'frames/%04d.jpg'),'-framerate','60','-i',str(panels/'%04d.png'),'-i',str(meta),'-map_chapters','2','-map_metadata','2','-filter_complex_threads','5','-filter_complex',filters,'-map','[out]','-threads','8','-c:v','libx264','-crf','16','-preset','fast','-colorspace','bt709','-movflags','+faststart',str(mp4)],check=True)
reader=io.get_reader(mp4);m=reader.get_meta_data();assert (reader.count_frames(),m['duration'],m['fps'],m['size'])==(3300,55.,60.,(1920,1080))
sheet=Image.new('RGB',(1440,810));sample=[162,510,806,1040,1440,1740,2100,2470,2920]
for j,k in enumerate(sample):
 im=Image.fromarray(reader.get_data(k));assert np.asarray(im).std()>10
 sheet.paste(im.resize((480,270),Image.Resampling.LANCZOS),(j%3*480,j//3*270))
sheet.save(O/'Filmden-Kareler.jpg',quality=94)

reader.close();print(m)
