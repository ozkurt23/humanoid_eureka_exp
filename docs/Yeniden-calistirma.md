# Ubuntu üzerinde tekrar çalıştırma

Python 3.12 ile depo kökünden aşağıdaki komutları çalıştırın. Tam arşivi indirmeden filmdeki 924 numaralı koşuyu üretebilirsiniz. Hareket planlayıcısı yerel CPU üzerinde aday basışları fizik simülasyonlarında karşılaştırır. Sonucun hesaplanması film süresinden uzun sürer.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
bash work/parmak_denge/run.sh 924
python work/parmak_denge/assess.py work/parmak_denge/kosu-924.npz
```

Bu makinedeki kurulu ortamı kullanmak için komutun başına `PYTHON="$HOME/env_isaaclab/bin/python"` eklenebilir. 1072 gibi 800'den büyük başka bir sayı, yeni bir itme takvimi oluşturur. Koşuların tamamının listesi ve başarısız örnekler makalede ve ölçüm tablosunda yer alır.

## Kayda bakış

[Film hareket kaydı](../veri/Film-hareket-kaydi.npz) 60 Hz pozları ve 500 Hz kuvvet, temas ve hareket kayıtlarını içerir. Sütunları yorumlamak için [ölçüm kodunu](../work/parmak_denge/assess.py) ve [denetleyici açıklamasını](../work/parmak_denge/README.md) kullanın.

## Render ve geliştirme geçmişi

[Özel arşiv](../arsiv/README.md) deney boyunca kaydedilen varyantları, önceki filmleri, CAD ve Blender girdilerini, 15 koşunun zaman serilerini ve son filmin render karelerini içerir. Tarihsel klasörlerdeki bazı giriş yolları deneyin yapıldığı Ubuntu makinesini gösterir. Bu depodaki çalıştırılabilir kopyada birleşik modelin geometri yolları göreli olarak düzenlendi. Dosyaların arşiv kopyaları deney anındaki sürümleridir.

Humanoid ve V3 el geometrisinin kaynağı [özel model deposundaki kayıt](https://github.com/ozkurt23/priv_humanoid/tree/171930c4e7b2a17c9c8ae082bb4e1056c0e966b4) olarak sabitlenmiştir.
