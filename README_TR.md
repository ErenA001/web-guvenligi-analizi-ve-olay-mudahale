# Secure AI — Web Güvenliği Analizi ve Olay Müdahale Sistemi

Secure AI; Apache/Nginx erişim loglarını ve basit eğitim loglarını analiz eden, IP bazlı incident sınıflandırması ve severity üreten React + Flask tabanlı bir güvenlik operasyon panelidir.

![Secure AI masaüstü görünümü](docs/screenshots/dashboard-desktop.png)

## Tamamlanan sağlamlaştırmalar

- **Kimlik doğrulama:** Dashboard, chatbot ve log yükleme uçları oturum açılmadan kullanılamaz.
- **Çoklu kullanıcı izolasyonu:** Her tarayıcı oturumu için ayrı, rastgele çalışma alanı oluşturulur; yüklenen loglar ve aktif log durumu birbirine karışmaz.
- **Rate limiting:** Giriş, chatbot ve log yükleme istekleri IP + oturum bazında SQLite üzerinde, Gunicorn worker'ları arasında ortak olarak sınırlandırılır.
- **Paylaşımlı analiz cache'i:** Dosya yolu, inode, boyut, değişim zamanı ve analiz şema sürümüne göre SQLite cache uygulanır. Gunicorn worker'ları aynı sonucu paylaşır; dosya değiştiğinde analiz otomatik yenilenir.
- **Zaman pencereli tespit:** Brute force ve scanner tespiti varsayılan olarak **5 dakikalık kayan pencere** kullanır.
- **Genişletilmiş parser:** Apache Common/Combined, ISO zaman damgalı ve eski basit `IP METHOD PATH STATUS` biçimleri desteklenir.
- **Güvenli yükleme:** Uzantı, boyut, UTF-8, ikili veri, log satırı ve çalışma alanı yolu doğrulanır; kayıt atomik yapılır.
- **Otomatik testler:** Parser, detection, cache, authentication, rate limiting, API, upload ve session izolasyonu kapsanır.

NVIDIA NIM bağlantısının adresi, modeli ve `NVIDIA_API_KEY` kullanımı değiştirilmemiştir.

## Desteklenen log biçimleri

Apache/Nginx tarzı:

```text
203.0.113.5 - - [04/Aug/2026:00:10:05 +0300] "POST /login HTTP/1.1" 401 123
```

ISO zaman damgalı:

```text
2026-08-04T00:10:05+03:00 203.0.113.5 POST /login 401
```

Basit eğitim biçimi:

```text
203.0.113.5 POST /login 401
```

Zaman damgalı loglarda brute force ve scanner tespiti kayan zaman penceresiyle yapılır. Eski zaman damgasız loglar, geriye dönük uyumluluk için toplam eşik mantığıyla analiz edilir.

## Hızlı kurulum — macOS / Linux

```bash
cd web-guvenligi-analizi-ve-olay-mudahale
./start.sh
```

`start.sh` şunları otomatik yapar:

1. Başka bilgisayardan kalmış uyumsuz `venv` klasörünü temizler.
2. Python sanal ortamını oluşturur.
3. Gerekli bağımlılıkları kurar.
4. `.env` yoksa `.env.example` dosyasından oluşturur.
5. Giriş bilgilerini ve kalıcı session secret değerini üretir.
6. Uygulamayı Gunicorn ile başlatır.

İlk çalıştırmada otomatik şifre üretilirse terminalde gösterilir ve şu dosyada tutulur:

```text
.runtime/initial_credentials.txt
```

Bu düz metin dosyası ilk başarılı girişten sonra otomatik silinir. Şifre hash'i ve session secret `.runtime` altında kalır; bu klasör Git tarafından izlenmez.

Tarayıcı:

```text
http://localhost:5001
```

## Mevcut NVIDIA API anahtarını koruma

Teslim paketinde gerçek `.env` dosyası ve API anahtarı bulunmaz. Mevcut projenizi güncelliyorsanız eski `.env` dosyanızı koruyun. Yeni kurulumda:

```env
NVIDIA_API_KEY=YOUR_NVIDIA_API_KEY
```

API anahtarı yoksa dashboard, dosya analizi ve deterministik chatbot cevapları çalışır. Yalnızca harici model gerektiren AI çağrıları devre dışı kalır.

## Giriş ayarları

Kolay yerel kullanım:

```env
APP_USERNAME=admin
APP_PASSWORD=Guclu-Bir-Sifre-123!
```

Düz metin parola yerine hash kullanmak için:

```bash
source venv/bin/activate
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Guclu-Bir-Sifre-123!'))"
```

Çıktıyı `.env` içine ekleyin:

```env
APP_USERNAME=admin
APP_PASSWORD=
APP_PASSWORD_HASH=scrypt:...
```

HTTPS arkasında:

```env
SESSION_COOKIE_SECURE=1
```

## Varsayılan güvenlik limitleri

| İşlem | Limit | Pencere |
|---|---:|---:|
| Giriş | 5 istek | 5 dakika |
| Chatbot | 30 istek | 1 dakika |
| Log yükleme | 6 istek | 5 dakika |
| Brute force tespiti | 5 başarısız giriş | 5 dakika |
| Scanner tespiti | 5 farklı path | 5 dakika |

Değerler `scripts/config.py` dosyasından değiştirilebilir.

## API

Kimlik doğrulama cookie tabanlıdır. `/api/health` dışındaki API uçları aktif oturum ister.

```http
GET /api/health
GET /api/dashboard
POST /api/chat
POST /api/upload
```

Chatbot örneği:

```http
POST /api/chat
Content-Type: application/json

{
  "question": "En riskli IP hangisi?",
  "history": []
}
```

Log yükleme:

```http
POST /api/upload
Content-Type: multipart/form-data

log_file=<dosya>
```

Limit aşımında `429 Too Many Requests` ve `Retry-After` başlığı döner. Oturum yoksa `401 Unauthorized` döner.

## Testler

```bash
./run_tests.sh
```

Test kapsamı:

- Apache, ISO ve eski log parser'ı
- URL-encoded path traversal
- Kayan pencere brute force/scanner tespiti
- Query string kaynaklı scanner yanlış pozitifleri
- Analiz cache hit/invalidation/TTL
- SQLite rate limiter ve çoklu worker paylaşımı
- Otomatik ve tanımlı kimlik doğrulama
- Güvenli yükleme ve workspace sınırları
- İki eşzamanlı oturumda log izolasyonu
- API authentication, rate limiting ve security headers
- Chatbot konuşma geçmişi ve güvenli cevap kuralları

Nihai doğrulamada **56/56 otomatik test** ve iki-worker gerçek Gunicorn HTTP akışı başarılıdır. Ayrıntılar `docs/reports/FINAL_TEST_REPORT.md` dosyasındadır.

## Frontend geliştirme

Final paket hazır `frontend/dist` içerir; ilk çalıştırmada Node.js gerekmez. Kaynak React kodunu değiştirmek için Node.js 20.19+ kullanın:

```bash
cd frontend
npm install
npm run lint
npm run build
```

## Güvenlik notları

- Session cookie: `HttpOnly`, `SameSite=Strict`; HTTPS ortamında `Secure` etkinleştirilebilir.
- Session secret kalıcı ve rastgele üretilir; birden fazla Gunicorn worker aynı secret değerini kullanır.
- Açık yönlendirme engellenir; `next` yalnızca yerel yolları kabul eder.
- `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy` ve `Permissions-Policy` uygulanır.
- HSTS yalnızca HTTPS isteğinde eklenir.
- Proxy başlıkları güvenilir proxy yapılandırması olmadan kabul edilmez; istemci IP spoofing'i engellenir.
- Yüklenen dosyalar kullanıcı oturumuna özel klasörde `0600` izinleriyle saklanır.
- AI çıktıları incident sınıflandırmasını kesin saldırı kanıtı gibi sunmaması için filtrelenir.

## Teknolojiler

- Python 3.11+
- Flask 3
- Gunicorn
- SQLite
- React 19 / Vite
- NVIDIA NIM / Llama 3.1

## Geliştirici

Developed by **@JhreX**  
Web: **jhrex.com.tr**  
WhatsApp: **+44 7441 900754**

> Eğitim ve yalnızca yetkili sistemlerde güvenlik analizi amacıyla kullanılmalıdır. Incident sınıflandırmaları tek başına gerçek bir saldırının kesin kanıtı değildir.
