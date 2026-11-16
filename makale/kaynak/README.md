# Makalenin kaynakları

`Makale.tex` yedi sayfalık Türkçe teknik raporun düzenlenebilir LaTeX kaynağıdır. Başlık, metin, kaynakça, şekil açıklamaları ve sonuç tablosu bu dosyadadır. Rapor bağımsız bir proje çalışması olarak hazırlanmıştır.

## PDF üretimi

Bu klasörde, Tectonic 0.17 veya XeLaTeX kurulu bir ortamda çalıştırın. Ubuntu üzerinde Liberation Serif, Lato ve DejaVu Sans Mono yazı tipleri kullanılır. Şekiller önceden hazırlandığı için PDF derlemesi Python gerektirmez.

```sh
tectonic --outdir .. Makale.tex
```

XeLaTeX kullanılıyorsa kaynakça ve bağlantılar için iki geçiş yapın. Kaynaklar metin içinde numaralandırılmıştır.

## Veriler ve çizimler

- `olcumler.json` film koşusunu, beş eşlenmiş itme karşılaştırmasını ve 15 tam deneme kaydının ölçümlerini içerir. Başarısız koşular da dahildir.
- `yuruyus.csv` filmdeki 500 Hz fizik kaydından her 25 örnekte bir alınan kuvvet ve ileri konum izidir. `kalem.csv` her iki bileğe göre 60 Hz kalem eğimini içerir.
- `sekiller.py` bu ölçümlerden vektör PDF grafikleri ve TeX satırlarını üretir. `python3 sekiller.py` komutu için NumPy ve Matplotlib gerekir. Tablo 1 metne doğrudan dizilmiştir. Sayısal kaynak güncellenirse `sekiller/kosular.tex` satırlarını Tablo 1'e aktarın.
- `gorseller/` klasöründe filmin gerçek Blender karelerinden kırpılmış fotoğraflar yer alır. `kareler.json` kaynak kamera, kare numarası ve oransal kırpma sınırlarını belirtir. Kare numaraları birden başlar, film zamanı (kare − 1) / 60 olarak hesaplanır.
- `veri_hazirla.py`, tam proje arşivi açıldıktan sonra, `python3 veri_hazirla.py /proje/klasoru` ile özgün MP4'ün üretiminde kullanılan verileri ve görsel kaynakları yeniden hazırlar. NumPy ve Pillow gerekir.
