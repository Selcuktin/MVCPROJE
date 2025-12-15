# 🖥️ Yerel Bilgisayarda Çalıştırma Rehberi

Sunucu kurmadan Windows bilgisayarınızda tam özellikli uzaktan eğitim sistemi!

## ✅ ŞU AN AKTİF OLAN SİSTEM

Sisteminiz **zaten çalışıyor!** SQLite database ile tam özellikli.

---

## 🚀 HEMEN BAŞLATMA

### Adım 1: Development Server'ı Çalıştır

```bash
cd C:\Users\mtn2\Downloads\OKULPROJE
python manage.py runserver
```

### Adım 2: Tarayıcıda Aç

```
Ana Sayfa: http://localhost:8000/
Admin Panel: http://localhost:8000/admin/
API Docs: http://localhost:8000/api/docs/
```

### Adım 3: Admin Kullanıcısı Oluştur (İlk Kez)

```bash
python manage.py createsuperuser
```

Bilgileri girin:
- Username: admin
- Email: admin@example.com
- Password: (güçlü şifre)

---

## 🎯 YEREL KULLANIM İÇİN ÖNERİLEN SETUP

### Seçenek 1: SQLite (Şu Anki - ÖNERİLEN)

**Artıları:**
- ✅ Zaten kurulu ve çalışıyor
- ✅ Kurulum gerektirmiyor
- ✅ Tek dosya database (kolay yedekleme)
- ✅ Küçük/orta projelerde mükemmel performans
- ✅ 30-50 kullanıcıya kadar rahat çalışır

**Eksi:**
- ⚠️ Çok fazla eşzamanlı yazma işleminde yavaşlayabilir
- ⚠️ Network üzerinden erişilemez (sadece localhost)

**Şu Anki Durum:** ✅ Aktif ve çalışıyor!

### Seçenek 2: PostgreSQL (Yerel Kurulum)

Windows'ta PostgreSQL kurarsanız daha profesyonel olur.

**Kurulum:**

1. **PostgreSQL İndir ve Kur:**
   - https://www.postgresql.org/download/windows/
   - Varsayılan ayarlarla kur
   - Password belirle (örn: postgres123)

2. **Database Oluştur:**

pgAdmin'i aç veya CMD'de:

```bash
psql -U postgres
```

PostgreSQL içinde:

```sql
CREATE DATABASE uzaktanogrenme;
\q
```

3. **Django Settings Güncelle:**

`config/settings.py` içinde:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'uzaktanogrenme',
        'USER': 'postgres',
        'PASSWORD': 'postgres123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

4. **psycopg2 Kur:**

```bash
pip install psycopg2-binary
```

5. **Migrate Et:**

```bash
python manage.py migrate
python manage.py createsuperuser
```

### Seçenek 3: MongoDB (NoSQL - Alternatif)

Django'da MongoDB kullanımı biraz farklı ama mümkün.

**Not:** Django ORM MongoDB'yi native desteklemiyor, `djongo` gerekir.

**Önermiyorum çünkü:**
- Mevcut kodlar PostgreSQL/SQLite için yazıldı
- Ekstra kütüphane gerektirir
- Relational database daha uygun bu proje için

---

## 🔧 ÖNERİLEN SETUP: SQLite + Redis (Opsiyonel)

### Sadece Cache İçin Redis (Opsiyonel)

Redis performansı artırır ama zorunlu değil.

#### Windows'ta Redis Kurulumu:

1. **Memurai İndir (Redis for Windows):**
   - https://www.memurai.com/get-memurai
   - Ücretsiz developer edition

2. **Kur ve Başlat:**
   - Installer'ı çalıştır
   - Service olarak başlat

3. **Django'ya Ekle:**

```bash
pip install django-redis redis
```

`config/settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

**Not:** Redis olmadan da sistem çalışır, sadece cache daha yavaş olur.

---

## 🌐 LOCAL NETWORK'TE PAYLAŞMA

Aynı WiFi'daki diğer cihazlardan erişmek için:

### Adım 1: IP Adresinizi Bulun

```bash
ipconfig
```

IPv4 adresinizi not edin (örn: 192.168.1.100)

### Adım 2: Server'ı IP ile Başlatın

```bash
python manage.py runserver 0.0.0.0:8000
```

### Adım 3: ALLOWED_HOSTS Güncelleyin

`config/settings.py`:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '192.168.1.100', '*']
```

### Adım 4: Diğer Cihazlardan Erişin

```
http://192.168.1.100:8000
```

**Güvenlik Uyarısı:** `'*'` production'da kullanılmamalı!

---

## 💾 DATABASE YEDEKLENMESİ

### SQLite Yedekleme (Çok Kolay!)

Database dosyası: `db.sqlite3`

**Manuel Yedek:**

```bash
copy db.sqlite3 backups\db_backup_2025-12-14.sqlite3
```

**Otomatik Yedek Script (Windows):**

`backup.bat` oluşturun:

```batch
@echo off
set BACKUP_DIR=C:\Users\mtn2\Downloads\OKULPROJE\backups
set DATE=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%
set DATE=%DATE: =0%

mkdir %BACKUP_DIR% 2>nul

copy db.sqlite3 "%BACKUP_DIR%\db_%DATE%.sqlite3"
echo Backup completed: %DATE%

REM Keep only last 7 backups
forfiles /p "%BACKUP_DIR%" /m "db_*.sqlite3" /d -7 /c "cmd /c del @path"
```

**Task Scheduler'a Ekle:**
- Task Scheduler'ı aç
- "Create Basic Task"
- Her gün saat 02:00'de `backup.bat` çalıştır

---

## 📱 MOBILE ERIŞIM

Aynı WiFi'deyken telefon veya tabletten erişebilirsiniz:

1. Server'ı 0.0.0.0:8000 ile başlatın
2. Telefondan: `http://192.168.1.100:8000`
3. Responsive olduğu için mobilde güzel görünür (Bootstrap 5)

---

## 🎮 KULLANIM SENARYOLARI

### Senaryo 1: Sadece Sen Kullanacaksan
- ✅ SQLite yeterli
- Server: `python manage.py runserver`
- Erişim: `http://localhost:8000`

### Senaryo 2: Aynı Evdeki Cihazlar
- ✅ SQLite + Network sharing
- Server: `python manage.py runserver 0.0.0.0:8000`
- Erişim: `http://[YOUR-IP]:8000`

### Senaryo 3: 5-10 Kişilik Grup (Aynı Ağda)
- ✅ SQLite veya PostgreSQL
- Server: `python manage.py runserver 0.0.0.0:8000`
- Opsiyonel: Redis cache ekle

### Senaryo 4: 50+ Kullanıcı / İnternet Erişimi
- ❌ Production deployment gerekir (sunucu)
- PostgreSQL + Redis zorunlu
- Gunicorn + Nginx

---

## 🔥 HIZLI BAŞLATMA SCRIPTI

`start.bat` oluşturun:

```batch
@echo off
echo ================================
echo UZAKTAN EGITIM SISTEMI BASLATILIYOR
echo ================================
echo.

cd C:\Users\mtn2\Downloads\OKULPROJE

echo [1/3] Aktivating virtual environment...
call venv\Scripts\activate

echo [2/3] Checking migrations...
python manage.py migrate --no-input

echo [3/3] Starting server...
echo.
echo ================================
echo SERVER BASLATILDI!
echo ================================
echo.
echo Ana Sayfa:     http://localhost:8000
echo Admin Panel:   http://localhost:8000/admin
echo API Docs:      http://localhost:8000/api/docs
echo.
echo CTRL+C ile durdurun
echo.

python manage.py runserver

pause
```

**Kullanımı:** `start.bat` dosyasına çift tıkla!

---

## 🛠️ SORUN GİDERME

### Port 8000 Kullanımda

```bash
# Farklı port kullan
python manage.py runserver 8080
```

### SQLite Locked Hatası

```bash
# Server'ı durdur (CTRL+C)
# Tekrar başlat
python manage.py runserver
```

### Static Files Görünmüyor

```bash
python manage.py collectstatic
```

Development'ta gerek yok ama:

```python
# settings.py
DEBUG = True  # Bu True olmalı development'ta
```

---

## 📊 PERFORMANS İPUÇLARI

### SQLite Optimization

`config/settings.py` ekle:

```python
# SQLite performance tuning
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
            'journal_mode': 'WAL',  # Write-Ahead Logging
        }
    }
}
```

### Cache Without Redis

Redis yoksa, dosya bazlı cache:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'C:/Users/mtn2/Downloads/OKULPROJE/cache',
    }
}
```

---

## 🎯 ÖNERİM: BU SETUP İLE DEVAM ET!

**Şu anki sisteminiz:**
- ✅ Tam özellikli çalışıyor
- ✅ SQLite ile hızlı ve stabil
- ✅ 30-50 kullanıcıya kadar ölçeklenebilir
- ✅ Kurulum gerektirmiyor
- ✅ Yedekleme çok kolay (tek dosya)

**Ne zaman production'a geçmeli:**
- 50+ eşzamanlı kullanıcı
- İnternet üzerinden erişim
- 7/24 çalışması gerekiyor
- Multiple server instance

---

## 🚀 ŞİMDİ YAPILACAKLAR

1. **Server'ı Başlat:**
```bash
cd C:\Users\mtn2\Downloads\OKULPROJE
python manage.py runserver
```

2. **Admin Kullanıcısı Oluştur:**
```bash
python manage.py createsuperuser
```

3. **Tarayıcıda Aç:**
```
http://localhost:8000/admin
```

4. **Test Et:**
   - Dönem oluştur
   - Ders ekle
   - Öğrenci/öğretmen profili oluştur
   - Kayıt yap
   - Not gir

---

**✅ HAZIRSINIZ! Sisteminiz tamamen çalışıyor ve kullanıma hazır!**

**Soru:** Aynı ağdaki başka cihazlardan da erişmek istiyor musunuz?
