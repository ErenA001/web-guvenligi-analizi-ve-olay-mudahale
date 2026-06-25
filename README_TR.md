# 🛡️ Web Güvenliği Analizi ve Olay Müdahale (Staj Projesi)

## 📌 Proje Hakkında

Bu proje, staj süreci kapsamında geliştirilmiş bir **web güvenliği analizi ve olay müdahale (incident response)** çalışmasıdır.

Projenin temel amacı, bir web uygulamasının güvenlik durumunu temel seviyede analiz etmek, web sunucusu log kayıtları üzerinden şüpheli aktiviteleri tespit etmek ve tespit edilen risklere karşı uygun iyileştirme veya müdahale önerileri üretmektir.

Bu çalışma, hem log tabanlı güvenlik analizi hem de web uygulaması güvenlik kontrolleri üzerine odaklanmaktadır. Proje eğitim amacıyla geliştirilmiş olup, gerçek dünya siber güvenlik süreçlerinin basitleştirilmiş bir modelini temsil etmektedir.

---

## 🎯 Projenin Amacı

Bu projenin temel amacı, gerçek dünya siber güvenlik süreçlerine benzer şekilde:

- Web tabanlı sistemlerde oluşabilecek güvenlik olaylarını analiz etmek
- Sunucu log kayıtları üzerinden anormal davranışları tespit etmek
- Şüpheli IP adreslerini belirlemek ve sınıflandırmak
- 401 Unauthorized ve 403 Forbidden gibi HTTP durum kodlarını güvenlik açısından yorumlamak
- Brute force gibi temel saldırı davranışlarını incelemek
- Web uygulamasının temel güvenlik kontrollerini değerlendirmek
- Güvenlik eksiklerini tespit ederek iyileştirme önerileri sunmak
- Incident response (olay müdahale) mantığını temel seviyede uygulamak
- Log analizi ve web güvenliği konusunda teknik farkındalık geliştirmek

---

## 🧠 Proje Yaklaşımı

Proje iki ana yaklaşım üzerine kurulmuştur:

### 1. Log Tabanlı Güvenlik Analizi

Bu aşamada web sunucusu veya örnek olarak oluşturulan log kayıtları incelenir. Loglar üzerinden IP adresleri, HTTP istekleri, durum kodları ve başarısız erişim denemeleri analiz edilir.

Bu analiz sayesinde:

- IP adreslerinin trafik davranışları incelenir
- Başarısız giriş denemeleri tespit edilir
- Şüpheli istek yoğunlukları belirlenir
- Yetkisiz erişim girişimleri gözlemlenir
- Olası saldırı davranışları hakkında yorum yapılır

Bu bölüm, temel bir **Security Operations Center (SOC)** mantığını simüle etmektedir.

### 2. Web Güvenlik Kontrolü

Projenin ilerleyen aşamalarında, yalnızca log kayıtları değil, web uygulamasının temel güvenlik yapılandırmaları da değerlendirilecektir.

Bu kapsamda:

- HTTPS kullanımı
- HTTP security headers
- Cookie güvenliği
- Login güvenliği
- Erişim kontrolü
- Hata mesajları
- OWASP Top 10 kapsamındaki temel riskler

gibi başlıklar incelenecektir.

Bu sayede projenin amacı yalnızca logları okumak değil, aynı zamanda bir web uygulamasının güvenlik açısından güçlü ve zayıf yönlerini temel seviyede değerlendirmektir.

---

## 🔐 Kapsanan Güvenlik Konuları

Proje aşağıdaki temel web güvenliği konularına odaklanmaktadır:

- Web uygulama güvenliği temelleri
- HTTP protokolü davranış analizi
- Web sunucusu log analizi
- IP bazlı trafik analizi
- Brute force saldırı mantığı
- Yetkisiz erişim girişimleri
- 401 ve 403 durum kodlarının güvenlik açısından yorumlanması
- Log analizi ile tehdit tespiti
- Temel web güvenlik kontrolleri
- OWASP Top 10 farkındalığı
- Incident response süreçlerinin temel mantığı

---

## 🛠️ Kullanılan Teknolojiler ve Yöntemler

- Python 3 ile veri işleme ve analiz
- Log parsing (metin tabanlı veri analizi)
- IP bazlı trafik inceleme
- HTTP status code analizi
- Git & GitHub versiyon kontrolü
- CLI (komut satırı) tabanlı geliştirme yaklaşımı
- Temel siber güvenlik analiz teknikleri
- Web güvenlik kontrol listesi yaklaşımı

---

## 🚨 Olay Müdahale Yaklaşımı

Proje kapsamında tespit edilen şüpheli durumlar yalnızca listelenmekle kalmayacak, aynı zamanda temel olay müdahale mantığıyla değerlendirilecektir.

Örnek müdahale ve iyileştirme önerileri:

- Şüpheli IP adresinin izlenmesi
- Tekrarlanan başarısız giriş denemelerinin incelenmesi
- Rate limiting uygulanması
- Güvenlik headerlarının eklenmesi
- Hatalı yapılandırmaların düzeltilmesi
- Log kayıtlarının düzenli olarak takip edilmesi
- Riskli alanların iyileştirilmesi

Bu yaklaşım sayesinde proje, yalnızca tespit yapan bir araç değil, aynı zamanda temel seviyede öneri sunan bir güvenlik analizi çalışması haline getirilmektedir.

---

## 📈 Projenin Katkısı

Bu proje sayesinde:

- Web güvenlik olaylarının nasıl analiz edildiği öğrenilmiştir
- Log verilerinin güvenlik açısından önemi anlaşılmıştır
- Şüpheli davranışların nasıl tespit edildiği simüle edilmiştir
- IP bazlı trafik analizinin temel mantığı kavranmıştır
- HTTP durum kodlarının güvenlik analizindeki rolü öğrenilmiştir
- Web uygulamalarında temel güvenlik kontrollerinin önemi anlaşılmıştır
- Incident response sürecinin temel mantığı kavranmıştır
- Gerçek dünya SOC ve web güvenliği süreçlerine giriş seviyesi bir bakış sağlanmıştır

---

## 📌 Genel Değerlendirme

Bu çalışma, siber güvenlik alanında özellikle **web güvenliği analizi, log analizi ve olay müdahale süreçlerine giriş seviyesinde bir uygulama** olarak tasarlanmıştır.

Proje, eğitim ve staj amacıyla geliştirilmiştir. Bu nedenle kullanılan senaryolar ve analiz yöntemleri temel seviyede tutulmuştur. Amaç, zararlı faaliyet gerçekleştirmek değil; sahip olunan veya izin verilen sistemlerde güvenlik durumunu incelemek, riskleri fark etmek ve iyileştirme önerileri geliştirmektir.

İlerleyen aşamalarda proje; saldırı tespiti, severity scoring, incident classification, incident response önerileri ve web güvenlik kontrol listesi gibi başlıklarla geliştirilecektir.
