# Deney arşivini açma

GitHub sürümündeki arşiv, birleşik yürüyüş ve iki kalem deneyinden önceki çalışmaları da içerir. İçinde özgün CAD ve simülasyon modelleri, el denetleyicileri, öğrenme ve arama kodu, ağırlıklar, başarılı ve başarısız koşular, ölçüm kayıtları, Blender sahneleri, ilk demolar ve son filmin 3.300 tam boy karesi bulunur. Son filme ait iki elin eşzamanlı yakın planları, bindirmeleri ve MP4 de korunmuştur.

## Ubuntu'da açma

Python 3.11 veya üzeri ve `zstd` gerekir. Deponun Releases bölümünden aynı sürümün tüm `proje.tar.zst.part-*` dosyalarını ve `PARCALAR.sha256` dosyasını aynı klasöre indirin. Aşağıdaki komutta `parcalar` bu klasörü gösterir. `deney-kopyasi` boş veya henüz mevcut olmayan bir klasör olmalıdır.

```sh
python3 arsiv.py parcalar --ac deney-kopyasi
```

Program her parçanın SHA-256 değerini kontrol eder, dosyaları açar, içerikleri özgün envanterle karşılaştırır ve dosya izinlerini geri yükler. Aynı içeriğe sahip bağımsız dosyalar bağımsız kalır. Kaynakta sabit bağlantıyla bağlı dosyalar ve sembolik bağlantılar yeniden oluşturulur. Alan planlaması için parçalarla açılan dosyaların toplamına yaklaşık 45 GB ayırın.

Yalnız doğrulama için aşağıdaki komut arşivi okuyarak parça özetlerini, her dosyanın özetini, boyutunu ve bağlantı hedeflerini kontrol eder.

```sh
python3 arsiv.py parcalar
```

`ENVANTER.jsonl.zst` dosyasını `zstdcat ENVANTER.jsonl.zst` ile inceleyebilirsiniz. Her satır bir yolun türünü ve dosyalar için SHA-256 değerini verir. Açılmış arşivin kökünde aynı envanterin düz metin kopyası bulunur.

## Kapsam ve yeniden üretim

Arşiv özgün proje dizinindeki deney çalışmalarını ve sonuçları kapsar. Çalışmaya sonradan eklenen yayın materyalleri deponun makale ve giriş sayfasında yer alır. Derleyici önbellekleri ve Git yönetim verileri dışarıda bırakılmıştır. Kaynak modelin yerel çalışma kopyasındaki 96 OBJ yolu içeriğiyle arşivlenmiştir. Git LFS işaretçileri ayrıca `provenance/pointers` altında bulunur. Upstream kaynak depo `ozkurt23/priv_humanoid` için sabitlenen revizyon `171930c4e7b2a17c9c8ae082bb4e1056c0e966b4` idi. Orijinal yerel checkout kısmi ve sığdı. Upstream ağacı ve yerel nesne envanteri `provenance/` altında bulunur. Tam çalışma alanı arşivinin kapsamı bu deneyin yerel dosyalarıdır.

Son deney denetleyicisi açılan klasörde `work/parmak_denge`, fizik modeli `work/duet`, render programı `work/surpriz_film`, son çıktılar `outputs/surpriz-denge` altındadır. Komutların kullandığı Ubuntu Python ortamının paket ve sürüm listesi `provenance/python-packages.txt` dosyasında verilmiştir. Tam sistem kurulumu ve kullanıcı hesabındaki genel çalışma ortamı, proje dizininin dışındadır. `work/parmak_denge/README.md` yeniden çalıştırma ayrıntılarını içerir.

Arşivde toplam 52.692 envanter kaydı, 51.240 normal dosya yolu ve 39.027 farklı dosya içeriği vardır. Sıkıştırılmış akış 17.124.660.084 bayttır.

### GitHub üzerinden toplu indirme

Depo kökünde, GitHub hesabınızla GitHub CLI oturumunu açtıktan sonra aşağıdaki komutları çalıştırın. İndirme kesilirse aynı komut önceden doğrulanmış parçaları atlar.

```bash
python3 arsiv/indir.py parcalar
python3 arsiv/arsiv.py parcalar --ac deney-kopyasi
```

[Sürümü GitHub'da aç](https://github.com/ozkurt23/humanoid_eureka_exp/releases/tag/v1.0.0)
## Farklı dizinde çalıştırma

Özgün birleşik MuJoCo modellerinin ağ yolları deneyin önceki konumunu içerir. Yeni konumda aşağıdaki komut iki taşınabilir XML kopyası oluşturur. `MODEL` değişkeniyle bunlardan birleşik modele ait olanı seçin. İşletim sisteminde kaynak projedeki `~/env_isaaclab` Python ortamının veya bu adla kurulmuş eşdeğerinin bulunması gerekir.

```sh
python3 tasinabilir-model.py deney-kopyasi
cd deney-kopyasi
MODEL=duet.portable.xml bash work/parmak_denge/run.sh 924
```

Tam sıkıştırılmış akışın SHA-256 özeti `0a2b7790b7ef56ca45990fea8393f49ef6cf14b470f34e8daea256a165351102` olarak doğrulandı. Envanterdeki 52.692 yol ayrı bir klasöre geri yüklendi ve bütünlükleri kontrol edildi.

## Public reuse and third-party notices

Original code, CAD, and research records in this archive are covered by [the public license scope](../LICENSING.md). Download project-licenses.zip and third-party-notices.zip from the same release alongside the archive parts. The Blender source release is also supplied. See [third-party source access](../third-party/README.md) for exact versions and dependencies.
