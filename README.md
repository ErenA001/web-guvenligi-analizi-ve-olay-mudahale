# 🛡️ Web Güvenliği Analizi ve Olay Müdahale (Staj Projesi)

## 📌 Proje Hakkında

Bu proje, staj süreci kapsamında geliştirilmiş bir **web güvenliği analizi ve olay müdahale (incident response)** çalışmasıdır.

Projenin temel amacı, web sunucularından elde edilen log kayıtları üzerinden güvenlik olaylarını analiz etmek, şüpheli aktiviteleri tespit etmek ve bu aktivitelerin olası saldırı senaryolarını değerlendirmektir.

---

## 🎯 Projenin Amacı

Bu projenin temel amacı, gerçek dünya siber güvenlik süreçlerine benzer şekilde:

- Web tabanlı sistemlerde oluşabilecek güvenlik olaylarını analiz etmek
- Sunucu log kayıtları üzerinden anormal davranışları tespit etmek
- Şüpheli IP adreslerini belirlemek ve sınıflandırmak
- Brute force gibi temel saldırı türlerinin davranışlarını incelemek
- Incident response (olay müdahale) mantığını temel seviyede uygulamak
- Log analizi üzerinden güvenlik farkındalığı geliştirmek

---

## 🧠 Proje Yaklaşımı

Proje, tamamen log tabanlı analiz yaklaşımı üzerine kurulmuştur. Bu yaklaşımda:

- Sistem tarafından üretilen HTTP logları incelenir
- IP adreslerinin davranışları analiz edilir
- Başarısız giriş denemeleri tespit edilir
- Şüpheli trafik örüntüleri belirlenir
- Elde edilen bulgular güvenlik açısından yorumlanır

Bu sayede temel bir **Security Operations (SOC) mantığı** simüle edilmiştir.

---

## 🔐 Kapsanan Güvenlik Konuları

Proje aşağıdaki temel web güvenliği konularına odaklanmaktadır:

- Web uygulama güvenliği temelleri
- HTTP protokolü davranış analizi
- Brute force saldırı mantığı
- Yetkisiz erişim girişimleri
- Log analizi ile tehdit tespiti
- Incident response süreçlerinin temel mantığı

---

## 🛠️ Kullanılan Teknolojiler ve Yöntemler

- Python 3 ile veri işleme ve analiz
- Log parsing (metin tabanlı veri analizi)
- Git & GitHub versiyon kontrolü
- CLI (komut satırı) tabanlı geliştirme yaklaşımı
- Temel siber güvenlik analiz teknikleri

---

## 📈 Projenin Katkısı

Bu proje sayesinde:

- Web güvenlik olaylarının nasıl analiz edildiği öğrenilmiştir
- Log verilerinin güvenlik açısından önemi anlaşılmıştır
- Şüpheli davranışların nasıl tespit edildiği simüle edilmiştir
- Incident response sürecinin temel mantığı kavranmıştır
- Gerçek dünya SOC süreçlerine giriş seviyesi bir bakış sağlanmıştır

---

## 📌 Genel Değerlendirme

Bu çalışma, siber güvenlik alanında özellikle **log analizi ve olay müdahale süreçlerine giriş seviyesinde bir uygulama** olarak tasarlanmıştır.

Eğitim amacıyla geliştirilmiş olup, gerçek sistem davranışlarının basitleştirilmiş bir modelini temsil etmektedir.
