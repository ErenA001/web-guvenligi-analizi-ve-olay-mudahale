# 🛡️ Web Güvenliği Analizi ve Olay Müdahale

Bu repository, staj süreci boyunca geliştirilen **Web Güvenliği Analizi ve Olay Müdahale** projesini içermektedir.

Proje kapsamında web logları ve güvenlik olayları analiz edilerek şüpheli aktivitelerin tespit edilmesi, saldırı senaryolarının incelenmesi ve bu olaylara yönelik temel incident response (olay müdahale) yaklaşımının uygulanması hedeflenmektedir.

---

## 🎯 Proje Amacı

Bu projenin temel amacı:

- Web uygulamalarında oluşan güvenlik olaylarını analiz etmek
- Log kayıtları üzerinden şüpheli aktiviteleri tespit etmek
- Temel saldırı türlerini (brute force, unauthorized access vb.) incelemek
- Incident response mantığını simüle etmek
- Güvenlik analizi için basit bir otomasyon sistemi geliştirmek

---

## 🧠 Kapsam

Bu proje aşağıdaki alanları kapsamaktadır:

- Web server log analizi
- IP bazlı trafik analizi
- Failed login (401) tespiti
- Şüpheli davranış analizi
- Basit saldırı senaryolarının simülasyonu
- Python ile veri işleme ve analiz

---

## 🛠️ Kullanılan Teknolojiler

- Python 3
- Git & GitHub
- Log analiz mantığı
- CLI tabanlı geliştirme
- Temel siber güvenlik prensipleri

---

## 📁 Proje Yapısı
web-guvenligi-analizi-ve-olay-mudahale/
│
├── logs/
│ └── sample_access.log
│
├── scripts/
│ └── log_analyzer.py
│
├── Daily_Reports/
│ ├── 1_Gun_22_06_2026.md
│ ├── 2_Gun_23_06_2026.md
│ └── 3_Gun_24_06_2026.md
│
└── README.md

---

## ⚙️ Sistem Özellikleri

- IP adreslerine göre istek analizi
- Başarısız giriş denemelerinin tespiti
- Şüpheli IP davranışlarının belirlenmesi
- Log dosyası üzerinden saldırı analizi
- Basit incident detection mantığı

---

## 🧪 Çalışma Mantığı

1. Web server log dosyası okunur
2. IP adresleri analiz edilir
3. HTTP status kodları incelenir
4. Başarısız girişler tespit edilir (401)
5. Şüpheli IP’ler raporlanır
6. Olası brute force saldırıları işaretlenir

---

## 📊 Örnek Çıktı

=== IP TRAFFIC ANALYSIS ===
192.168.1.10 -> 3 request
192.168.1.11 -> 2 request

=== SUSPECT IPs ===
192.168.1.11 -> POSSIBLE BRUTE FORCE ATTACK


---

## 📅 Staj Süreci (Özet)

Proje, 30 günlük staj planı kapsamında geliştirilmiştir.

İlk 3 gün içerisinde:

- Proje yapısı oluşturulmuştur
- Web güvenliği temel kavramları incelenmiştir
- Log analizi için temel sistem kurulmuştur

---

## 🚀 Gelecek Geliştirmeler

- Grafik tabanlı saldırı analiz dashboard’u
- Flask tabanlı web arayüzü
- Gerçek zamanlı log izleme sistemi
- SIEM benzeri gelişmiş analiz sistemi
- Otomatik raporlama sistemi

---

## 👨‍💻 Not

Bu proje eğitim amaçlı geliştirilmiş olup, web güvenliği analizi ve incident response süreçlerini anlamak için hazırlanmıştır.
