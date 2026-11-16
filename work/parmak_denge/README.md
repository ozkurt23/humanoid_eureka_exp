# Beklenmedik yanal itme ve iki kalem

Bu klasör, mevcut Ubuntu çalışma alanındaki birleşik humanoid ve V3 el modeliyle çalışır. Simülatör MuJoCo, hesaplama yerel CPU üzerindedir. Kalemler serbest cisimdir. Her iki elin tendonları kalemi parmak uçlarında hareket ettirir.

## Aynı koşuyu yeniden üretmek

Çalışma alanının kökünden `bash work/parmak_denge/run.sh 924` komutunu çalıştırın. Sonuç `work/parmak_denge/kosu-924.npz` dosyasına yazılır. Farklı bir kayıt numarası yeni bir itme takvimi üretir. 800’den küçük numaralar önceki 60, 75, 85, 100 ve 115 N dizisiyle karşılaştırma içindir. Daha büyük numaralar her itmenin başlangıcını, yönünü, şiddetini, yükselme süresini ve tepe yükü süresini örnekler.

Arşivi açarken klasörü `work/parmak_denge` olarak yerleştirin. Kardeş `work/duet`, `work/tips` klasörleri, bunların kullandığı mevcut model ve CAD dosyaları ile Ubuntu bilgisayarındaki `~/env_isaaclab` ortamı gereklidir. Arşiv mevcut deney için denetleyiciyi taşır.

## Hareket üretimi

`world.py` dış kuvveti üretir. Denetleyici bir önceki fizik adımının momentum farkından yanal yükü kestirir. Yük algılandığında `shooting.py` güncel durumu kopyalar ve aday adımları yerel simülasyonlarda karşılaştırır. Adayların hiçbirine gerçek gelecek kuvvet dizisi verilmez. Kuvvet kestiriminden oluşturulan yüklenme ve bırakma varsayımları kullanılır. Ana simülasyon seçilen adımla kesintisiz ilerler.

`catch.py` ile `blindbalance.py` basış ve yürüyüşe dönüşü üretir. Çok açılmış ve öne arkaya şaşırtılmış ayaklarda ilk salınım yana ayrılır. Böylece zaten önde olan ayak ileriye bir adım daha uzanmadan destek açıklığını daraltır. `shootrun.py` tendon ve eklem komutlarını uygular. Kalem merkezi, elin kendi koordinat sisteminde başlangıçtan 6,8 mm avuca doğru kayarsa ya da uzunlamasına dışarı kayması 10 mm’yi aşarsa o elin salınım genliği yumuşak biçimde %75’e iner. Tetikleme gerçekleşen harekete ait 60 Hz el konumu ölçümüne dayanır.

## Kayıt

`poses` ve `qs` saniyede 60 örnek içerir. 55 saniyelik film ilk 3.300 kareyi kullanır, dosya son zaman noktasını da içerir. `metrics` ve `ticks` 500 Hz ölçümlerdir. `names` gövde adlarını, `dex` ele göre kalem konumu uzaklığı, eğim ve temas ölçümlerini içerir. `assess.py` bir NPZ dosyasındaki basış, yürüyüş ve kalem sonuçlarını ölçer.
