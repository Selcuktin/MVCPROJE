
T.C.
SELÇUK ÜNİVERSİTESİ
TEKNOLOJİ FAKÜLTESİ
BİLGİSAYAR MÜHENDİSLİĞİ

Django Kurs Yönetim Sistemi

Metin SELÇUKARSLAN

MÜHENDİSLİK TASARIMI / BİLGİSAYAR MÜHENDİSLİĞİ UYGULAMALARI

EKİM-2025
KONYA
Her Hakkı Saklıdır

---
**PROJE KABUL VE ONAYI**

Metin Selçukarslan tarafından hazırlanan “Django Kurs Yönetim Sistemi” adlı proje çalışması 26/10/2025 tarihinde aşağıdaki jüri üyeleri tarafından oy birliği/oy çokluğu ile Selçuk Üniversitesi Teknoloji Fakültesi Bilgisayar Mühendisliği bölümünde Mühendislik Tasarımı / Bilgisayar Mühendisliği Uygulamaları Projesi olarak kabul edilmiştir.

**Jüri Üyeleri**
Danışman: Prof. Dr. HUMAR KAHRAMANLI ÖRNEK
Üye: Dr. Öğr. Üyesi Onur İNAN
Üye: Dr. Öğr. Üyesi Selahattin ALAN

Yukarıdaki sonucu onaylarım.

Bilgisayar Mühendisliği Bölüm Başkanı
Prof. Dr. NURETTİN DOĞAN

---
**PROJE BİLDİRİMİ**

Bu projedeki bütün bilgilerin etik davranış ve akademik kurallar çerçevesinde elde edildiğini ve proje yazım kurallarına uygun olarak hazırlanan bu çalışmada bana ait olmayan her türlü ifade ve bilginin kaynağına eksiksiz atıf yapıldığını bildiririm.

**DECLARATION PAGE**

I hereby declare that all information in this document has been obtained and presented in accordance with academic rules and ethical conduct. I also declare that, as required by project rules and conduct, I have fully cited and referenced all material and results that are not original to this work.

İmza: ____________________
Metin Selçukarslan
Tarih: 26/10/2025

---
**ÖZET**

MÜHENDİSLİK TASARIMI / BİLGİSAYAR MÜHENDİSLİĞİ UYGULAMALARI PROJESİ

Django MVC Kurs Yönetim Sistemi

Metin SELÇUKARSLAN

SELÇUK ÜNİVERSİTESİ
TEKNOLOJİ FAKÜLTESİ
BİLGİSAYAR MÜHENDİSLİĞİ BÖLÜMÜ

Danışman: Prof. Dr. HUMAR KAHRAMANLI ÖRNEK

2025, 25 Sayfa
Jüri
Prof. Dr. HUMAR KAHRAMANLI ÖRNEK
Dr. Öğr. Üyesi Onur İNAN
Dr. Öğr. Üyesi Selahattin ALAN

Bu proje, modern web teknolojileri kullanılarak geliştirilmiş kapsamlı bir kurs yönetim sistemidir. Sistem, eğitim kurumlarında öğrenci-öğretmen etkileşimini kolaylaştıran, ders yönetimi, ödev sistemi, sınav (quiz) sistemi, not defteri, mesajlaşma, akademik dönem yönetimi ve duyuru sistemi gibi temel eğitim süreçlerini dijitalleştiren bir platform sunmaktadır.

Proje, Django 4.2.x web framework'ü kullanılarak MTV (Model-Template-View) mimarisine uygun olarak geliştirilmiştir. Sistem toplam 11 ana modülden oluşmaktadır: kullanıcı yönetimi, öğrenci, öğretmen, dersler, notlar, quiz, gradebook, forum, akademik dönem, kayıt sistemi ve yardımcı araçlar. Frontend tarafında Bootstrap 5.3, HTML5, CSS3 ve JavaScript teknolojileri kullanılmıştır. Veritabanı olarak geliştirme ortamında SQLite3, prodüksiyon ortamı uyumluluğu için PostgreSQL altyapısı tercih edilmiştir. Sistem, rol tabanlı yetkilendirme (RBAC) ile öğrenci, öğretmen ve admin kullanıcıları için özelleştirilmiş dashboardlar sunmaktadır.

Sistem testleri sonucunda, sınav oluşturma, otomatik notlandırma, transkript oluşturma ve anlık mesajlaşma gibi tüm temel fonksiyonların başarıyla çalıştığı görülmüştür. Ayrıca REST API desteği ile mobil uygulama entegrasyonuna hazır bir altyapı sağlanmıştır.

**Anahtar Kelimeler:** Django, eğitim yönetimi, MVC/MTV mimarisi, Python, web uygulaması, sınav sistemi, LMS, veritabanı yönetimi, REST API

---
**ABSTRACT**

ENGINEERING DESIGN APPLICATIONS PROJECT

Django MVC Course Management System

Metin SELÇUKARSLAN

SELCUK UNIVERSITY
FACULTY OF TECHNOLOGY
DEPARTMENT OF COMPUTER ENGINEERING

2025, 25 Pages
Jury
Prof. Dr. HUMAR KAHRAMANLI ÖRNEK
Dr. Öğr. Üyesi Onur İNAN
Dr. Öğr. Üyesi Selahattin ALAN

This project is a comprehensive course management system developed using modern web technologies. The system provides a platform that facilitates student-teacher interaction in educational institutions by digitalizing fundamental educational processes such as course management, assignment system, quiz system, gradebook, messaging, academic term management, and announcement system.

The project has been developed using Django 4.2.x web framework in accordance with MTV (Model-Template-View) architecture. The system consists of 11 main modules: user management, students, teachers, courses, notes, quiz, gradebook, forum, academic term, enrollment, and utilities. Bootstrap 5.3, HTML5, CSS3, and JavaScript technologies have been used on the frontend. SQLite3 was used for development, with PostgreSQL compatibility for production. The system offers customized dashboards for student, teacher, and admin users through role-based authorization (RBAC).

System tests have shown that all basic functions, such as quiz creation, automatic grading, transcript generation, and instant messaging, work successfully. Additionally, a REST API infrastructure is provided for future mobile application integration.

**Keywords:** Django, education management, MVC/MTV architecture, Python, web application, quiz system, LMS, database management, REST API

---
**ÖNSÖZ**

Bu proje, modern web teknolojileri kullanılarak geliştirilmiş kapsamlı bir kurs yönetim sisteminin tasarım ve implementasyonunu içermektedir. Proje sürecinde Django web framework'ünün güçlü özelliklerinden yararlanarak, eğitim kurumları için pratik, kullanışlı ve ölçeklenebilir bir sistem geliştirilmiştir. Proje geliştirme sürecinde MVC (Model-View-Controller) ve MTV mimarisinin avantajları göz önünde bulundurularak, modüler ve sürdürülebilir bir kod yapısı oluşturulmuştur. Özellikle sınav sistemi, not defteri ve mesajlaşma modülleri ile sistem zenginleştirilmiştir.

Bu çalışmanın gerçekleştirilmesinde değerli katkıları olan danışman hocama ve proje sürecinde desteklerini esirgemeyen arkadaşlarıma teşekkür ederim.

Metin SELÇUKARSLAN
Konya / 2025

---
**İÇİNDEKİLER**

ÖZET iv
ABSTRACT v
ÖNSÖZ vi
1. GİRİŞ 1
2. KAYNAK ARAŞTIRMASI 2
3. MATERYAL VE YÖNTEM 4
4. ARAŞTIRMA SONUÇLARI VE TARTIŞMA 8
5. SONUÇLAR VE ÖNERİLER 9
KAYNAKLAR 13
EKLER 14
ÖZGEÇMİŞ 15

---
**SİMGELER VE KISALTMALAR**

**Simgeler**
%: Yüzde
≥: Büyük veya eşit
≤: Küçük veya eşit
≠: Eşit değil
≈: Yaklaşık eşit
>: Büyüktür
<: Küçüktür

**Kısaltmalar**
API: Application Programming Interface
CBV: Class-Based Views
CRUD: Create, Read, Update, Delete
CSRF: Cross-Site Request Forgery
CSS: Cascading Style Sheets
DRF: Django REST Framework
FBV: Function-Based Views
HTML: HyperText Markup Language
HTTP/HTTPS: HyperText Transfer Protocol
JS: JavaScript
JWT: JSON Web Token
MVC: Model-View-Controller
MTV: Model-Template-View
ORM: Object-Relational Mapping
PBKDF2: Password-Based Key Derivation Function 2
REST: Representational State Transfer
RBAC: Role-Based Access Control
SMTP: Simple Mail Transfer Protocol
SPA: Single Page Application
SQL: Structured Query Language
URL: Uniform Resource Locator
XSS: Cross-Site Scripting
LMS: Learning Management System

---
**1. GİRİŞ**

Eğitim teknolojilerinin hızla geliştiği günümüzde, geleneksel eğitim yöntemlerinin yanında dijital araçların kullanımı giderek artmaktadır. Özellikle uzaktan eğitim ve hibrit eğitim modellerinin yaygınlaşmasıyla birlikte, eğitim kurumlarının dijitalleşme ihtiyacı daha da belirgin hale gelmiştir. Bu süreçte, öğrenci-öğretmen etkileşimini kolaylaştıran, ders yönetimini dijitalleştiren, sınav ve değerlendirme süreçlerini otomatize eden web tabanlı sistemlere olan ihtiyaç artmıştır.

Bu proje kapsamında, Django web framework'ü (Django Software Foundation, 2024) kullanılarak geliştirilen Kurs Yönetim Sistemi, sadece temel ders yönetimini değil, aynı zamanda kapsamlı bir sınav sistemi, otomatik notlandırma, transkript oluşturma ve anlık iletişim gibi ileri seviye özellikleri de barındırmaktadır.

**1.1. Proje Tanımı**
Django Kurs Yönetim Sistemi, 11 farklı modülden oluşan (users, students, teachers, courses, notes, quiz, gradebook, forum, academic, enrollment, utils) bütünleşik bir eğitim platformudur. Sistem, Django 4.2.x (Django Software Foundation, 2024) ve Bootstrap 5.3 (Bootstrap Team, 2024) teknolojileri üzerine inşa edilmiştir. REST API desteği (Django REST Framework, 2024) sayesinde mobil ve harici sistemlerle entegrasyona açıktır.

**1.2. Problem Tanımı**
Mevcut sistemlerde karşılaşılan temel sorunlar; parçalı yapı (sınav için ayrı, notlar için ayrı sistem kullanımı), kullanıcı deneyimi eksiklikleri, mobil uyumsuzluk ve özelleştirme zorluklarıdır. Ayrıca kağıt tabanlı sınav ve ödev süreçleri hem maliyetli hem de hata riskine açıktır.

**1.3. Proje Hedefleri**
- **Teknik Hedefler:** Django MTV mimarisine (Django Software Foundation, 2024) uygun, modüler (11 modül) yapı, REST API altyapısı, güvenli ve performanslı bir sistem geliştirmek.
- **Fonksiyonel Hedefler:** Çoktan seçmeli sınav sistemi, otomatik not hesaplama, transkript üretimi, anlık mesajlaşma sistemi.
- **Performans Hedefleri:** Hızlı sayfa yükleme, optimize edilmiş veritabanı sorguları.

**1.4. Proje Kapsamı**
Proje; Kullanıcı Yönetimi, Ders Yönetimi, Sınav Sistemi (Quiz), Not Defteri (Gradebook), Mesajlaşma (Forum), Akademik Dönem Yönetimi modüllerini kapsamaktadır. Sistem, Selçuk Üniversitesi Eğitim-Öğretim Yönetmeliği (Selçuk Üniversitesi, 2024) standartlarına uygun olarak geliştirilmiştir.

---
**2. KAYNAK ARAŞTIRMASI**

**2.1. Web Tabanlı Eğitim Sistemleri**
Moodle, Blackboard ve Canvas gibi global LMS sistemleri incelenmiştir. Bu sistemlerin karmaşıklığı ve maliyetleri karşısında, Django tabanlı özelleştirilebilir bir çözümün KOBİ ve orta ölçekli eğitim kurumları için daha uygun olduğu değerlendirilmiştir.

**2.2. Django Framework**
Python (Python Software Foundation, 2024) tabanlı Django, "batteries included" felsefesi ile kimlik doğrulama, admin paneli, ORM ve güvenlik özelliklerini hazır sunması nedeniyle tercih edilmiştir (Django Software Foundation, 2024). Instagram, Pinterest ve Udemy gibi platformların da Django kullanması, teknolojinin ölçeklenebilirliğini kanıtlamaktadır.

**2.3. Teknoloji Seçimi**
- **Backend:** Django 4.2.x (Django Software Foundation, 2024) - Güvenlik ve hız
- **API:** Django REST Framework (Django REST Framework, 2024) - Mobil entegrasyon
- **Frontend:** Bootstrap 5.3 (Bootstrap Team, 2024) - Responsive tasarım
- **Veritabanı:** SQLite3 (Geliştirme) / PostgreSQL (Prodüksiyon)
- **Yan Bileşenler:** Pillow (Görsel işleme), Openpyxl (Excel raporlama), ReportLab (PDF çıktıları)

---
**3. MATERYAL VE YÖNTEM**

**3.1. Sistem Mimarisi**
Sistem, MTV (Model-Template-View) mimarisine uygun olarak tasarlanmıştır. 11 ana modül (app) birbirinden bağımsız çalışabilecek şekilde kurgulanmıştır.
- **Modüller:** users, students, teachers, courses, notes, quiz, gradebook, forum, academic, enrollment, utils.

**3.2. Veritabanı Tasarımı**
Veritabanı şeması genişletilerek şu ana tablolar oluşturulmuştur:
- **Kullanıcı:** User, UserProfile
- **Akademik:** AcademicYear, AcademicTerm
- **Ders:** Course, CourseGroup, Enrollment
- **Sınav:** Quiz, Question, QuestionBank, QuizAttempt, QuizAnswer
- **Not:** Grade, GradeScale, Transcript
- **İletişim:** Message, MessageThread, Announcement

**3.3. Geliştirme Araçları**
VS Code IDE, Git versiyon kontrolü, Postman (API testi), DB Browser for SQLite.

---
**4. ARAŞTIRMA SONUÇLARI VE TARTIŞMA**

**4.1. Sistem Mimarisi ve Teknoloji Seçimi Sonuçları**
Proje, 11 modül ve yaklaşık 15.000+ satır Python kodu, 8.000+ satır Template kodu ile tamamlanmıştır. Modüler yapı sayesinde "Quiz" veya "Forum" modülleri istendiğinde sisteme eklenip çıkarılabilmektedir.

**4.1.1. Sınav ve Soru Bankası Sistemi (Quiz Modülü)**
Geliştirilen quiz modülü ile öğretmenler soru bankaları oluşturabilmekte, bu bankalardan rastgele soru seçimi ile sınavlar hazırlayabilmektedir. Öğrenciler sınavları online çözmekte ve sonuçlar anında not defterine işlenmektedir.

**4.1.2. Not Defteri ve Transkript (Gradebook Modülü)**
Selçuk Üniversitesi not sistemine uygun (AA, BA, vb.) harf notu hesaplama algoritması başarıyla entegre edilmiştir. Öğrenciler transkriptlerini PDF olarak indirebilmektedir.

**4.1.3. Mesajlaşma (Forum Modülü)**
Sistem içi güvenli mesajlaşma altyapısı kurulmuş, öğrenci ve öğretmenlerin iletişim kurması kolaylaştırılmıştır.

---
**5. SONUÇLAR VE ÖNERİLER**

**5.1. Sonuçlar**
Django Kurs Yönetim Sistemi projesi başarıyla tamamlanmıştır. Elde edilen temel kazanımlar:
1.  **Kapsamlı Modüler Yapı:** 11 farklı modülün entegre çalışması sağlanmıştır.
2.  **Sınav Sistemi:** Çoktan seçmeli ve otomatik puanlanan sınav altyapısı kurulmuştur.
3.  **Raporlama:** PDF transkript ve Excel öğrenci listesi export özellikleri eklenmiştir.
4.  **Güvenlik:** Django'nun yerleşik güvenlik önlemleri (CSRF, XSS koruması) ve Rol Tabanlı Erişim Kontrolü (RBAC) uygulanmıştır.
5.  **API Desteği:** Mobil uygulamalar için RESTful API uçları hazırlanmıştır.

**5.2. Öneriler ve Gelecek Geliştirmeler**
1.  **Video Konferans:** Zoom veya BigBlueButton API entegrasyonu ile canlı ders özelliği eklenebilir.
2.  **Yapay Zeka:** Sınav sorularının zorluk seviyesini öğrenci başarısına göre ayarlayan adaptif bir sistem geliştirilebilir.
3.  **Mobil Uygulama:** Mevcut API kullanılarak React Native veya Flutter ile mobil uygulama geliştirilmelidir.
4.  **Redis Cache:** Yüksek trafikli durumlar için önbellekleme mekanizması devreye alınmalıdır.

---
**KAYNAKLAR**

Bootstrap Team. (2024). Bootstrap 5.3 Documentation. Retrieved January 2025. https://getbootstrap.com/docs/5.3/

Botpress Inc. (2024). Botpress Documentation - Conversational AI Platform. Retrieved January 2025. https://botpress.com/docs

Django REST Framework. (2024). Django REST Framework Documentation. Retrieved January 2025. https://www.django-rest-framework.org/

Django Software Foundation. (2024). Django 4.2 Documentation. Retrieved January 2025. https://docs.djangoproject.com/en/4.2/

Python Software Foundation. (2024). Python 3.11 Documentation. Retrieved January 2025. https://docs.python.org/3.11/

Selçuk Üniversitesi. (2024). Önlisans ve Lisans Eğitim-Öğretim Yönetmeliği. Retrieved January 2025. https://www.selcuk.edu.tr/mevzuat


---
**EKLER**

**EK-1: Kontrol Formu**
(Mevcut form korunmuştur)

**EK-2: Ekran Görüntüleri**
1. Öğrenci Dashboard
2. Öğretmen Dashboard
3. Admin Dashboard
4. Sınav Oluşturma Ekranı
5. Not Defteri ve Transkript

**EK-3: Veritabanı Şeması**
(Proje dosyasında mevcut ER diyagramı)

**EK-4: API Dokümantasyonu**
(Swagger/OpenAPI çıktıları)

---
**ÖZGEÇMİŞ**

**KİŞİSEL BİLGİLER**
Adı Soyadı: Metin Selçukarslan
Uyruğu: TC Vatandaşı
Doğum Yeri ve Tarihi: Bursa 26.07.2001
Telefon: 5537134322
E-mail: 223301105@ogr.selcuk.edu.tr

**EĞİTİM**
- **Lise:** Zekikonukoğlu Anadolu Lisesi İnegöl/Bursa (2020)
- **Üniversite:** Hacettepe Üniversitesi Bilgisayar Programcılığı (2021)
- **Lisans:** Selçuk Üniversitesi Bilgisayar Mühendisliği (Devam ediyor)

**YETKİNLİKLER**
- **Diller:** Python, JavaScript, SQL
- **Frameworks:** Django, Django REST Framework, Bootstrap
- **Araçlar:** Git, VS Code, Postman
- **Yabancı Dil:** İngilizce

**PROJELERİ**
- Django Kurs Yönetim Sistemi (Bitirme Projesi)
