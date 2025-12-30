# 🔐 Şifre Sıfırlama Sistemi

## 📋 Genel Bakış

E-posta ile şifre sıfırlama sistemi Django'nun built-in şifre sıfırlama özelliğini kullanır.

---

## 🎯 Özellikler

✅ **E-posta ile Sıfırlama** - Kullanıcıya güvenli bağlantı gönderilir
✅ **Token Tabanlı** - Güvenli, tek kullanımlık tokenlar
✅ **24 Saat Geçerlilik** - Bağlantılar 24 saat sonra geçersiz olur
✅ **Modern Arayüz** - Responsive ve kullanıcı dostu tasarım
✅ **Güvenli** - Django'nun güvenlik standartları

---

## 🔄 Şifre Sıfırlama Akışı

```
1. Kullanıcı "Şifremi Unuttum" linkine tıklar
   ↓
2. E-posta adresini girer
   ↓
3. Sistem e-posta gönderir (token içeren bağlantı)
   ↓
4. Kullanıcı e-postadaki bağlantıya tıklar
   ↓
5. Yeni şifre belirleme sayfası açılır
   ↓
6. Yeni şifreyi girer ve kaydeder
   ↓
7. Şifre değiştirilir, giriş yapabilir
```

---

## 📁 Dosya Yapısı

### URL Yapılandırması
**Dosya:** `apps/users/urls.py`

```python
# Şifre Sıfırlama URL'leri
path('password-reset/', ...)                    # 1. Adım: E-posta girişi
path('password-reset/done/', ...)               # 2. Adım: E-posta gönderildi
path('password-reset-confirm/<uidb64>/<token>/', ...)  # 3. Adım: Yeni şifre
path('password-reset-complete/', ...)           # 4. Adım: Tamamlandı
```

### Template'ler
**Lokasyon:** `templates/users/`

1. **password_reset.html** - E-posta girişi
2. **password_reset_done.html** - E-posta gönderildi mesajı
3. **password_reset_confirm.html** - Yeni şifre belirleme
4. **password_reset_complete.html** - Başarılı mesajı
5. **password_reset_email.html** - E-posta içeriği
6. **password_reset_subject.txt** - E-posta konusu

---

## ⚙️ Yapılandırma

### E-posta Ayarları
**Dosya:** `config/settings.py`

#### Development (Geliştirme)
```python
# Console'a yazdırır (gerçek e-posta göndermez)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Kullanım:** 
- Geliştirme sırasında kullanılır
- E-posta Django console'da görünür
- Gerçek e-posta gönderilmez

#### Production (Canlı Ortam)
```python
# Gmail SMTP Örneği
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'Uzaktan Eğitim Sistemi <your-email@gmail.com>'
```

**Gmail App Password Oluşturma:**
1. Google Hesabı → Güvenlik
2. 2 Adımlı Doğrulama'yı aktif et
3. Uygulama Şifreleri → Yeni şifre oluştur
4. Oluşan 16 haneli şifreyi `EMAIL_HOST_PASSWORD` olarak kullan

---

## 🎨 Arayüz Özellikleri

### 1. Şifre Sıfırlama Sayfası
- Modern gradient tasarım
- Responsive (mobil uyumlu)
- Form validasyonu
- Geri dönüş linki

### 2. E-posta Gönderildi Sayfası
- Başarı animasyonu
- Bilgilendirici mesaj
- Spam klasörü uyarısı

### 3. Yeni Şifre Belirleme
- Şifre gereksinimleri gösterimi
- Şifre tekrar kontrolü
- Geçersiz token kontrolü

### 4. Tamamlandı Sayfası
- Başarı mesajı
- Giriş sayfasına yönlendirme

---

## 🔒 Güvenlik

### Token Sistemi
- **Tek Kullanımlık:** Her token sadece 1 kez kullanılabilir
- **Zamanlı:** 24 saat sonra otomatik geçersiz olur
- **Şifreli:** Django'nun güvenli token sistemi

### Şifre Gereksinimleri
- En az 8 karakter
- Sadece rakamlardan oluşmamalı
- Çok yaygın şifreler kabul edilmez
- Kullanıcı adına benzememelidir

---

## 📧 E-posta İçeriği

### Konu
```
Şifre Sıfırlama - Uzaktan Eğitim Sistemi
```

### İçerik
```
Merhaba,

Uzaktan Eğitim Sistemi hesabınız için şifre sıfırlama talebinde bulundunuz.

Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:

[Şifre Sıfırlama Bağlantısı]

Bu bağlantı 24 saat geçerlidir.

Eğer bu talebi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.

Saygılarımızla,
Uzaktan Eğitim Sistemi
```

---

## 🧪 Test Etme

### Development Ortamında
1. Login sayfasına git: `http://localhost:8000/users/login/`
2. "Şifremi Unuttum" linkine tıkla
3. E-posta adresini gir (sistemde kayıtlı olmalı)
4. Django console'u kontrol et (e-posta içeriği orada görünür)
5. Console'daki bağlantıyı kopyala ve tarayıcıya yapıştır
6. Yeni şifre belirle

### Production Ortamında
1. SMTP ayarlarını yapılandır
2. Gerçek e-posta adresi kullan
3. E-posta gelen kutusunu kontrol et
4. Bağlantıya tıkla ve şifreyi değiştir

---

## 🐛 Sorun Giderme

### E-posta Gelmiyor
**Sorun:** E-posta gönderilmiyor
**Çözüm:**
- SMTP ayarlarını kontrol et
- Gmail için App Password kullan
- Firewall/Antivirus kontrolü
- Spam klasörünü kontrol et

### Token Geçersiz
**Sorun:** "Geçersiz bağlantı" hatası
**Çözüm:**
- Bağlantı 24 saat içinde kullanılmalı
- Her token sadece 1 kez kullanılabilir
- Yeni sıfırlama talebi oluştur

### Console'da E-posta Görünmüyor
**Sorun:** Development'ta e-posta console'da görünmüyor
**Çözüm:**
- `EMAIL_BACKEND` ayarını kontrol et
- Django sunucusunu yeniden başlat
- Console çıktısını kontrol et

---

## 📊 Kullanım İstatistikleri

| Özellik | Durum |
|---------|-------|
| E-posta Gönderimi | ✅ Aktif |
| Token Güvenliği | ✅ Aktif |
| 24 Saat Geçerlilik | ✅ Aktif |
| Responsive Tasarım | ✅ Aktif |
| Form Validasyonu | ✅ Aktif |

---

## 🔄 Güncelleme Geçmişi

**Versiyon 1.0** - 20 Aralık 2025
- ✅ İlk versiyon oluşturuldu
- ✅ Modern arayüz tasarlandı
- ✅ E-posta template'leri eklendi
- ✅ Login sayfasına link eklendi
- ✅ Dokümantasyon hazırlandı

---

## 📝 Notlar

- Development ortamında `console` backend kullanılır
- Production'da SMTP yapılandırması gereklidir
- Gmail kullanıyorsanız App Password oluşturun
- Token'lar veritabanında saklanmaz (güvenlik)
- Her sıfırlama talebi yeni token oluşturur

---

**Son Güncelleme:** 20 Aralık 2025
**Versiyon:** 1.0
