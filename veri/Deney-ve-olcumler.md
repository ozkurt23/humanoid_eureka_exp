# Beklenmedik itmeler altında iki kalemle yürüyüş

Blender filmi 55 saniyelik tek bir MuJoCo koşusunu 10 kamera açısından gösteriyor. Kamera kesmelerinde simülasyon devam ediyor. İki kalem serbest cisim olarak simüle edildi. Parmakları mevcut tendon komutları hareket ettirdi.

## Filmdeki beş itme

| Başlangıç (s) | Yanal kuvvet (N) | Tepe yükünde süre (s) | İtme yönünde basılan adım (cm) | Sonraki yürüyüş (cm) | Sol / sağ kalem (°) |
|---:|---:|---:|---:|---:|---:|
| 6,098 | -62,8 | 1,77 | 15,8 | 36,7 | 32,8 / 33,6 |
| 17,222 | -107,7 | 1,82 | 29,4 | 30,2 | 33,9 / 33,9 |
| 27,044 | 103,6 | 1,30 | 18,9 | 15,7 | 30,6 / 28,4 |
| 34,882 | 104,8 | 1,23 | 15,2 | 39,5 | 30,9 / 30,5 |
| 45,962 | -63,2 | 1,70 | 20,3 | 24,7 | 32,3 / 33,9 |

Adım uzunluğu, en az 30 ms yer temasını kesen ve en az 5 mm yükselen ayağın kalkış ile iniş arasındaki yanal yer değiştirmesidir. Birden fazla adımda itme yönündeki en uzun iniş gösterilir. Sonraki yürüyüş, yük bitiminden bir sonraki itmeye veya film sonuna kadar belin ileri yönde aldığı net mesafedir. Kalem açısı, itme boyunca kalem ekseninin kendi eline göre gördüğü en büyük açı farkıdır.

Kuvvet sıfıra indikten sonra ilk ileri adım için ayak 2,16–2,25 saniye içinde yerden kesildi. Burada en az 3,5 cm ileri basan ayağın kalkış anı ölçüldü.

## İtme yapılmasaydı

Her satır için aynı başlangıçtan bir kez daha simülasyon yaptık ve yalnızca o itmenin kuvvetini sıfırladık. İtmeden önce iki koşudaki 500 Hz hareket ölçümleri birebir eşleşti. Aşağıdaki işaretli fark belin yanal konumudur. Pozitif değer itme yönünü gösterir.

| İtme | 0,5 s (cm) | 1,0 s (cm) | Tepe yükünün sonunda (cm) | Kuvvet bittiğinde (cm) |
|---:|---:|---:|---:|---:|
| 1 | -3,5 | -6,2 | 13,3 | 10,8 |
| 2 | 21,2 | 27,7 | 40,0 | 7,3 |
| 3 | 2,5 | -0,9 | 4,2 | 24,7 |
| 4 | 2,9 | 1,2 | 12,4 | 17,2 |
| 5 | 8,3 | 11,3 | 18,2 | 27,2 |

## Aynı denetleyiciyle yürütülen koşular

714, 715, 716 ve 727 önceki zamanlama karşılaştırmalarıdır. 800’den küçük kayıtlarda 60, 75, 85, 100 ve 115 N sırası korunur, başlangıç anları ve ilk yön kayıt numarasıyla değişir. 800’den büyük kayıtlarda saatler, işaretler, 60–115 N aralığındaki tepe yükleri, 1–2 saniyelik yük süreleri ve 0,85–1,35 saniyelik yükselme süreleri dış kuvvet üretecinde değişir. Denetleyiciye bu takvim verilmez.

| Kayıt | Süre (s) | İleri yol (m) | İtme yönünde adım | Sonra ileri yürüyüş | İki uçtan temas, sol / sağ (%) | Avuç teması | Ayak dışı zemin teması |
|---:|---:|---:|---:|---:|---:|---|---|
| 714 | 55,000 | 2,00 | 5/5 | 5/5 | 99,93 / 100,00 | Yok | Yok |
| 715 | 55,000 | 1,97 | 5/5 | 5/5 | 100,00 / 99,98 | Yok | Yok |
| 716 | 55,000 | 1,92 | 5/5 | 5/5 | 99,80 / 99,87 | Yok | Yok |
| 727 | 55,000 | 1,97 | 5/5 | 5/5 | 100,00 / 100,00 | Yok | Yok |
| 905 | 55,000 | 1,97 | 5/5 | 5/5 | 99,94 / 100,00 | Yok | Yok |
| 924 | 55,000 | 1,94 | 5/5 | 5/5 | 99,95 / 99,78 | Yok | Yok |
| 1042 | 17,518 | 0,60 | 1/5 | 1/5 | 98,17 / 98,57 | Var | Yok |
| 1051 | 55,000 | 2,18 | 5/5 | 5/5 | 99,91 / 100,00 | Yok | Yok |
| 1052 | 25,970 | 0,94 | 3/5 | 2/5 | 98,77 / 99,08 | Yok | Yok |
| 1071 | 48,682 | 1,10 | 5/5 | 4/5 | 99,92 / 99,73 | Var | Yok |
| 1072 | 55,000 | 1,93 | 5/5 | 5/5 | 99,93 / 99,97 | Yok | Yok |
| 1073 | 55,000 | 1,80 | 5/5 | 5/5 | 99,92 / 100,00 | Yok | Yok |
| 1074 | 55,000 | 1,94 | 5/5 | 5/5 | 100,00 / 99,87 | Yok | Yok |
| 1075 | 55,000 | 1,79 | 5/5 | 5/5 | 99,76 / 99,97 | Yok | Yok |
| 1076 | 55,000 | 1,99 | 5/5 | 5/5 | 99,89 / 100,00 | Yok | Yok |

Adım sayımında en az 3 cm yanal iniş, ileri yürüyüşte en az 2 cm net ilerleme arandı. İki uçtan temas yüzdesi, kalemin başparmakla başka bir parmağın uç pedi arasında kaldığı 2 ms örneklerin oranıdır. Avuç ve ayak dışı zemin temas sütunları, koşunun herhangi bir anını kapsar. 55 saniyeden kısa kayıtlar denge izleme sınırı aşıldığında durduruldu.

Kuvvetler bele ve iki yanal yönde uygulandı. Sonuçlar bu modelin simülasyonuna ve ölçülen yük aralığına aittir. Denetleyici gerçekleşen hareketten kuvveti kestirir ve olası ayak basışlarını Ubuntu bilgisayarında simüle ederek seçer. Bu deneyde yürüyüş için yeni bir ödül eğitimi yapılmadı.

## Birlikte başarı ölçütü

Bir koşunun başarılı sayılması için robotun 55 saniyeyi tamamlaması, ayak dışında yere değmemesi, beş itmenin her birinde yana adım atması ve ardından ileri yürümesi gerekir. Ayrıca her iki elde karşılıklı parmak ucu teması koşu boyunca en az %98 olmalı, kalemler avuca değmemeli ve her itmede her kalem kendi eline göre en az 15° hareket etmelidir.

- Önceki dört zamanlama — 4/4 başarılı.
- Film ve ek denemeler — 3/5 başarılı. Ölçütlerin tümünü karşılamayan kayıtlar 1042, 1052.
- Denetleyici sabitlendikten sonra ayrılan altı yeni zamanlama — 5/6 başarılı. Ölçütlerin tümünü karşılamayan kayıtlar 1071.

Fiziksel adım araması simülasyon süresinden uzun sürebilir. Film gerçek zamanlı çalışan bir donanım denetleyicisinin hız testi değildir.
