# 📖 KULLANIM KILAVUZU

Uzaktan Eğitim Sistemi - Hızlı Başlangıç Rehberi

---

## 🚀 HIZLI BAŞLATMA

### 1. Server'ı Başlat

**Yöntem 1 (Kolay):**
`START_HERE.bat` dosyasına **çift tıklayın**

**Yöntem 2 (Manuel):**
```bash
cd C:\Users\mtn2\Downloads\OKULPROJE
python manage.py runserver
```

### 2. Tarayıcıda Aç

- **Ana Sayfa:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin
- **API Docs:** http://localhost:8000/api/docs

---

## 👨‍💼 YÖNETİCİ (ADMIN) İŞLEMLERİ

### İlk Kurulum

1. **Admin kullanıcısı oluştur:**
```bash
python manage.py createsuperuser
```

2. **Admin panele giriş:**
http://localhost:8000/admin

### Sistem Kurulumu (Sırayla)

#### Adım 1: Akademik Dönem Oluştur
1. Admin → Academic Terms → Add
2. **Name:** 2024-2025 Güz (otomatik)
3. **Year Start:** 2024
4. **Year End:** 2025
5. **Term Type:** Fall (Güz)
6. **Start Date:** 16.09.2024
7. **End Date:** 31.01.2025
8. **Registration Start:** 01.09.2024
9. **Registration End:** 20.09.2024
10. **Is Active:** ✅ (işaretle)
11. Save

#### Adım 2: Ders Oluştur (Course)
1. Admin → Courses → Add
2. **Code:** CS101
3. **Name:** Programlama I
4. **Credits:** 3
5. **Capacity:** 30
6. **Description:** Python programlama dersi
7. Save

#### Adım 3: Öğretmen Oluştur
1. Admin → Users → Add
2. Username & password oluştur
3. Save
4. Admin → User Profiles → Add
5. User seç, **User Type:** Teacher
6. Save
7. Admin → Teachers → Add
8. User'ı seç, bilgileri doldur
9. Save

#### Adım 4: Öğrenci Oluştur
1. Admin → Users → Add (kullanıcı oluştur)
2. Admin → User Profiles → Add (user type: student)
3. Admin → Students → Add (detayları doldur)

#### Adım 5: Ders Grubu Oluştur
1. Admin → Course Groups → Add
2. **Course:** CS101 seç
3. **Teacher:** Öğretmen seç
4. **Name:** A (otomatik artar)
5. **Academic Term:** 2024-2025 Güz seç
6. **Classroom:** B201
7. **Schedule:** Pzt 09:00-12:00
8. **Status:** Active
9. Save

#### Adım 6: Kayıt Yöntemi Tanımla
1. Admin → Enrollment Methods → Add
2. **Course Group:** Seç
3. **Method Type:** Self (öğrenci kendisi kayıt olur)
4. **Is Enabled:** ✅
5. **Max Students:** 30
6. **Enrollment Start:** 01.09.2024
7. **Enrollment End:** 20.09.2024
8. Save

#### Adım 7: Soru Bankası & Quiz Oluştur
1. Admin → Question Banks → Add
2. Bank oluştur
3. Admin → Questions → Add
4. Sorular ekle (çoktan seçmeli, doğru/yanlış, vb.)
5. Admin → Quizzes → Add
6. Quiz oluştur, soruları ekle

---

## 👨‍🎓 ÖĞRENCİ İŞLEMLERİ

### Giriş Yap
1. http://localhost:8000/login
2. Username & password gir
3. Dashboard'a yönlendirileceksin

### Ders Seçimi
1. Dashboard → **"Ders Seç"** butonu
2. veya http://localhost:8000/enrollment/available/
3. Mevcut dersleri gör
4. **"Kayıt Ol"** butonu
5. Gerekirse enrollment key gir
6. Onay mesajı

### Quiz Girme
1. Dashboard → **"Quizler"** butonu
2. veya http://localhost:8000/quiz/available/
3. Aktif quiz'i bul
4. **"Quiz'i Başlat"**
5. Timer başlar ⏱️
6. Soruları cevapla
7. **"Teslim Et"** veya süre bitince otomatik teslim
8. Sonuçları görüntüle

### Notları Görüntüle
1. Dashboard → **"Notlarım"**
2. veya http://localhost:8000/gradebook/my-grades/
3. Kategori bazlı notları gör
4. **"Transkript"** → Tüm dönemlerin notları

### Mesaj Gönder
1. Dashboard → **"Mesajlar"**
2. **"Yeni Mesaj"**
3. Alıcı seç (öğretmenler listesi)
4. Konu & mesaj yaz
5. Gönder

---

## 👨‍🏫 ÖĞRETMEN İŞLEMLERİ

### Soru Bankası Yönetimi
1. Dashboard → **"Soru Bankası"**
2. veya http://localhost:8000/quiz/question-banks/
3. **"Yeni Banka Oluştur"**
4. Bankayı seç → **"Soru Ekle"**
5. Soru tipini seç:
   - Çoktan seçmeli (A-E arası şıklar)
   - Doğru/Yanlış
   - Kısa cevap
   - Essay
   - Eşleştirme
   - Boşluk doldurma
6. Doğru cevabı belirt
7. Açıklama ekle (opsiyonel)
8. Save

### Quiz Oluşturma
1. **"Derslerim"** → Ders seç
2. **"Quiz Oluştur"** butonu
3. Bilgileri doldur:
   - Başlık
   - Başlangıç/Bitiş zamanı
   - Süre (dakika) → Timer için
   - Max deneme sayısı
   - Geçme notu (%)
   - **Auto Submit:** ✅ (süre bitince otomatik teslim)
4. **"Soru Ekle"** → Soru bankasından seç
5. Her soru için puan belirle
6. Save → Quiz aktif!

### Not Girişi
1. **"Derslerim"** → Ders seç
2. **"Not Defteri"** butonu
3. veya http://localhost:8000/gradebook/course/<group_id>/
4. Önce kategorileri oluştur:
   - Admin → Grade Categories → Add
   - Örn: "Vize" (40%), "Final" (60%)
5. Not kalemlerini oluştur:
   - Admin → Grade Items → Add
   - Kategori seç, ağırlık belirle
6. Notları gir:
   - Not defterinde öğrenci notlarını gör
   - Otomatik harf notu hesaplanır (AA-FF)

### Öğrenci Mesajlarını Oku
1. Dashboard → **"Mesajlar"**
2. Gelen kutusu → Mesajları oku
3. **"Cevapla"** veya **"Yeni Mesaj"**

---

## 🎯 ÖZEL ÖZELLİKLER

### Quiz Timer (Gerçek Zamanlı Sayaç)
- Quiz başladığında timer başlar
- Kalan süre gösterilir (HH:MM:SS)
- 10 dk kala → Sarı
- 5 dk kala → Kırmızı
- Süre bitince → Otomatik teslim

### Ağırlıklı Not Sistemi
```
Örnek:
- Vize: 40% ağırlık
  - Quiz 1: 50% (vize içinde)
  - Quiz 2: 50% (vize içinde)
- Final: 60% ağırlık

Hesaplama:
Vize = (Quiz1 * 0.5 + Quiz2 * 0.5) * 0.4
Final = FinalScore * 0.6
Toplam = Vize + Final → Harf notu
```

### Enrollment Rules
- **Prerequisite:** Önkoşul dersler (min grade)
- **Department:** Bölüm kısıtı
- **Year:** Yarıyıl kısıtı
- **Capacity:** Otomatik kontrol

### Activity Tracking
- Öğrenci aktiviteleri takip edilir
- Progress % hesaplanır
- Prerequisite unlock sistemi

---

## 📊 ÖĞRENCİ DASHBOARD

**Gösterilen Bilgiler:**
- Kayıtlı ders sayısı
- Genel ortalama (GPA)
- Bekleyen ödev sayısı
- Aktif quiz sayısı
- Yaklaşan quizler (7 gün)
- Son bildirimler
- Okunmamış mesaj sayısı

**Quick Actions:**
- Ders Seç
- Quizler
- Notlarım
- Mesajlar
- Derslerim

---

## 📊 ÖĞRETMEN DASHBOARD

**Gösterilen Bilgiler:**
- Verdiğim ders sayısı
- Toplam öğrenci sayısı
- Notlandırılacak ödev sayısı
- Aktif quiz sayısı
- Ders listesi (öğrenci sayıları ile)
- Bekleyen görevler

**Quick Actions:**
- Yeni Ders Oluştur
- Soru Bankası
- Mesajlar
- Tüm Derslerim

---

## 🔐 GÜVENLİK ÖZELLİKLERİ

1. **Login Rate Limiting:**
   - 5 başarısız deneme → 15 dk kilit
   - IP bazlı takip

2. **Content Access:**
   - Sadece kayıtlı öğrenciler ders içeriğine erişebilir
   - Öğretmen sadece kendi derslerini görebilir

3. **CSRF Protection:**
   - Tüm formlar korumalı
   - AJAX istekleri token ile

4. **2FA (Opsiyonel):**
   - Email bazlı doğrulama
   - 6 haneli kod
   - Backup codes

---

## 💾 YEDEKLEME

### Basit Yedek (SQLite)
```bash
copy db.sqlite3 backups\backup_$(date).sqlite3
```

### Tam Yedek
```bash
xcopy /E /I . ..\OKULPROJE_BACKUP
```

---

## 🌐 AĞ ÜZERİNDEN ERİŞİM

### Aynı WiFi'deki Cihazlar

1. **IP bul:**
```bash
ipconfig
# IPv4: 192.168.1.100
```

2. **Server başlat:**
```bash
python manage.py runserver 0.0.0.0:8000
```

3. **ALLOWED_HOSTS güncelle:**
`config/settings.py`:
```python
ALLOWED_HOSTS = ['*']  # Geliştirme için
```

4. **Diğer cihazlardan:**
```
http://192.168.1.100:8000
```

---

## 🛠️ SORUN GİDERME

### Server başlamıyor
```bash
# Port kontrolü
netstat -ano | findstr :8000

# Farklı port kullan
python manage.py runserver 8080
```

### Static files görünmüyor
```python
# settings.py kontrol et
DEBUG = True  # Development'ta True olmalı
```

### Database locked
```bash
# Server'ı durdur (CTRL+C)
# Tekrar başlat
```

---

## 📞 YARD IM

**Sık Karşılaşılan Durumlar:**

1. **"Öğrenci/Öğretmen profili bulunamadı"**
   - Admin panelden UserProfile oluşturulmalı
   - Student/Teacher objesi oluşturulmalı

2. **"Bu derse kayıt olamazsınız"**
   - EnrollmentMethod tanımlı mı kontrol et
   - Tarih aralığı aktif mi?
   - Kapasite doldu mu?

3. **"Quiz görünmüyor"**
   - Quiz is_active = True mi?
   - Start/End time doğru mu?
   - Öğrenci derse kayıtlı mı?

4. **"Notlar hesaplanmıyor"**
   - GradeCategory oluşturuldu mu?
   - GradeItem'lar tanımlı mı?
   - Ağırlıklar toplamı 100%?

---

## 🎯 ÖRNEKendiriSENARYO

### Senaryo: Quiz Oluştur ve Uygula

**Öğretmen:**
1. Login yap
2. Soru Bankası → Yeni banka oluştur
3. Banka'ya 10 soru ekle (çoktan seçmeli)
4. Derslerim → CS101 seç
5. "Quiz Oluştur"
   - Başlık: "Vize Sınavı"
   - Süre: 60 dakika
   - Max deneme: 1
   - Geçme notu: 60%
   - Auto submit: ✅
6. Soru bankasından 20 soru seç
7. Her soru 5 puan
8. Save & Publish

**Öğrenci:**
1. Login yap
2. Dashboard → "Quizler"
3. "Vize Sınavı" → "Quiz'i Başlat"
4. Timer 60:00'dan başlar
5. Soruları cevapla
6. "Teslim Et" veya süre bitince otomatik
7. Sonucu gör (otomatik hesaplanır)

**Öğretmen:**
1. Quiz Detay → Attempts
2. Öğrenci cevaplarını gör
3. Essay soruları manuel notlandır
4. İstatistikleri incele

---

## 📊 NOT SİSTEMİ KULLANIMI

### Senaryo: Not Defteri Kurulumu

**Adım 1: Kategorileri Oluştur**

Admin → Grade Categories → Add

Örnek yapı:
```
CS101 - Grup A:
├── Vize (40%)
│   ├── Quiz 1 (50%)
│   └── Quiz 2 (50%)
├── Final (60%)
└── Bonus (+10% ekstra)
```

**Adım 2: Not Kalemlerini Oluştur**

Admin → Grade Items → Add
- Category: Vize
- Name: Quiz 1
- Max Score: 100
- Weight in Category: 50%

**Adım 3: Notları Gir**

Admin → Grades → Add
veya
Gradebook sayfasından toplu giriş

**Sonuç:**
- Otomatik hesaplama
- Harf notu: AA-FF
- GPA güncellenir

---

## 🎊 SİSTEM HAZIR!

**Tüm özellikler aktif ve kullanıma hazır:**

✅ Dönem yönetimi  
✅ Ders seçimi (4 yöntem)  
✅ Timer'lı sınavlar  
✅ Soru bankası  
✅ Not defteri  
✅ Mesajlaşma  
✅ Bildirimler  
✅ Raporlama  

**Kullanmaya başlayabilirsiniz! 🚀**

---

*Detaylı bilgi için:*
- `README.md` - Genel bakış
- `LOCAL_SETUP_GUIDE.md` - Yerel kurulum
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `SISTEM_HATALARI_RAPORU.md` - Teknik detaylar
