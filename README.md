# 🖥️ mrzgr — Merkezi Helpdesk Yönetim Sistemi

Kurumsal ortamlarda teknik destek taleplerini, demirbaş envanterini ve uzaktan masaüstü erişimini tek çatı altında toplayan Django tabanlı web uygulaması.

---

## 📌 Proje Hakkında

Geleneksel destek süreçleri; dağınık e-posta zincirleri, takibi güç sözlü talepler ve yetersiz raporlama üzerine kurulu olduğundan kurumsal hafıza oluşturmayı engeller. **mrzgr**, bu soruna yönelik geliştirilen tam kapsamlı bir yardım masası çözümüdür.

Her talep bir **ticket** olarak kaydedilir, önceliklendirilir, ilgili personele atanır ve çözüm sonrasında değerlendirilir. Sistem aynı zamanda cihaz envanterini yönetir ve teknik personelin kullanıcı bilgisayarlarına doğrudan tarayıcı üzerinden bağlanmasına olanak tanır.

---

## ✨ Özellikler

### 🎫 Ticket Yönetimi
- Web arayüzü veya e-posta ile ticket açma
- Personel atama ve öncelik sınıflandırması (Kritik / Normal / Düşük)
- SLA takibi — 4 saat uyarı, 24 saat kritik eşiği
- Görev notları, dosya ekleri ve görev geçmişi
- Tamamlanma sonrası otomatik e-posta bildirimi ve memnuniyet anketi

### 📡 Posta Botu
- Gmail IMAP üzerinden gelen kutusu dinleme (60 sn döngü)
- Yalnızca sistemde kayıtlı e-posta adreslerinden gelen mailleri ticket'a dönüştürür
- Tanımsız gönderenler otomatik olarak reddedilir
- Ekli dosyalar görev dosyaları olarak kaydedilir

### 🖥️ Demirbaş & Uzaktan Erişim
- Cihaz envanteri (Laptop, Telefon, Monitör, Yazıcı, Diğer)
- Her cihaza IP, RDP ve VNC bağlantı bilgisi tanımlama
- **Akıllı yönlendirme:** VNC şifresi tanımlıysa → noVNC; sadece RDP bilgisi varsa → Apache Guacamole
- Tarayıcı üzerinden gerçek zamanlı ekran erişimi (noVNC + websockify)
- Cihaz bazında görev geçmişi

### 👥 Personel & Raporlama
- Personel profil sayfası (departman, unvan, telefon, fotoğraf)
- Personel kartı: çözülen görev sayısı, ortalama memnuniyet puanı
- Yönetici rapor ekranı + Excel dışa aktarma
- Duyuru sistemi (Normal / Acil / Kutlama)
- Gerçek zamanlı bildirim paneli

---

## 🏗️ Mimari

```
Kullanıcı Tarayıcısı
        │
        ▼
  Django (Python)
        │
        ├── PostgreSQL  ──── tüm veriler
        │
        ├── VNC şifresi tanımlı mı?
        │       ├── Evet ──→ websockify → UltraVNC (port 5900)
        │       └── Hayır ─→ Apache Guacamole → RDP  (port 3389)
        │
        └── Posta Botu ────→ Gmail IMAP → yeni ticket
```

| Servis | Teknoloji | Port |
|---|---|---|
| Web uygulaması | Django | 8000 |
| Veritabanı | PostgreSQL | 5433 |
| VNC proxy | noVNC + websockify | 6080 |
| RDP gateway | Apache Guacamole | 8081 |
| Guacamole daemon | guacd | 4822 |

---

## 🛠️ Teknoloji Yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.10+, Django 4.2 |
| Veritabanı | PostgreSQL, psycopg2 |
| Frontend | HTML5, CSS3, Bootstrap, JavaScript |
| Konteynerleştirme | Docker, Docker Compose |
| Uzaktan Erişim (VNC) | noVNC, websockify |
| Uzaktan Erişim (RDP) | Apache Guacamole |
| Raporlama | openpyxl |
| Görsel İşleme | Pillow |

---

## 🚀 Kurulum

### Gereksinimler

- Docker & Docker Compose
- Python 3.10+
- Uzaktan bağlanılacak Windows makinelerde [UltraVNC Server](https://www.uvnc.com/)

### 1. Depoyu klonlayın

```bash
git clone https://github.com/kullanici_adi/mrzgr.git
cd mrzgr
```

### 2. Ortam değişkenlerini ayarlayın

```bash
cp .env.example .env
```

`.env` dosyasını açıp tüm değerleri doldurun (SECRET_KEY, veritabanı şifresi, e-posta bilgileri, NOVNC_HOST).

### 3. Guacamole yapılandırmasını oluşturun

```bash
cp guac_config/user-mapping.xml.example guac_config/user-mapping.xml
```

`user-mapping.xml` dosyasını açıp kullanıcı adı, şifre ve hedef IP'yi düzenleyin.

### 4. Docker servislerini başlatın

```bash
docker compose up -d
```

### 5. Veritabanı migrasyonlarını çalıştırın

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Geliştirme sunucusunu başlatın

```bash
python manage.py runserver
```

Uygulama `http://127.0.0.1:8000` adresinde çalışmaya başlar.

### 7. (Opsiyonel) Posta botunu başlatın

```bash
python manage.py mail_oku
```

Bot, her 60 saniyede bir gelen kutusu kontrol eder.

---

## 📂 Dizin Yapısı

```
mrzgr/
├── config/
│   ├── settings.py          # Uygulama ayarları (env'den okur)
│   ├── urls.py              # URL yönlendirmeleri
│   └── wsgi.py
├── yonetim/
│   ├── models.py            # Veri modelleri
│   ├── views.py             # İş mantığı & sayfa render
│   ├── forms.py             # Form tanımları
│   ├── admin.py             # Django admin yapılandırması
│   ├── templates/           # HTML şablonları
│   └── management/
│       └── commands/
│           └── mail_oku.py  # Posta botu
├── guac_config/
│   ├── user-mapping.xml         # Gerçek yapılandırma (.gitignore'da)
│   └── user-mapping.xml.example # Örnek şablon
├── novnc_tokens/            # websockify oturum tokenları (.gitignore'da)
├── Dockerfile               # Django uygulama imajı
├── Dockerfile.novnc         # noVNC + websockify imajı
├── docker-compose.yml
├── requirements.txt
├── .env                     # Gerçek şifreler (.gitignore'da)
└── .env.example             # Şablon — repoda görünür
```

---

## 🗺️ Geliştirme Süreci

**1. Dönem — Temel Altyapı**
- Ticket sistemi (oluşturma, atama, takip, arşivleme)
- Posta botu ile otomatik ticket oluşturma
- Personel profil ve bildirim sistemi
- Memnuniyet anketi
- Raporlama ve Excel dışa aktarma
- Docker + PostgreSQL altyapısı

**2. Dönem — Uzaktan Erişim & Cihaz Yönetimi**
- Demirbaş envanteri ve cihaz–görev ilişkilendirme
- Apache Guacamole entegrasyonu (RDP)
- noVNC + websockify entegrasyonu (VNC) — Guacamole'un UltraVNC ile yaşadığı ekran güncelleme uyumsuzluğu nedeniyle VNC için tercih edildi
- Akıllı bağlantı yönlendirme (VNC şifresi varsa noVNC, yoksa Guacamole)
- Token tabanlı VNC oturum yönetimi

---

## 📄 Lisans

Bu proje Mersin Üniversitesi Bilişim Sistemleri ve Teknolojileri programı bitirme projesi kapsamında geliştirilmiştir.
