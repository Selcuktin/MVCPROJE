# 📚 Proje Dosya Rehberi

## Her Dosyanın Ne İşe Yaradığı

### 📁 **Ana Klasör Yapısı**

```
MVCPROJE/
├── apps/           → Django uygulamaları (modüler yapı)
├── config/         → Proje ayarları
├── utils/          → Yardımcı araçlar
├── templates/      → HTML şablonları
├── static/         → CSS, JS, görseller
├── logs/           → Sistem logları
└── manage.py       → Django komut satırı
```

---

## 🎯 **Python Dosya Tipleri ve Görevleri**

### 1. **models.py** - 📊 Veritabanı Modelleri
**Ne yapar?** Database tablolarını Python sınıfları olarak tanımlar (ORM - Object Relational Mapping)

**Örnek:**
```python
class Student(models.Model):
    first_name = models.CharField(max_length=100)
    # Bu kod veritabanında 'students' tablosu oluşturur
```

**Bulunduğu yerler:**
- `apps/students/models.py` - Öğrenci modeli
- `apps/courses/models.py` - Ders, ödev, duyuru modelleri
- `apps/teachers/models.py` - Öğretmen modeli
- `apps/notes/models.py` - Not modeli
- `utils/models.py` - ActivityLog, ChangeHistory

---

### 2. **views.py** - 🎯 İş Mantığı (Controller)
**Ne yapar?** HTTP isteklerini işler, veritabanından veri çeker, HTML render eder

**Örnek:**
```python
def student_list(request):
    students = Student.objects.all()  # DB'den veri al
    return render(request, 'students/list.html', {'students': students})
```

**İki tip view var:**
- **Class-Based Views (CBV):** ListView, DetailView, CreateView, UpdateView, DeleteView
- **Function-Based Views (FBV):** Basit fonksiyonlar

**Bulunduğu yerler:**
- `apps/students/views.py` - Öğrenci CRUD işlemleri
- `apps/courses/views.py` - Ders, ödev, duyuru işlemleri
- `apps/teachers/views.py` - Öğretmen işlemleri
- `apps/users/views.py` - Login, logout, register
- `apps/users/api_views.py` - JWT API endpoint'leri
- `utils/views.py` - Activity log görüntüleme

---

### 3. **forms.py** - ✏️ Form Validasyonu
**Ne yapar?** Kullanıcıdan gelen verileri doğrular ve temizler

**Örnek:**
```python
class StudentForm(forms.ModelForm):
    def clean_email(self):
        email = self.cleaned_data['email']
        if Student.objects.filter(email=email).exists():
            raise ValidationError('Bu email zaten kullanılıyor')
        return email
```

**Görevleri:**
- Input validasyonu (email formatı, zorunlu alanlar)
- Hata mesajları
- Veri temizleme

**Bulunduğu yerler:**
- `apps/students/forms.py` - Öğrenci formu
- `apps/courses/forms.py` - Ders, ödev, duyuru formları
- `apps/teachers/forms.py` - Öğretmen formu
- `apps/users/forms.py` - Kullanıcı kayıt formu

---

### 4. **urls.py** - 🛣️ URL Routing
**Ne yapar?** URL pattern'lerini view fonksiyonlarına bağlar

**Örnek:**
```python
urlpatterns = [
    path('students/', views.StudentListView.as_view(), name='student_list'),
    path('students/<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),
]
```

**Pattern:**
- `/students/` → Öğrenci listesi göster
- `/students/5/` → ID=5 olan öğrenciyi göster

**Bulunduğu yerler:**
- `config/urls.py` - Ana URL routing (tüm app'leri dahil eder)
- `apps/*/urls.py` - Her app'in kendi URL'leri
- `utils/urls.py` - Activity log URL'leri

---

### 5. **admin.py** - 🔧 Admin Panel Ayarları
**Ne yapar?** Django admin panelini özelleştirir

**Örnek:**
```python
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email']
    search_fields = ['first_name', 'last_name']
```

**Görevleri:**
- Admin panelde hangi alanlar görünsün?
- Arama ve filtreleme
- Toplu işlemler

**Bulunduğu yerler:**
- `apps/*/admin.py` - Her model için admin ayarları
- `utils/admin.py` - ActivityLog admin

---

### 6. **apps.py** - ⚙️ App Konfigürasyonu
**Ne yapar?** Django app'ini tanımlar

**Örnek:**
```python
class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.students'
    verbose_name = 'Öğrenciler'
```

**Görevleri:**
- App adı
- Türkçe isim (verbose_name)
- Signal handler'ları başlatma

---

### 7. **tests.py** - 🧪 Test Dosyası
**Ne yapar?** Unit ve integration testleri

**Örnek:**
```python
class StudentTest(TestCase):
    def test_student_creation(self):
        student = Student.objects.create(first_name='John')
        self.assertEqual(student.first_name, 'John')
```

**Kullanım:**
```bash
python manage.py test
```

---

### 8. **migrations/** - 🔄 Database Değişiklikleri
**Ne yapar?** Database şeması değişiklik geçmişini saklar

**Örnek dosyalar:**
- `0001_initial.py` - İlk tablo oluşturma
- `0002_add_field.py` - Yeni alan ekleme

**Komutlar:**
```bash
python manage.py makemigrations  # Migration oluştur
python manage.py migrate         # Database'e uygula
```

---

### 9. **serializers.py** - 📦 API Serialization
**Ne yapar?** Model ↔ JSON dönüşümü (REST API için)

**Örnek:**
```python
class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'email']
```

**Çıktı:**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com"
}
```

---

### 10. **decorators.py** - 🎨 Decorator Fonksiyonları
**Ne yapar?** Fonksiyon sarmalayıcıları (wrapper)

**Örnek:**
```python
@login_required
@student_required
def my_view(request):
    # Sadece giriş yapmış öğrenciler erişebilir
```

**Bulunduğu yer:**
- `utils/decorators.py` - Özel decorator'lar

---

### 11. **middleware.py** - 🔀 Request/Response İşleme
**Ne yapar?** Her HTTP isteğinde araya girer

**Örnek:**
```python
class LoggingMiddleware:
    def process_request(self, request):
        # Her istekte çalışır
        log_activity(request.user, 'page_view')
```

**Bulunduğu yer:**
- `utils/logging_middleware.py` - Activity logging

---

### 12. **permissions.py** - 🔐 Yetkilendirme
**Ne yapar?** Özel permission sınıfları

**Örnek:**
```python
class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.userprofile.user_type in ['teacher', 'admin']
```

---

### 13. **validators.py** - ✅ Özel Validasyonlar
**Ne yapar?** Custom validation fonksiyonları

**Örnek:**
```python
def validate_tc_no(value):
    if len(value) != 11:
        raise ValidationError('TC No 11 haneli olmalı')
```

---

### 14. **helpers.py** - 🛠️ Yardımcı Fonksiyonlar
**Ne yapar?** Genel kullanım fonksiyonları

**Örnek:**
```python
def calculate_gpa(grades):
    return sum(grades) / len(grades)
```

---

### 15. **api_views.py** - 🌐 API Endpoint'leri
**Ne yapar?** REST API endpoint'leri (JWT authentication ile)

**Örnek:**
```python
@api_view(['POST'])
def register_api(request):
    # API üzerinden kullanıcı kaydı
    return Response({'token': '...'})
```

**Endpoint'ler:**
- POST `/api/token/` - JWT token al
- POST `/api/register/` - Kayıt ol
- POST `/api/logout/` - Çıkış yap
- GET `/api/profile/` - Profil bilgisi

---

## 📂 **Klasör Bazlı Açıklama**

### `apps/users/`
**Görev:** Kullanıcı yönetimi ve authentication
- **models.py:** User, UserProfile
- **views.py:** Login, logout, register (web)
- **api_views.py:** JWT authentication (API)
- **forms.py:** Kayıt formu

### `apps/students/`
**Görev:** Öğrenci yönetimi
- **models.py:** Student modeli
- **views.py:** CRUD işlemleri, dashboard
- **forms.py:** Öğrenci formu

### `apps/teachers/`
**Görev:** Öğretmen yönetimi
- **models.py:** Teacher modeli
- **views.py:** CRUD işlemleri, dashboard
- **forms.py:** Öğretmen formu

### `apps/courses/`
**Görev:** Ders, ödev, duyuru yönetimi
- **models.py:** Course, CourseGroup, Assignment, Submission, Announcement
- **views.py:** Tüm ders işlemleri, PDF/Excel export
- **forms.py:** Ders, ödev, duyuru formları

### `apps/notes/`
**Görev:** Not yönetimi
- **models.py:** Note modeli (vize, final, bütünleme)
- **views.py:** Not CRUD işlemleri
- **forms.py:** Not giriş formu

### `utils/`
**Görev:** Yardımcı araçlar
- **models.py:** ActivityLog, ChangeHistory
- **logging_middleware.py:** Otomatik aktivite loglaması
- **views.py:** Log görüntüleme
- **decorators.py:** @student_required, @teacher_required
- **permissions.py:** Özel permission'lar

### `config/`
**Görev:** Proje ana ayarları
- **settings.py:** Tüm Django ayarları (database, apps, middleware, JWT)
- **urls.py:** Ana URL routing
- **wsgi.py:** Production deployment

---

## 🎓 **Öğrenme Sırası (Yeni Başlayanlar İçin)**

1. **models.py** → Database tablolarını anla
2. **urls.py** → URL pattern'leri öğren
3. **views.py** → İş mantığını kavra
4. **forms.py** → Form validasyonu anla
5. **templates/** → HTML şablonları
6. **admin.py** → Admin paneli
7. **api_views.py** → REST API (ileri seviye)

---

## 🔍 **Hızlı Arama Rehberi**

**"Öğrenci nasıl oluşturulur?"**
→ `apps/students/forms.py` ve `apps/students/views.py`

**"Not nasıl girilir?"**
→ `apps/notes/views.py` ve `apps/courses/views.py` (GradeUpdateView)

**"PDF rapor nasıl oluşur?"**
→ `apps/courses/views.py` → `export_pdf()` metodu

**"Login nasıl çalışır?"**
→ `apps/users/views.py` → CustomLoginView

**"JWT authentication nedir?"**
→ `apps/users/api_views.py`

**"Aktivite logları nerede?"**
→ `utils/views.py` → activity_log_list

---

**Güncelleme:** 10 Ekim 2025  
**Durum:** ✅ Tüm dosyalara docstring eklendi

