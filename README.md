# Django MVC Kurs Yönetim Sistemi

Modern ve kullanıcı dostu bir kurs yönetim sistemi. Django framework'ü kullanılarak MVC (Model-View-Controller) mimarisine uygun olarak geliştirilmiştir.

## 🚀 Özellikler

### 👥 Kullanıcı Yönetimi
- Rol tabanlı yetkilendirme (Öğrenci, Öğretmen, Admin)
- Güvenli kayıt ve giriş sistemi
- Profil yönetimi

### 📚 Ders Yönetimi
- Ders oluşturma, düzenleme, silme (CRUD)
- Ders grupları yönetimi
- Öğrenci kayıt sistemi
- Detaylı ders bilgileri

### 📝 Ödev Sistemi
- Ödev oluşturma ve atama
- Online ödev teslim sistemi
- Ödev değerlendirme ve notlandırma
- Son teslim tarihi kontrolü

### 📢 Duyuru Sistemi
- Ders bazlı duyurular
- Durum yönetimi (Aktif/Pasif/Süresi Dolmuş)
- Duyuru düzenleme ve silme

### 📊 Not Sistemi
- Vize, Final, Bütünleme notları
- Otomatik harf notu hesaplama
- Not görüntüleme ve düzenleme
- Detaylı not raporları

## 🛠️ Teknolojiler

- **Backend:** Django 4.2.7
- **Frontend:** Bootstrap 5, Font Awesome
- **Database:** SQLite3 (Geliştirme)
- **Authentication:** Django Auth System
- **Forms:** Django Forms + Crispy Forms

## 📦 Kurulum

### Gereksinimler
- Python 3.8+
- pip

### Adımlar

1. **Projeyi klonlayın**
```bash
git clone <repo-url>
cd OKULPROJE
```

2. **Sanal ortam oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Database migration**
```bash
python manage.py migrate
```

5. **Örnek veri oluşturun**
```bash
python manage.py create_sample_users
python manage.py create_sample_data
python manage.py add_sample_announcements_assignments
```

6. **Sunucuyu başlatın**
```bash
python manage.py runserver
```

7. **Tarayıcıda açın**
```
http://127.0.0.1:8000
```

## 👤 Demo Kullanıcılar

### Admin
- **Kullanıcı Adı:** admin
- **Şifre:** admin123

### Öğretmen
- **Kullanıcı Adı:** teacher1
- **Şifre:** teacher123

### Öğrenci
- **Kullanıcı Adı:** student1
- **Şifre:** student123

## 📁 Proje Yapısı

```
OKULPROJE/
├── apps/                       # Django uygulamaları
│   ├── courses/               # Ders yönetimi
│   ├── students/              # Öğrenci yönetimi
│   ├── teachers/              # Öğretmen yönetimi
│   ├── notes/                 # Not yönetimi
│   └── users/                 # Kullanıcı yönetimi
├── config/                    # Proje ayarları
│   ├── settings.py
│   └── urls.py
├── templates/                 # HTML şablonları
├── static/                    # CSS, JS, görseller
├── utils/                     # Yardımcı fonksiyonlar
├── manage.py
└── requirements.txt
```

## 🎯 MVC Mimarisi

### Model (Veri Katmanı)
- `apps/*/models.py` - Veritabanı modelleri
- Django ORM kullanımı

### View (Sunum Katmanı)
- `templates/` - HTML şablonları
- Bootstrap ile responsive tasarım

### Controller (İş Mantığı)
- `apps/*/views.py` - İş mantığı ve veri işleme
- Class-Based Views (CBV) ve Function-Based Views (FBV)

## 🔐 Güvenlik

- Django authentication sistemi
- CSRF koruması
- XSS koruması
- Rol tabanlı erişim kontrolü
- Form validasyonu

## 📝 Yönetim Komutları

```bash
# Örnek kullanıcılar oluştur
python manage.py create_sample_users

# Örnek ders ve öğrenci verileri oluştur
python manage.py create_sample_data

# Örnek duyuru ve ödevler ekle
python manage.py add_sample_announcements_assignments

# Veritabanını sıfırla ve yeni veri oluştur
python manage.py flush
python manage.py migrate
python manage.py create_sample_users
python manage.py create_sample_data
```

## 🚦 URL Yapısı

- `/` - Ana sayfa
- `/admin/` - Django admin paneli
- `/courses/` - Ders işlemleri
- `/students/` - Öğrenci işlemleri
- `/teachers/` - Öğretmen işlemleri
- `/notes/` - Not işlemleri
- `/accounts/` - Kullanıcı işlemleri

## 📸 Ekran Görüntüleri

### Ana Sayfa
- Modern ve kullanıcı dostu arayüz
- Öğrenci ve öğretmen portalları

### Öğretmen Paneli
- Ders grupları yönetimi
- Ödev ve duyuru yönetimi
- Öğrenci notlandırma

### Öğrenci Paneli
- Kayıtlı dersler
- Ödev teslim sistemi
- Not görüntüleme

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

## 📧 İletişim

Proje Hakkında Sorularınız İçin: [GitHub Issues](https://github.com/yourusername/repo/issues)

---

**Not:** Bu proje Django MVC pattern'ine uygun, temiz kod prensipleriyle geliştirilmiş, modüler ve genişletilebilir bir yapıya sahiptir.
