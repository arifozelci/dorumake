# DoruMake - Sipariş Otomasyon Sistemi

## Proje Özeti

DoruMake, Castrol bayileri için tedarikçi portallarına otomatik sipariş girişi yapan bir RPA (Robotic Process Automation) sistemidir. İki farklı tedarikçi portalını destekler ve paralel çalışabilir. Uzun yıllar sorunsuz çalışması için enterprise-grade hata yönetimi, logging ve monitoring sistemleri içerir.

---

## Tedarikçiler ve Portal Bilgileri

### 1. Mann & Hummel (TecCom Portal)

| Bilgi | Değer |
|-------|-------|
| **Portal URL** | https://teccom.tecalliance.net/newapp/auth/welcome |
| **Kullanıcı** | dilsad.kaptan@dorufinansal.com |
| **Şifre** | Dilsad.2201 |
| **Yöntem** | CSV dosya yükleme |
| **Tedarikçi** | FILTRON-MANN+HUMMEL Türkiye |
| **Ürünler** | Hava filtreleri, polen filtreleri, yağ filtreleri |

**Sipariş Akışı (6 Adım):**
1. Login → Kullanıcı adı/şifre ile giriş
2. Menü → "Sorgulama ve sipariş" > "Dosya Yükle"
3. Dosya Seç → `Siparis_formu_TecOrder_2018.csv` formatında dosya
4. Tedarikçi Seç → "FILTRON-MANN+HUMMEL Türkiye"
5. Müşteri Seç → "Sapma gösteren sevk yeri adresi kullan" → Müşteri kodu (TRM56062 vb.)
6. TALEP → SİPARİŞ → Sipariş numarası al

**CSV Format (Siparis_formu_TecOrder_2018.csv):**
- Sıra No | Parça Numarası | Miktar | Parça Adı
- Maksimum 750 kalem

---

### 2. Mutlu Akü (VisionNext PRM Portal)

| Bilgi | Değer |
|-------|-------|
| **Portal URL** | https://mutlu.visionnext.com.tr/Prm/UserAccount/Login |
| **Kullanıcı** | burak.bakar@castrol.com |
| **Şifre** | 123456 |
| **Yöntem** | Manuel form doldurma |
| **Müşteri** | CASTROL (sağ üst köşeden seçilir) |
| **Ürünler** | Akü (EFB, Start-Stop, HD serisi) |

**Sipariş Akışı (11 Adım):**
1. Login → Kullanıcı adı/şifre ile giriş
2. Müşteri Seç → Sağ üst köşeden "CASTROL BATMAN DALAY PETROL" vb.
3. Menü → Sol menü > "Satış/Satın Alma" > "Satın Alma Siparişi"
4. Oluştur → "Oluştur" butonuna tıkla
5. Form Doldur:
   - Depo: A. Merkez Depo
   - Müşteri: CASTROL
   - Personel: Seç (dropdown)
   - Fiyat Listesi: Castrol Fiyat Listesi 25003
   - Ödeme Tipi: Açık Hesap
   - Ödeme Vadesi: 60 Gün
   - Açıklama: [Caspar Sipariş Numarası]
6. Ürünler Sekmesi → Sol üstten "Ürünler" sekmesine tıkla
7. ARA → Aktif ürün listesi gelir (palet içi miktarlarla)
8. Adet Gir → Her ürün için sipariş adedi girilir
9. Kaydet (Ürünler) → "Kaydet" → "Kaydedildi..." mesajı bekle → Ekranı kapat
10. Kaydet (Sipariş) → Sağ üst "Kaydet" butonu
11. SAP Onayla → "Siparişi Onayla" butonu → SAP'e aktarım (KRİTİK!)

**Örnek Ürün Kodları:**
- AF-CST-AUEFB-04-0630600-L52B13-01-0 → Castrol 12/63 EFB (Palet: 72)
- AF-CST-AUEFB-04-0720720-L53B13-01-0 → Castrol 12/72 EFB (Palet: 66)
- AF-CST-COSFB-00-1050760-C13B03-01-0 → Castrol 12/105 HD (Palet: 45)

---

## E-posta Bilgileri

| Bilgi | Değer |
|-------|-------|
| **E-posta** | dorumakerobot@gmail.com |
| **App Password** | mskfwezpwamducxw |
| **Protokol** | IMAP |
| **IMAP Host** | imap.gmail.com:993 |

Sipariş mailleri bu adrese gelir. Caspar sistemi (info@caspar.com.tr) Excel eki gönderir.

---

## Veritabanı Bilgileri

| Bilgi | Değer |
|-------|-------|
| **Tip** | SQL Server 2019 (Docker) |
| **Container** | sqlserver |
| **Port** | 1433 |
| **Kullanıcı** | sa |
| **Şifre** | KolayAlacak2025 |
| **Database** | DoruMake |

---

## Admin Panel Bilgileri

| Bilgi | Değer |
|-------|-------|
| **URL** | https://93-94-251-138.sslip.io |
| **Kullanıcı** | admin |
| **Şifre** | YkcBqTFO6qBKLeiC |

---

## Müşteri Kodları (Mapping)

| Müşteri | Mann & Hummel Kodu | Mutlu Akü Kodu |
|---------|-------------------|----------------|
| DALAY PETROL (Batman) | TRM56062 | CASTROL BATMAN DALAY PETROL |
| Diğer müşteriler | TRM56018 vb. | Mapping yapılacak |

---

## Teknik Mimari

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DoruMake SYSTEM (Linux Native)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐   ┌────────────────┐   ┌────────────────┐               │
│  │  ADMIN PANEL   │   │  EMAIL WORKER  │   │  ROBOT WORKERS │               │
│  │   (Next.js)    │   │   (Python)     │   │  (Playwright)  │               │
│  │   Port: 3000   │   │   IMAP Poll    │   │                │               │
│  │                │   │                │   │  ┌──────────┐  │               │
│  │  - Dashboard   │   │  - Fetch mail  │   │  │ Mann &   │  │               │
│  │  - Orders      │   │  - Parse Excel │   │  │ Hummel   │  │               │
│  │  - Logs        │   │  - Queue order │   │  └──────────┘  │               │
│  │  - Settings    │   │                │   │  ┌──────────┐  │               │
│  │  - Alerts      │   │                │   │  │ Mutlu    │  │               │
│  │                │   │                │   │  │ Akü      │  │               │
│  └───────┬────────┘   └───────┬────────┘   │  └──────────┘  │               │
│          │                    │            └───────┬────────┘               │
│          │                    │                    │                         │
│          └────────────────────┼────────────────────┘                         │
│                               │                                              │
│  ┌────────────────────────────▼────────────────────────────────┐            │
│  │                   SQL Server (Docker)                        │            │
│  │  - orders, order_items                                      │            │
│  │  - emails                                                   │            │
│  │  - suppliers                                                │            │
│  │  - system_logs                                              │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Redis Queue    │  │  File Watcher   │  │  Scheduler      │              │
│  │  (Job Queue)    │  │  (New files)    │  │  (APScheduler)  │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Proje Yapısı

```
DoruMake/
├── apps/
│   ├── web/                          # Next.js Admin Panel
│   │   ├── src/
│   │   │   ├── app/                  # App Router (pages)
│   │   │   │   ├── (dashboard)/      # Ana panel
│   │   │   │   ├── orders/           # Sipariş listesi
│   │   │   │   ├── emails/           # E-posta listesi
│   │   │   │   ├── logs/             # Log viewer
│   │   │   │   └── settings/         # Ayarlar
│   │   │   ├── components/           # React components
│   │   │   └── lib/                  # Utilities, API calls
│   │   └── package.json
│   │
│   └── robot/                        # Python Robot Service
│       ├── src/
│       │   ├── config/               # Configuration
│       │   │   ├── __init__.py
│       │   │   └── settings.py       # Pydantic settings
│       │   ├── db/                   # Database
│       │   │   ├── __init__.py
│       │   │   ├── connection.py     # SQLAlchemy connection
│       │   │   └── models.py         # ORM models
│       │   ├── email/                # Email service
│       │   │   ├── __init__.py
│       │   │   ├── fetcher.py        # IMAP fetcher
│       │   │   └── parser.py         # Email parser
│       │   ├── parser/               # File parsers
│       │   │   ├── __init__.py
│       │   │   ├── excel_parser.py   # Excel parser
│       │   │   └── csv_generator.py  # TecCom CSV generator
│       │   ├── robots/               # Supplier robots
│       │   │   ├── __init__.py
│       │   │   ├── base.py           # Abstract base robot
│       │   │   ├── mann_hummel.py    # TecCom robot
│       │   │   └── mutlu_aku.py      # VisionNext robot
│       │   ├── workers/              # Background workers
│       │   │   ├── __init__.py
│       │   │   ├── email_worker.py   # Email polling worker
│       │   │   ├── order_worker.py   # Order processing worker
│       │   │   └── scheduler.py      # APScheduler jobs
│       │   ├── api/                  # FastAPI endpoints
│       │   │   ├── __init__.py
│       │   │   ├── main.py           # FastAPI app
│       │   │   └── routes/           # API routes
│       │   ├── notifications/        # Alert system
│       │   │   ├── __init__.py
│       │   │   └── email_notifier.py # Email alerts
│       │   └── utils/                # Utilities
│       │       ├── __init__.py
│       │       ├── logger.py         # Loguru setup
│       │       └── retry.py          # Retry decorator
│       ├── screenshots/              # Error screenshots
│       ├── downloads/                # Downloaded files
│       ├── logs/                     # Log files
│       ├── requirements.txt
│       └── main.py                   # Entry point
│
├── packages/
│   └── database/                     # Shared Prisma schema
│       └── prisma/schema.prisma
│
├── scripts/                          # Deployment scripts
│   ├── install.sh                    # Linux installation
│   └── dorumake.service              # Systemd service
│
├── source/                           # Örnek dosyalar
├── .env.example
├── CLAUDE.md                         # Bu dosya
└── package.json
```

---

## Hata Yönetimi Stratejisi (Enterprise-Grade)

### 1. Retry Mekanizması

```python
# Her işlem için retry politikası
RETRY_CONFIG = {
    "login": {
        "max_attempts": 3,
        "wait_seconds": [5, 15, 30],  # Exponential backoff
        "on_failure": "notify_admin"
    },
    "navigation": {
        "max_attempts": 3,
        "wait_seconds": [2, 5, 10],
        "on_failure": "skip_and_log"
    },
    "form_fill": {
        "max_attempts": 2,
        "wait_seconds": [3, 10],
        "on_failure": "screenshot_and_notify"
    },
    "submit": {
        "max_attempts": 3,
        "wait_seconds": [5, 15, 30],
        "on_failure": "notify_admin"
    }
}
```

### 2. Hata Kategorileri

| Kategori | Seviye | Aksiyon | Screenshot |
|----------|--------|---------|------------|
| **LOGIN_FAILED** | CRITICAL | 3x retry → Admin bildirimi → Dur | Evet |
| **ELEMENT_NOT_FOUND** | ERROR | 3x retry → Log → Sonraki sipariş | Evet |
| **TIMEOUT** | WARNING | Sayfayı yenile → 2x retry | Hayır |
| **NETWORK_ERROR** | ERROR | 30sn bekle → 3x retry | Hayır |
| **VALIDATION_ERROR** | WARNING | Log → Sonraki sipariş | Hayır |
| **SAP_CONFIRM_FAILED** | CRITICAL | Admin bildirimi → Manuel müdahale | Evet |
| **UNEXPECTED_POPUP** | WARNING | Popup kapat → Devam et | Evet |
| **SESSION_EXPIRED** | ERROR | Re-login → Devam et | Hayır |

### 3. Screenshot Politikası

```python
# Sadece kritik hatalarda screenshot al
SCREENSHOT_ON = [
    "LOGIN_FAILED",
    "SAP_CONFIRM_FAILED",
    "ELEMENT_NOT_FOUND",
    "UNEXPECTED_POPUP",
    "ORDER_SUBMIT_FAILED"
]

# Screenshot kayıt formatı
# screenshots/{supplier}/{date}/{order_id}_{step}_{timestamp}.png
# Örnek: screenshots/mutlu_aku/2025-01-19/ORD123_login_143052.png
```

### 4. Logging Yapısı

```python
# Log seviyeleri ve hedefleri
LOGGING = {
    "console": "INFO",      # Terminalde görünen
    "file": "DEBUG",        # Detaylı dosya logu
    "database": "WARNING",  # DB'ye yazılan

    # Log dosyaları (logrotate ile yönetilecek)
    "files": {
        "robot.log": "DEBUG",        # Tüm robot aktivitesi
        "error.log": "ERROR",        # Sadece hatalar
        "orders.log": "INFO",        # Sipariş işlemleri
        "email.log": "INFO"          # E-posta işlemleri
    },

    # Log retention (gün)
    "retention": {
        "debug": 7,
        "info": 30,
        "error": 90
    }
}
```

### 5. Bildirim Sistemi

```python
# Admin bildirim kanalları
NOTIFICATIONS = {
    "email": {
        "enabled": True,
        "recipients": ["arif.ozelci@dorufinansal.com", "dilsad.kaptan@dorufinansal.com"],
        "on_events": ["LOGIN_FAILED", "SAP_CONFIRM_FAILED", "DAILY_SUMMARY"]
    },
    "webhook": {
        "enabled": False,  # İleride eklenebilir
        "url": None
    }
}

# Bildirim throttling (spam önleme)
# Aynı hata için 1 saat içinde max 3 bildirim
```

---

## Paralel Çalışma Stratejisi

### Worker Mimarisi

```
                    ┌─────────────────┐
                    │   Main Process  │
                    │   (Supervisor)  │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │ Email Worker│   │ Mann Worker │   │ Mutlu Worker│
    │  (Async)    │   │  (Async)    │   │  (Async)    │
    │             │   │             │   │             │
    │ Poll IMAP   │   │ Process     │   │ Process     │
    │ Parse Excel │   │ TecCom      │   │ VisionNext  │
    │ Queue Order │   │ Orders      │   │ Orders      │
    └─────────────┘   └─────────────┘   └─────────────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   SQL Server    │
                    │   (Docker)      │
                    └─────────────────┘
```

### Kurallar

1. **Bağımsız Kuyruklar:** Her tedarikçi için ayrı sipariş kuyruğu
2. **Aynı Anda Çalışma:** Mann & Hummel siparişi işlenirken Mutlu Akü de paralel çalışır
3. **Kaynak Paylaşımı:** Database ve e-posta servisi paylaşımlı, robotlar bağımsız
4. **Browser İzolasyonu:** Her robot kendi browser context'ini kullanır
5. **Graceful Shutdown:** SIGTERM geldiğinde mevcut işlemi tamamla, yenisine başlama

---

## Health Check & Monitoring

### Sistem Sağlık Kontrolleri

```python
HEALTH_CHECKS = {
    "database": {
        "interval": 60,  # saniye
        "timeout": 5,
        "on_failure": "alert"
    },
    "email_server": {
        "interval": 300,
        "timeout": 10,
        "on_failure": "alert"
    },
    "mann_portal": {
        "interval": 600,
        "timeout": 30,
        "on_failure": "log"  # Portal değişmiş olabilir
    },
    "mutlu_portal": {
        "interval": 600,
        "timeout": 30,
        "on_failure": "log"
    }
}
```

### Dashboard Metrikleri

- Bugün işlenen sipariş sayısı
- Başarı/başarısızlık oranı
- Ortalama işlem süresi
- Son 24 saat hata sayısı
- Kuyrukta bekleyen sipariş
- Son başarılı/başarısız sipariş

---

## Güvenlik Önlemleri

1. **Şifre Saklama:** Tüm şifreler environment variable olarak tutulacak
2. **Database:** Sadece localhost erişimi, remote bağlantı kapalı
3. **Admin Panel:** Basit auth (ileride OAuth eklenebilir)
4. **Log Gizliliği:** Şifreler ve hassas veriler loglarda maskelenecek
5. **File Permissions:** 600 for .env, 755 for scripts

---

## Linux Sunucu Bilgileri

| Bilgi | Değer |
|-------|-------|
| **Sunucu Adı** | WEBKASVR |
| **IP Adresi** | 93.94.251.138 |
| **İşletim Sistemi** | Ubuntu |
| **Kullanıcı** | ubuntu |
| **Şifre** | hE6RZ!Xa |
| **Kurulum Dizini** | /opt/dorumake |

**ÖNEMLİ:** Sunucuda başka uygulamalar var. Onlara dokunmadan sadece `/opt/dorumake` dizininde çalışılacak.

---

## Linux Deployment

### PM2 Services

```bash
# Çalışan servisler
pm2 status

# Servisler:
# - dorumake-web         (Next.js Admin Panel - Port 3000)
# - dorumake-api         (FastAPI Backend - Port 8000)
# - dorumake-email-worker (Email Polling Worker)

# Yeniden başlatma
pm2 restart dorumake-web
pm2 restart dorumake-api
pm2 restart dorumake-email-worker

# Logları görme
pm2 logs dorumake-api --lines 50
```

### Logrotate

```
# /etc/logrotate.d/dorumake
/opt/dorumake/apps/robot/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Önemli Kurallar

1. **Paralel Çalışma:** Mann & Hummel ve Mutlu Akü robotları birbirini BEKLEMEMELİ
2. **Linux Native:** Docker kullanılmayacak, systemd service olarak çalışacak
3. **Hata Yönetimi:** Kritik hatalarda screenshot + admin bildirimi
4. **Retry:** Her işlem için exponential backoff ile retry
5. **SAP Onay:** Mutlu Akü'de "Siparişi Onayla" butonu ZORUNLU (aksi halde SAP'e düşmez)
6. **CSV Format:** Mann & Hummel için `Siparis_formu_TecOrder_2018.csv` formatı kullanılmalı
7. **Logging:** Tüm işlemler loglanmalı, 90 gün retention
8. **Monitoring:** Health check + dashboard metrikleri

---

## Geliştirme Öncelikleri

1. Database şeması ve modeller
2. E-posta servisi (IMAP fetch + Excel parse)
3. Mutlu Akü robotu (daha karmaşık)
4. Mann & Hummel robotu (CSV upload)
5. Admin panel (dashboard + log viewer)
6. Bildirim sistemi (e-posta alerts)
7. Linux deployment scripts
