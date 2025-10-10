# 🔧 JWT Authentication Kurulumu

## ⚠️ Şu Anda JWT Devre Dışı

JWT authentication hazır ama **paket yüklenmesi gerekiyor**.

---

## 📦 Kurulum Adımları

### 1. **Paketi Yükle**

```bash
# Doğru Python ortamını kullandığınızdan emin olun
python -m pip install djangorestframework-simplejwt==5.3.0
```

### 2. **Settings.py'yi Güncelle**

`config/settings.py` dosyasında şu satırları aktif et:

```python
INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt.token_blacklist',  # Yorumu kaldır
    # ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # Yorumu kaldır
    ],
    # ...
}
```

### 3. **URLs.py'yi Güncelle**

`apps/users/urls.py` dosyasında JWT endpoint yorumlarını kaldır:

```python
from rest_framework_simplejwt.views import TokenRefreshView
from . import api_views

urlpatterns = [
    # ... web routes
    
    # JWT API Endpoints
    path('api/token/', api_views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/register/', api_views.register_api, name='api_register'),
    path('api/logout/', api_views.logout_api, name='api_logout'),
    path('api/profile/', api_views.user_profile_api, name='api_profile'),
]
```

### 4. **Migration Yap**

```bash
python manage.py migrate
```

### 5. **Sunucuyu Başlat**

```bash
python manage.py runserver
```

---

## 🧪 Test Etme

### 1. Token Al (Login)

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com"
  }
}
```

### 2. API'ye Erişim

```bash
curl http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Token Yenile

```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"YOUR_REFRESH_TOKEN\"}"
```

---

## 🔍 Sorun Giderme

### Problem: ModuleNotFoundError

**Çözüm:**
```bash
# Hangi Python kullanıldığını kontrol et
python --version
where python

# Doğru ortama paketi yükle
python -m pip install djangorestframework-simplejwt==5.3.0

# Veya pip'i doğrudan kullan
pip install djangorestframework-simplejwt==5.3.0
```

### Problem: Virtual Environment Kullanıyorsanız

```bash
# Virtual environment aktif mi kontrol et
# Aktif değilse:
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Sonra paketi yükle
pip install djangorestframework-simplejwt==5.3.0
```

---

## 📋 JWT Özellikleri

✅ **Access Token:** 1 saat geçerli  
✅ **Refresh Token:** 7 gün geçerli  
✅ **Token Rotation:** Güvenlik için otomatik yenileme  
✅ **Blacklist:** Çıkış yapınca token geçersiz olur  
✅ **Custom Claims:** Token içinde kullanıcı bilgileri  

---

## 🎯 Şu Anda Neler Çalışıyor?

✅ **Session-based authentication** (Web)  
✅ **Activity Logging**  
✅ **PDF Export**  
✅ **CRUD İşlemleri**  

**JWT hazır ama devre dışı** - Paketi yükleyince aktif hale gelecek.

---

## 💡 Alternatif: JWT Olmadan Devam

Eğer JWT'ye ihtiyacınız yoksa (sadece web uygulaması):
- **Hiçbir şey yapmanıza gerek yok!**
- Session-based authentication yeterlidir
- Proje şu haliyle tam çalışıyor

---

**Güncelleme:** 11 Ekim 2025  
**Durum:** JWT dosyaları hazır, kurulum bekleniyor

