# 🎓 Uzaktan Öğrenme Yönetim Sistemi

Modern, güvenli ve ölçeklenebilir bir uzaktan eğitim platformu. Selçuk Üniversitesi/Moodle benzeri tam kapsamlı özellikler.

## 🌟 Özellikler

### Akademik Yönetim
- ✅ Dönem yönetimi (Güz/Bahar/Yaz)
- ✅ Ders ve grup yönetimi
- ✅ 4 farklı kayıt yöntemi (Manuel, Self, Key, Cohort)
- ✅ Kayıt kuralları (Önkoşul, bölüm, yarıyıl kısıtları)
- ✅ Otomatik kapasite kontrolü

### Not Yönetimi
- ✅ Ağırlıklı not sistemi (GradeCategory)
- ✅ Çoklu değerlendirme kalemleri
- ✅ Otomatik harf notu hesaplama
- ✅ Transkript oluşturma
- ✅ Toplu not girişi

### Sınav & Quiz
- ✅ Soru bankası sistemi
- ✅ 6 soru tipi (Çoktan seçmeli, Doğru/Yanlış, Essay, vb.)
- ✅ Zamanlayıcı ve otomatik teslim
- ✅ Çoklu deneme hakkı
- ✅ IP kısıtlama

### İletişim
- ✅ Forum sistemi (konular, cevaplar, çözüm işaretleme)
- ✅ 1:1 mesajlaşma
- ✅ Grup mesaj dizileri
- ✅ Event-driven bildirimler
- ✅ Email entegrasyonu

### İçerik & Aktivite
- ✅ Ödev sistemi
- ✅ Duyurular
- ✅ Aktivite tamamlama takibi
- ✅ Önkoşul bazlı erişim kontrolü
- ✅ İzin tabanlı içerik indirme

### Raporlama
- ✅ Öğrenci transkriptleri
- ✅ Öğretmen analitikleri
- ✅ CSV/PDF export
- ✅ Not dağılım istatistikleri

### Güvenlik & Compliance
- ✅ 2FA (Email-based)
- ✅ Rate limiting (DDoS koruması)
- ✅ KVKK uyumluluğu
- ✅ HTTPS/SSL zorunluluğu
- ✅ Güvenli çerez yönetimi

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Nginx (production için)

### Adımlar

1. **Repo'yu klonlayın:**
```bash
git clone <repository-url>
cd OKULPROJE
```

2. **Virtual environment oluşturun:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **Environment variables ayarlayın:**
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

5. **Veritabanı migration:**
```bash
python manage.py migrate
```

6. **Superuser oluşturun:**
```bash
python manage.py createsuperuser
```

7. **Development server'ı çalıştırın:**
```bash
python manage.py runserver
```

8. **Admin panele erişin:**
```
http://localhost:8000/admin/
```

## 🔧 Production Deployment

### Environment Variables

```env
DJANGO_SECRET_KEY=<güçlü-secret-key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_NAME=uzaktanogrenme
DB_USER=dbuser
DB_PASSWORD=<güçlü-şifre>
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<app-password>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Production Checklist

- [ ] PostgreSQL veritabanı kurulumu
- [ ] Redis sunucusu kurulumu
- [ ] SSL sertifikası alınması
- [ ] Environment variables ayarlanması
- [ ] `python manage.py migrate` çalıştırılması
- [ ] `python manage.py collectstatic` çalıştırılması
- [ ] Gunicorn + Nginx konfigürasyonu
- [ ] Firewall ayarları
- [ ] Backup stratejisi

### Gunicorn + Nginx

**Gunicorn:**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Nginx config örneği:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
}
```

## 🧪 Testing

```bash
# Tüm testleri çalıştır
python manage.py test

# Belirli app'i test et
python manage.py test apps.courses

# Coverage raporu
coverage run --source='.' manage.py test
coverage report
```

## 📊 Apps Yapısı

- `apps.users` - Kullanıcı yönetimi ve authentication
- `apps.students` - Öğrenci profilleri
- `apps.teachers` - Öğretmen profilleri
- `apps.courses` - Ders ve grup yönetimi
- `apps.academic` - Akademik dönem yönetimi
- `apps.enrollment` - Gelişmiş kayıt sistemi
- `apps.gradebook` - Not defteri sistemi
- `apps.forum` - Forum ve mesajlaşma
- `apps.quiz` - Quiz ve sınav sistemi
- `apps.notes` - Legacy not sistemi

## 🔐 Güvenlik

### Implemented Security Features:

1. **Authentication & Authorization**
   - Role-based access control
   - 2FA (Two-Factor Authentication)
   - Session security

2. **Data Protection**
   - HTTPS/SSL enforcement
   - Secure cookies (HttpOnly, Secure flags)
   - CSRF protection
   - XSS prevention

3. **Rate Limiting**
   - Login attempt tracking (5 attempts, 15 min lockout)
   - API rate limiting
   - IP-based throttling

4. **Compliance**
   - KVKK (Turkish Data Protection Law) compliance
   - Consent tracking
   - Data processing agreements

## 📝 API Dokumentasyonu

API dokümantasyonuna erişim:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- Schema: `http://localhost:8000/api/schema/`

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 👥 İletişim

Proje Sahibi - [@username](https://github.com/username)

Proje Linki: [https://github.com/username/OKULPROJE](https://github.com/username/OKULPROJE)

## 🙏 Teşekkürler

- Django Framework
- Bootstrap
- Selçuk Üniversitesi (ilham kaynağı)

---

**⭐ Projeyi beğendiyseniz yıldız vermeyi unutmayın!**
