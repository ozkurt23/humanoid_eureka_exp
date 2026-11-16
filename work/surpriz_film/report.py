"""Write measurements for one frozen controller and compare the five omitted impulses."""
from pathlib import Path
import json,sys,hashlib
import numpy as np
W=Path(__file__).resolve().parent;root=W.parents[1];out=root/'outputs/surpriz-denge'
sys.path.insert(0,str(root/'work/surpriz'))
from assess import measure
def de(x,n=1):return f'{x:.{n}f}'.replace('.',',')
def realstep(e):
    return max([0]+[a['shift_cm'] for a in e['landings'] if a['lift_cm']>=.5])
def evalrow(path):
    d=measure(path);ev=d['events']
    body=bool(d['seconds']==55 and d['ground']==0 and len(ev)==5)
    fingers=bool(min(d['opposed'])>=98 and d['palm']==0 and min(min(e['shaft_deg']) for e in ev)>=15)
    stepping=sum(realstep(e)>=3 for e in ev)
    walks=sum(e['walk_cm']>=2 for e in ev)
    return dict(data=d,all_ok=(body and fingers and stepping==5 and walks==5),body=body,fingers=fingers,steps=stepping,walks=walks)
if __name__=='__main__':
    folder=Path(sys.argv[1]);files=[folder/f'z{x}.npz' for x in sys.argv[2:]]
    results=[evalrow(p) for p in files]
    z=np.load(W/'final.npz');m=z['metrics'];f=z['ticks'][:,-1]
    windows=np.where(np.diff(np.r_[False,abs(f)>0,False]))[0].reshape(-1,2)
    take=measure(W/'final.npz');rows=[]
    for j,(lo,hi) in enumerate(windows):
        u=np.load(root/f'work/itme_kiyas/skip{j}.npz')['metrics']
        assert np.array_equal(m[:lo],u[:lo]) and len(u)>hi
        seg=f[lo:hi];mag=max(abs(seg));sg=np.sign(seg[np.argmax(abs(seg))])
        plateau=np.where(abs(seg)>=mag-1e-8)[0]
        idx=[lo+250,lo+500,lo+plateau[-1],hi]
        paired=100*sg*(m[idx,1]-u[idx,1]);e=take['events'][j]
        feet=z['poses'][:,[list(z['names']).index(side+'_ankle_roll') for side in 'LR'],:3]
        restarts=[]
        for side in range(2):
            air=~m[:,10+side].astype(bool)
            for lift,land in np.where(np.diff(np.r_[False,air,False]))[0].reshape(-1,2):
                if lift<hi or land>=len(m) or land-lift<15:continue
                if feet[round(lift*.12),side,1]-feet[round(land*.12),side,1]>.035:
                    restarts.append((lift-hi)*.002);break
        rows.append(dict(restart_s=min(restarts) if restarts else None,onset=lo*.002,plateau=(1+plateau[-1]-plateau[0])*.002,force=sg*mag,
                         foot_cm=realstep(e),walk_cm=e['walk_cm'],shaft=e['shaft_deg'],paired=paired.tolist()))
    lines=['# Beklenmedik itmeler altında iki kalemle yürüyüş','',
           'Blender filmi 55 saniyelik tek bir MuJoCo koşusunu 10 kamera açısından gösteriyor. Kamera kesmelerinde simülasyon devam ediyor. İki kalem serbest cisim olarak simüle edildi. Parmakları mevcut tendon komutları hareket ettirdi.','','## Filmdeki beş itme','',
           '| Başlangıç (s) | Yanal kuvvet (N) | Tepe yükünde süre (s) | İtme yönünde basılan adım (cm) | Sonraki yürüyüş (cm) | Sol / sağ kalem (°) |',
           '|---:|---:|---:|---:|---:|---:|']
    for e in rows:
        lines.append(f"| {de(e['onset'],3)} | {de(e['force'])} | {de(e['plateau'],2)} | {de(e['foot_cm'])} | {de(e['walk_cm'])} | {de(e['shaft'][0])} / {de(e['shaft'][1])} |")
    lines+=['','Adım uzunluğu, en az 30 ms yer temasını kesen ve en az 5 mm yükselen ayağın kalkış ile iniş arasındaki yanal yer değiştirmesidir. Birden fazla adımda itme yönündeki en uzun iniş gösterilir. Sonraki yürüyüş, yük bitiminden bir sonraki itmeye veya film sonuna kadar belin ileri yönde aldığı net mesafedir. Kalem açısı, itme boyunca kalem ekseninin kendi eline göre gördüğü en büyük açı farkıdır.','',
            f'Kuvvet sıfıra indikten sonra ilk ileri adım için ayak {de(min(r["restart_s"] for r in rows),2)}–{de(max(r["restart_s"] for r in rows),2)} saniye içinde yerden kesildi. Burada en az 3,5 cm ileri basan ayağın kalkış anı ölçüldü.','',
            '## İtme yapılmasaydı','',
            'Her satır için aynı başlangıçtan bir kez daha simülasyon yaptık ve yalnızca o itmenin kuvvetini sıfırladık. İtmeden önce iki koşudaki 500 Hz hareket ölçümleri birebir eşleşti. Aşağıdaki işaretli fark belin yanal konumudur. Pozitif değer itme yönünü gösterir.','',
            '| İtme | 0,5 s (cm) | 1,0 s (cm) | Tepe yükünün sonunda (cm) | Kuvvet bittiğinde (cm) |','|---:|---:|---:|---:|---:|']
    for j,e in enumerate(rows,1):
        lines.append('| '+str(j)+' | '+' | '.join(de(v) for v in e['paired'])+' |')
    lines+=['','## Aynı denetleyiciyle yürütülen koşular','',
            '714, 715, 716 ve 727 önceki zamanlama karşılaştırmalarıdır. 800’den küçük kayıtlarda 60, 75, 85, 100 ve 115 N sırası korunur, başlangıç anları ve ilk yön kayıt numarasıyla değişir. 800’den büyük kayıtlarda saatler, işaretler, 60–115 N aralığındaki tepe yükleri, 1–2 saniyelik yük süreleri ve 0,85–1,35 saniyelik yükselme süreleri dış kuvvet üretecinde değişir. Denetleyiciye bu takvim verilmez.','',
            '| Kayıt | Süre (s) | İleri yol (m) | İtme yönünde adım | Sonra ileri yürüyüş | İki uçtan temas, sol / sağ (%) | Avuç teması | Ayak dışı zemin teması |','|---:|---:|---:|---:|---:|---:|---|---|']
    for r in results:
        d=r['data'];lines.append(f"| {d['name'][1:]} | {de(d['seconds'],3)} | {de(d['forward'],2)} | {r['steps']}/5 | {r['walks']}/5 | {de(d['opposed'][0],2)} / {de(d['opposed'][1],2)} | {'Var' if d['palm'] else 'Yok'} | {'Var' if d['ground'] else 'Yok'} |")
    lines+=['','Adım sayımında en az 3 cm yanal iniş, ileri yürüyüşte en az 2 cm net ilerleme arandı. İki uçtan temas yüzdesi, kalemin başparmakla başka bir parmağın uç pedi arasında kaldığı 2 ms örneklerin oranıdır. Avuç ve ayak dışı zemin temas sütunları, koşunun herhangi bir anını kapsar. 55 saniyeden kısa kayıtlar denge izleme sınırı aşıldığında durduruldu.','',
            'Kuvvetler bele ve iki yanal yönde uygulandı. Sonuçlar bu modelin simülasyonuna ve ölçülen yük aralığına aittir. Denetleyici gerçekleşen hareketten kuvveti kestirir ve olası ayak basışlarını Ubuntu bilgisayarında simüle ederek seçer. Bu deneyde yürüyüş için yeni bir ödül eğitimi yapılmadı.']
    groups = {
        "Önceki dört zamanlama": {714,715,716,727},
        "Film ve ek denemeler": {905,924,1042,1051,1052},
        "Denetleyici sabitlendikten sonra ayrılan altı yeni zamanlama": set(range(1071,1077)),
    }
    lines.extend(["", "## Birlikte başarı ölçütü", "",
                  "Bir koşunun başarılı sayılması için robotun 55 saniyeyi tamamlaması, ayak dışında yere değmemesi, beş itmenin her birinde yana adım atması ve ardından ileri yürümesi gerekir. Ayrıca her iki elde karşılıklı parmak ucu teması koşu boyunca en az %98 olmalı, kalemler avuca değmemeli ve her itmede her kalem kendi eline göre en az 15° hareket etmelidir.", ""])
    for label, group in groups.items():
        subset=[r for r in results if int(r["data"]["name"][1:]) in group]
        if subset:
            failures=[r["data"]["name"][1:] for r in subset if not r["all_ok"]]
            lines.append(f"- {label} — {sum(r['all_ok'] for r in subset)}/{len(subset)} başarılı." + (" Ölçütlerin tümünü karşılamayan kayıtlar " + ", ".join(failures) + "." if failures else ""))
    lines.extend(["", "Fiziksel adım araması simülasyon süresinden uzun sürebilir. Film gerçek zamanlı çalışan bir donanım denetleyicisinin hız testi değildir."])
    (out/'Deney-ve-olcumler.md').write_text('\n'.join(lines)+'\n')
    (out/'Olcumler.json').write_text(json.dumps(dict(take=take,paired=rows,trials=results),ensure_ascii=False,indent=2,default=lambda x:x.item()))
