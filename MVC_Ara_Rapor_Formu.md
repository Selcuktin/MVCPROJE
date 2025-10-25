# MVC Tabanlı Web Mimarisi Dersi
## Proje Ara Rapor Formu

---

## Proje Adı
**Django MVC Kurs Yönetim Sistemi**

---

## Projede Görev Alan Kişi Bilgileri
**Öğrenci Numarası:** [Öğrenci Numarası]  
**Ad Soyad:** [Öğrencinin Adı SOYADI]

---

## Giriş

Django MVC Kurs Yönetim Sistemi, eğitim kurumlarının ders, öğrenci ve öğretmen yönetim süreçlerini dijitalleştirmek amacıyla geliştirilmiş modern bir web uygulamasıdır. Proje, Model-View-Controller (MVC) mimarisine tam uyumlu olarak tasarlanmış olup, Python Django framework'ü kullanılarak hayata geçirilmiştir.

Sistem, üç temel kullanıcı rolünü desteklemektedir: Öğrenci, Öğretmen ve Yönetici. Her rol, kendine özgü yetkilere sahip olup, ders kayıtları, ödev yönetimi, not girişi ve duyuru sistemi gibi temel eğitim süreçlerini kapsamaktadır. Proje, modern web standartlarına uygun, güvenli ve ölçeklenebilir bir yapıya sahiptir.

Uygulamanın temel amacı, geleneksel kağıt tabanlı eğitim yönetim süreçlerini dijital ortama taşıyarak, zaman tasarrufu sağlamak, hata oranını azaltmak ve kullanıcı deneyimini iyileştirmektir.

---

## Katkılar

Proje tek kişi tarafından geliştirilmiş olup, tüm aşamalarda aşağıdaki katkılar sağlanmıştır:

| Katkı Alanı | Detay | Tamamlanma Oranı |
|-------------|-------|------------------|
| **Sistem Analizi ve Tasarım** | Gereksinim analizi, veritabanı tasarımı, sistem mimarisi planlama | %100 |
| **Backend Geliştirme** | Django models, views, controllers, services implementasyonu | %100 |
| **Frontend Geliştirme** | HTML templates, Bootstrap CSS, JavaScript etkileşimleri | %100 |
| **Veritabanı Yönetimi** | SQLite veritabanı tasarımı, migration işlemleri, veri modelleme | %100 |
| **Güvenlik Implementasyonu** | Authentication, authorization, CSRF koruması, form validation | %100 |
| **Test ve Debug** | Unit testler, integration testler, hata ayıklama | %90 |
| **Dokümantasyon** | Kod dokümantasyonu, kullanıcı kılavuzu, teknik dökümanlar | %85 |
| **UI/UX Tasarım** | Kullanıcı arayüzü tasarımı, responsive design, accessibility | %95 |

---

## Kullanılan/Kullanılacak Teknolojiler

### Programlama Dili: Python 3.8+

**Literatürdeki Tanımı:** Python, Guido van Rossum tarafından 1991 yılında geliştirilen, yüksek seviyeli, yorumlamalı, genel amaçlı bir programlama dilidir. Okunabilir sözdizimi ve geniş kütüphane desteği ile bilinir.

**Özellikleri:**
- Basit ve okunabilir sözdizimi
- Platform bağımsızlığı
- Geniş standart kütüphane
- Güçlü topluluk desteği
- Nesne yönelimli programlama desteği

**Neden Tercih Edildi:**
- Django framework'ü ile mükemmel entegrasyon
- Hızlı geliştirme imkanı
- Zengin kütüphane ekosistemi
- Web geliştirme için optimize edilmiş yapı
- Öğrenme kolaylığı ve kod okunabilirliği

### Web Framework: Django 4.2.7

**Literatürdeki Tanımı:** Django, Python ile yazılmış, ücretsiz ve açık kaynaklı bir web framework'üdür. "Batteries included" felsefesi ile geliştirilmiş olup, web uygulaması geliştirmek için gerekli tüm bileşenleri içerir.

**Özellikleri:**
- MVC (Model-View-Controller) mimarisi
- ORM (Object-Relational Mapping) desteği
- Yerleşik admin paneli
- Güvenlik odaklı tasarım
- Ölçeklenebilir mimari
- URL routing sistemi

**Neden Tercih Edildi:**
- MVC mimarisine tam uyumluluk
- Güçlü güvenlik özellikleri (CSRF, XSS koruması)
- Hızlı prototipleme imkanı
- Zengin dokümantasyon
- Büyük topluluk desteği
- Enterprise düzeyinde projeler için uygunluk

### Frontend Framework: Bootstrap 5.3

**Literatürdeki Tanımı:** Bootstrap, Twitter tarafından geliştirilen, responsive ve mobile-first web siteleri oluşturmak için kullanılan açık kaynaklı CSS framework'üdür.

**Özellikleri:**
- Responsive grid sistemi
- Hazır UI bileşenleri
- Cross-browser uyumluluğu
- Customizable tema sistemi
- JavaScript plugin'leri

**Neden Tercih Edildi:**
- Hızlı UI geliştirme imkanı
- Mobile-first yaklaşım
- Django ile kolay entegrasyon
- Profesyonel görünüm
- Geniş browser desteği

### Veritabanı: SQLite3

**Literatürdeki Tanımı:** SQLite, dosya tabanlı, serverless, self-contained bir SQL veritabanı motorudur. Küçük ve orta ölçekli uygulamalar için ideal bir çözümdür.

**Özellikleri:**
- Kurulum gerektirmez
- Dosya tabanlı depolama
- ACID uyumluluğu
- Cross-platform desteği
- Hafif ve hızlı

**Neden Tercih Edildi:**
- Geliştirme aşaması için ideal
- Kolay kurulum ve yönetim
- Django ile native entegrasyon
- Production'a geçişte PostgreSQL'e kolay migration
- Prototipleme için mükemmel

### İkon Kütüphanesi: Font Awesome 6

**Literatürdeki Tanımı:** Font Awesome, web projelerinde kullanılmak üzere tasarlanmış scalable vector icon kütüphanesidir.

**Özellikleri:**
- 2000+ ücretsiz ikon
- Scalable vector format
- CSS ve JavaScript entegrasyonu
- Customizable renkler ve boyutlar

**Neden Tercih Edildi:**
- Zengin ikon koleksiyonu
- Bootstrap ile uyumlu
- Kolay implementasyon
- Profesyonel görünüm

---

## Uygulama Çalışma Prensibi

### MVC Mimarisi İş Akışı

```
[USER REQUEST] 
       ↓
[URL DISPATCHER] (urls.py)
       ↓
[VIEW LAYER] (views.py)
       ↓
[CONTROLLER LAYER] (controllers.py)
       ↓
[SERVICE LAYER] (services.py)
       ↓
[MODEL LAYER] (models.py)
       ↓
[DATABASE] (SQLite3)
       ↓
[RESPONSE FLOW] (Reverse Direction)
       ↓
[TEMPLATE RENDERING] (HTML + Bootstrap)
       ↓
[USER RESPONSE]
```

### Detaylı Süreç Açıklaması

#### 1. İstek Alma Aşaması (Request Handling)
- Kullanıcı tarayıcıdan bir URL'e istek gönderir
- Django'nun URL dispatcher'ı (urls.py) gelen isteği analiz eder
- Uygun view fonksiyonuna yönlendirme yapar

#### 2. View Katmanı İşleme (View Layer Processing)
- View fonksiyonu HTTP isteğini alır
- Gerekli parametreleri çıkarır
- Controller katmanını çağırır
- Template rendering işlemini başlatır

#### 3. Controller Katmanı Koordinasyonu (Controller Coordination)
- İş mantığı koordinasyonunu yapar
- Service katmanından gerekli verileri talep eder
- Form validasyonu ve yetkilendirme kontrolü
- Context data hazırlama

#### 4. Service Katmanı İş Mantığı (Business Logic)
- Karmaşık iş kurallarını uygular
- Veri hesaplamaları ve dönüşümleri
- Model katmanı ile etkileşim
- Cache yönetimi

#### 5. Model Katmanı Veri İşleme (Data Layer)
- ORM aracılığıyla veritabanı sorguları
- Veri doğrulama (validation)
- İlişkisel veri yönetimi
- CRUD operasyonları

#### 6. Veritabanı İşlemleri (Database Operations)
- SQLite3 veritabanında veri okuma/yazma
- Transaction yönetimi
- Index kullanımı ve optimizasyon

#### 7. Yanıt Oluşturma (Response Generation)
- Model verilerinin template'e aktarılması
- HTML rendering (Django template engine)
- Bootstrap CSS ile styling
- JavaScript etkileşimleri

#### 8. Kullanıcıya Yanıt (User Response)
- Render edilmiş HTML sayfasının kullanıcıya gönderilmesi
- Static dosyaların (CSS, JS, images) yüklenmesi
- AJAX istekleri için JSON response

### Güvenlik Katmanları

#### Authentication (Kimlik Doğrulama)
- Django'nun yerleşik auth sistemi
- Session tabanlı kullanıcı yönetimi
- Password hashing (PBKDF2)

#### Authorization (Yetkilendirme)
- Rol tabanlı erişim kontrolü
- Permission decorators
- Template-level yetki filtreleme

#### Data Protection (Veri Koruması)
- CSRF token koruması
- XSS koruması
- SQL injection koruması
- Form validation

### Performans Optimizasyonları

#### Database Optimizations
- Query optimization
- Select_related ve prefetch_related kullanımı
- Database indexing

#### Frontend Optimizations
- Static file compression
- CSS/JS minification
- Image optimization
- Lazy loading

---

## Kaynaklar

1. **Django Software Foundation.** (2023). *Django Documentation*. https://docs.djangoproject.com/

2. **Holovaty, A., & Kaplan-Moss, J.** (2009). *The Definitive Guide to Django: Web Development Done Right*. Apress.

3. **Greenfeld, D. R., & Roy, A.** (2021). *Two Scoops of Django 3.x: Best Practices for the Django Web Framework*. Two Scoops Press.

4. **Percival, H., & Gregory, B.** (2020). *Architecture Patterns with Python: Enabling Test-Driven Development, Domain-Driven Design, and Event-Driven Microservices*. O'Reilly Media.

5. **Bootstrap Team.** (2023). *Bootstrap 5 Documentation*. https://getbootstrap.com/docs/5.3/

6. **Mozilla Developer Network.** (2023). *Web Development Guide*. https://developer.mozilla.org/

7. **Forcier, J., Bissex, P., & Chun, W. J.** (2008). *Python Web Development with Django*. Addison-Wesley Professional.

8. **Shaw, Z. A.** (2017). *Learn Python 3 the Hard Way: A Very Simple Introduction to the Terrifyingly Beautiful World of Computers and Code*. Addison-Wesley Professional.

9. **Gamma, E., Helm, R., Johnson, R., & Vlissides, J.** (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.

10. **Martin, R. C.** (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.

---

**Rapor Tarihi:** [Tarih]  
**Öğrenci:** [Öğrencinin Adı SOYADI]  
**Öğrenci Numarası:** [Numara]  
**Ders:** MVC Tabanlı Web Mimarisi  
**Öğretim Üyesi:** [Hoca Adı]