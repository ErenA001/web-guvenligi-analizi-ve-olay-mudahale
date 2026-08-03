SECURE AI - HIZLI KURULUM (macOS / Linux)

EN KOLAY YONTEM
1) Terminalde proje klasorune gir:
   cd web-guvenligi-analizi-ve-olay-mudahale

2) Calistir:
   ./start.sh

3) Terminalde gorunen ilk kullanici adi ve sifreyle giris yap:
   http://localhost:5001

start.sh su islemleri otomatik yapar:
- Baska bilgisayardan kalmis uyumsuz venv klasorunu temizler.
- Yeni Python sanal ortami olusturur.
- Gerekli paketleri kurar.
- .env yoksa .env.example dosyasindan olusturur.
- Ilk giris sifresini guvenli bicimde uretir.
- Gunicorn ile uygulamayi 5001 portunda baslatir.

MEVCUT NVIDIA API ANAHTARI
- Uygulama NVIDIA_API_KEY yapisini degistirmez.
- Eski .env dosyaniz varsa koruyun; paket icindeki .env.example sadece ornektir.
- Yeni kurulumda .env icine su bicimde ekleyin:
  NVIDIA_API_KEY=YOUR_NVIDIA_API_KEY

SABIT GIRIS SIFRESI TANIMLAMAK ICIN
.env dosyasinda:
  APP_USERNAME=admin
  APP_PASSWORD=Guclu-Bir-Sifre-123!

Daha guvenli hash kullanimi README_TR.md dosyasinda anlatilmistir.

TESTLER
  ./run_tests.sh

MANUEL KURULUM
  python3 -m venv venv
  source venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
  cp .env.example .env
  gunicorn -c gunicorn.conf.py app:app

NOTLAR
- Hazir React production build paket icindedir; ilk calistirmada npm gerekmez.
- Frontend kaynaklarini degistirirsen Node.js 20.19+ ile:
  cd frontend
  npm install
  npm run build
  cd ..
- HTTPS arkasinda SESSION_COOKIE_SECURE=1 yapin.
GUVENLIK UYARISI
- Eski kaynak ZIP paketinde API anahtari acik halde bulunuyordu. Eski anahtari iptal edip yenisini kullanin.
- Gercek .env veya opencode.json dosyasini Git deposuna ya da teslim ZIP paketine eklemeyin.

