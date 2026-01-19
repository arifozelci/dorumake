# DoruMake - Proje Geliştirme Planı

## Durum Açıklamaları
- [ ] Yapılacak
- [x] Tamamlandı
- [🔄] Devam Ediyor

---

## Faz 1: Temel Altyapı ✅

### 1.1 Proje Yapısı
- [x] Monorepo yapısı oluştur (apps/web, apps/robot, packages/database)
- [x] package.json ve turbo.json yapılandırması
- [x] .gitignore ve .env.example dosyaları
- [x] CLAUDE.md dokümantasyonu

### 1.2 Veritabanı
- [x] PostgreSQL şema tasarımı (Prisma)
- [x] Temel modeller: Supplier, Customer, Product, Order, Email
- [x] Enum tanımları: OrderStatus, EmailStatus, LogLevel
- [ ] Migration dosyaları oluştur
- [ ] Seed data (tedarikçiler, müşteriler)

### 1.3 Python Robot Altyapısı
- [x] requirements.txt
- [x] Pydantic settings yapılandırması
- [x] Loguru logging sistemi
- [x] Retry mekanizması (exponential backoff)
- [🔄] SQLAlchemy modelleri
- [ ] Database connection pool

---

## Faz 2: E-posta Servisi

### 2.1 IMAP Bağlantısı
- [ ] IMAP client (imapclient)
- [ ] E-posta polling (her 60 saniye)
- [ ] Yeni mail algılama
- [ ] SSL/TLS bağlantı

### 2.2 E-posta İşleme
- [ ] Mail parse (konu, gönderen, tarih)
- [ ] Attachment çıkarma (Excel dosyaları)
- [ ] Dosya kaydetme (downloads/)
- [ ] Email durumu güncelleme (DB)

### 2.3 Excel Parse
- [ ] openpyxl ile Excel okuma
- [ ] Sipariş verilerini çıkarma
- [ ] Ürün listesi oluşturma
- [ ] Tedarikçi belirleme (mail içeriğinden)
- [ ] Müşteri mapping

---

## Faz 3: Robot Modülleri

### 3.1 Base Robot
- [ ] Abstract base class
- [ ] Playwright browser yönetimi
- [ ] Screenshot alma (hata durumunda)
- [ ] Step logging
- [ ] Timeout handling

### 3.2 Mutlu Akü Robot (VisionNext PRM)
- [ ] Login fonksiyonu
- [ ] Müşteri seçimi (sağ üst dropdown)
- [ ] Menü navigasyonu (Satın Alma Siparişi)
- [ ] Yeni sipariş oluşturma (Oluştur butonu)
- [ ] Form doldurma:
  - [ ] Depo seçimi
  - [ ] Müşteri seçimi
  - [ ] Personel seçimi
  - [ ] Fiyat listesi seçimi
  - [ ] Ödeme tipi ve vadesi
  - [ ] Açıklama (Caspar sipariş no)
- [ ] Ürünler sekmesi
- [ ] ARA butonu ile ürün listesi
- [ ] Ürün adetleri girişi
- [ ] Kaydet (ürünler)
- [ ] Kaydet (sipariş)
- [ ] SAP Onayla butonu (KRİTİK!)
- [ ] Sipariş numarası alma

### 3.3 Mann & Hummel Robot (TecCom)
- [ ] Login fonksiyonu
- [ ] Menü navigasyonu (Dosya Yükle)
- [ ] CSV dosyası oluşturma (Siparis_formu_TecOrder_2018.csv formatı)
- [ ] Dosya yükleme
- [ ] Tedarikçi seçimi (FILTRON-MANN+HUMMEL Türkiye)
- [ ] Müşteri seçimi (Sapma gösteren sevk yeri adresi)
- [ ] TALEP butonu
- [ ] SİPARİŞ butonu
- [ ] Sipariş numarası alma

---

## Faz 4: Worker Sistemi

### 4.1 Email Worker
- [ ] IMAP polling loop
- [ ] Yeni mail işleme
- [ ] Queue'ya ekleme
- [ ] Hata yönetimi

### 4.2 Order Worker
- [ ] Sipariş kuyruğu dinleme
- [ ] Tedarikçiye göre robot seçimi
- [ ] Paralel işleme (Mann & Mutlu aynı anda)
- [ ] Durum güncellemeleri
- [ ] Retry logic

### 4.3 Scheduler
- [ ] APScheduler kurulumu
- [ ] Health check jobs
- [ ] Günlük özet rapor
- [ ] Eski log temizliği

---

## Faz 5: Bildirim Sistemi

### 5.1 E-posta Bildirimleri
- [ ] SMTP client
- [ ] Hata bildirimi template
- [ ] Günlük özet template
- [ ] Throttling (spam önleme)

### 5.2 Bildirim Kuralları
- [ ] LOGIN_FAILED → Anında bildirim
- [ ] SAP_CONFIRM_FAILED → Anında bildirim
- [ ] DAILY_SUMMARY → Her gün 18:00

---

## Faz 6: Admin Panel (Next.js)

### 6.1 Kurulum
- [ ] Next.js 14 App Router
- [ ] Tailwind CSS
- [ ] shadcn/ui components
- [ ] Prisma client

### 6.2 Sayfalar
- [ ] Dashboard (özet metrikler)
- [ ] Siparişler listesi
- [ ] Sipariş detay
- [ ] E-postalar listesi
- [ ] Log viewer
- [ ] Ayarlar

### 6.3 Özellikler
- [ ] Basit authentication
- [ ] Real-time updates (polling)
- [ ] Filtreleme ve arama
- [ ] Manuel sipariş tetikleme
- [ ] Screenshot görüntüleme

---

## Faz 7: API

### 7.1 FastAPI Endpoints
- [ ] GET /api/health
- [ ] GET /api/orders
- [ ] GET /api/orders/{id}
- [ ] POST /api/orders/{id}/retry
- [ ] GET /api/emails
- [ ] GET /api/logs
- [ ] GET /api/stats

### 7.2 WebSocket (opsiyonel)
- [ ] Real-time order updates
- [ ] Live log streaming

---

## Faz 8: Linux Deployment

### 8.1 Sunucu Hazırlığı
- [ ] SSH bağlantı testi
- [ ] Python 3.11+ kurulumu
- [ ] Node.js 18+ kurulumu
- [ ] PostgreSQL kurulumu
- [ ] Playwright dependencies

### 8.2 Uygulama Kurulumu
- [ ] /opt/dorumake dizini oluştur
- [ ] Git clone veya dosya transferi
- [ ] Python venv oluştur
- [ ] pip install -r requirements.txt
- [ ] playwright install chromium
- [ ] npm install (admin panel)

### 8.3 Servis Yapılandırması
- [ ] .env dosyası oluştur
- [ ] dorumake-robot.service (systemd)
- [ ] dorumake-web.service (systemd)
- [ ] nginx reverse proxy (opsiyonel)
- [ ] logrotate yapılandırması

### 8.4 Güvenlik
- [ ] Firewall kuralları
- [ ] SSL sertifikası (Let's Encrypt)
- [ ] Dosya izinleri (600 for .env)

---

## Faz 9: Test ve Doğrulama

### 9.1 Birim Testleri
- [ ] Parser testleri
- [ ] Database testleri
- [ ] Retry logic testleri

### 9.2 Entegrasyon Testleri
- [ ] E-posta okuma testi
- [ ] Mutlu Akü portal testi (demo)
- [ ] TecCom portal testi (demo)

### 9.3 End-to-End Test
- [ ] Tam sipariş döngüsü
- [ ] Hata senaryoları
- [ ] Recovery testleri

---

## Notlar

### Kritik Noktalar
1. **SAP Onayla butonu** - Mutlu Akü'de bu butona basılmazsa sipariş SAP'e aktarılmaz!
2. **CSV format** - Mann & Hummel için doğru format kullanılmalı
3. **Paralel çalışma** - İki robot birbirini beklemeden çalışmalı
4. **Retry** - Network hataları için exponential backoff

### Sunucu Bilgileri
- IP: 93.94.251.138
- User: ubuntu
- Dizin: /opt/dorumake

### Portal Bilgileri
- Mutlu: https://mutlu.visionnext.com.tr/Prm/UserAccount/Login
- TecCom: https://teccom.tecalliance.net/newapp/auth/welcome
