# Proje ve yayın planı

Çalışmanın sorusu, bir insansı robotun yanal bir itmeyi kendi hareketinden algılayıp basışını değiştirmesi, ileri yürüyüşe dönmesi ve bu sırada iki kalemi de parmak uçlarında hareket ettirebilmesidir. Yayın, bu üç davranışın aynı zaman aralığında gerçekleşip gerçekleşmediğini okuyucunun inceleyebileceği şekilde düzenlendi.

| Aşama | Uygulama | İncelenecek çıktı |
|:---|:---|:---|
| Modeli sabitle | Birleşik insansı modeli, sağ ve sol V3 elini ve iki serbest kalemi aynı fizik sahnesine al. | [Film ve yakın çekimler](../medya/Film.mp4) |
| Denetleyiciyi kur | Gerçekleşen hareketten yanal yükü kestir. Farklı ayakları, basış konumlarını ve kuvvetin farklı zamanlarda kalkmasını aday simülasyonlarla karşılaştır. | [Yöntem ve denetleyici açıklaması](../makale/Makale.pdf) |
| İki görevi birlikte sına | Her itmede yere teması kesilen ayağın yeni iniş yerini, takip eden ileri yürüyüşü ve kalem ekseninin ele göre hareketini ölç. Avuç ve parmak ucu temaslarını fizik adımlarında kaydet. | [Ölçüm tablosu](../veri/Deney-ve-olcumler.md) |
| Sonucu karşılaştır | Dört önceki zamanlamayı, film dahil beş ek koşuyu ve denetleyici sabitlendikten sonra altı yeni zamanlamayı ayrı raporla. Filmdeki her itmenin atlandığı beş eşlenmiş koşuyu karşılaştır. | [Koşular ve eşlenmiş ölçümler](../veri/Olcumler.json) |
| Kanıtı görselleştir | Aynı 55 saniyelik kaydı on kamera açısından göster. Gövde, yere basış ve iki bileğe göre kalem hareketi için genel açıları eşzamanlı yakın çekimlerle birleştir. | [Bölüm seçilebilen yerel gösterim](../index.html) |
| Birlikte sakla | Makaleyi, filmi, kaynakları, veriyi ve yeniden kurma yolunu özel depoda topla. Arşiv parçalarının bütünlüğünü denetle. | [Arşiv ve kurulum](../arsiv/README.md) |

## Bulguların izlenebilirliği

Filmdeki bir olayı seçerken başlangıç zamanını kullanın. Örneğin 17,222 s satırı, 107,7 N tepe kuvvetini, 29,4 cm yanal adımı ve iki elde 33,9° kalem hareketini aynı pencerede birleştirir. 40,0 cm’lik bel farkı ise bu itme kaldırıldığında elde edilen ayrı koşuyla karşılaştırmadır. Bu fark ile fiziksel adım uzunluğu farklı ölçümlerdir.

Tek bir başarılı filmin performansı ne ölçüde temsil ettiğini görmek için altı yeni zamanlamanın her birine bakın. 1071 numaralı kayıtta robot beşinci itmede de yana basmasına rağmen ileri yürüyüş ve temas koşullarını sona kadar sağlayamadı. Yükün yönü, uygulama noktası ve model değiştiğinde uygulanacak sınama, araştırmanın ayrı bir sonraki aşamasıdır.

## Görsel okuma sırası

GitHub giriş sayfası, ikinci itmenin eşzamanlı gövde ve el görüntüleriyle açılır. Yerel sunumda okuyucu beş itme arasında geçiş yapabilir. Makale birimler, başarı tanımı, karşılaştırmalar ve sınırlılıklarla sayısal sonuçları açıklar. [Proje girişine dön](../README.md)
