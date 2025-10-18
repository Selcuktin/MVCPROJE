# MVC Architecture Overview

## 🎯 MVC Akışı (Flow)

```
User Request → View → Controller → Service → Model
                ↓         ↓         ↓        ↓
User Response ← View ← Controller ← Service ← Model
```

### Detaylı Akış:
1. **User** sends a request to **View**
2. **View** calls the appropriate **Controller** 
3. **Controller** executes a **Service** function
4. **Service** interacts with the **Model**
5. Response data flows back: **Model** → **Service** → **Controller** → **View** → **Template**

## 📋 Katman Sorumlulukları (Layer Responsibilities)

### 🗄️ Model Layer (`models.py`)
- **Sorumluluk**: Data structure & ORM logic
- **İçerik**: 
  - Database table definitions
  - Field definitions and constraints
  - Model relationships (ForeignKey, ManyToMany)
  - Model methods for data validation
- **Kural**: Sadece Service katmanı tarafından kullanılır

### 🔧 Service Layer (`services.py`)
- **Sorumluluk**: Business logic & data processing
- **İçerik**:
  - Database queries (Model.objects.filter(), get(), create())
  - Data calculations and processing
  - Complex business rules
  - Data validation and transformation
- **Kural**: Model ile doğrudan etkileşim kurar, Controller tarafından çağrılır

### 🎮 Controller Layer (`controllers.py`)
- **Sorumluluk**: Request handling & routing
- **İçerik**:
  - HTTP request processing
  - Service method calls
  - Context data preparation
  - Permission checks
- **Kural**: Service katmanını çağırır, View'a context döner

### 👁️ View Layer (`views.py`)
- **Sorumluluk**: Rendering templates
- **İçerik**:
  - Template rendering
  - Controller method calls
  - HTTP response generation
- **Kural**: Sadece Controller çağrısı yapar, başka mantık içermez

## 🔄 Katmanlar Arası İletişim Kuralları

### ✅ İzin Verilen İletişimler:
- **View** → **Controller**
- **Controller** → **Service** 
- **Service** → **Model**

### ❌ Yasak İletişimler:
- **View** → **Service** (doğrudan)
- **View** → **Model** (doğrudan)
- **Controller** → **Model** (doğrudan)

## 📁 Dosya Yapısı

```
app_name/
├── models.py          # Model Layer
├── services.py        # Service Layer  
├── controllers.py     # Controller Layer
├── views.py          # View Layer
├── forms.py          # Form definitions
├── urls.py           # URL routing
└── templates/app_name/
    ├── list.html
    ├── detail.html
    ├── form.html
    └── delete.html
```

## 💡 Örnek Implementasyon

### 1. Service Layer Örneği:
```python
# services.py
"""Service Layer: Business logic and data processing operations."""

class StudentService:
    def get_student_grades(self, student_id):
        student = Student.objects.get(id=student_id)
        grades = Grade.objects.filter(student=student)
        avg = round(sum(g.score for g in grades) / len(grades), 2) if grades else 0
        return {"student": student, "grades": grades, "average": avg}
```

### 2. Controller Layer Örneği:
```python
# controllers.py
"""Controller Layer: Handles request routing and response context generation."""

class StudentController:
    def __init__(self):
        self.student_service = StudentService()
    
    def student_report_controller(self, request, student_id):
        data = self.student_service.get_student_grades(student_id)
        context = {
            "student": data["student"], 
            "grades": data["grades"], 
            "average": data["average"]
        }
        return context
```

### 3. View Layer Örneği:
```python
# views.py
"""View Layer: Renders templates and handles HTTP responses."""

def student_report_view(request, student_id):
    controller = StudentController()
    context = controller.student_report_controller(request, student_id)
    return render(request, "students/student_report.html", context)
```

## 🧪 Test Yapısı

### Controller Tests:
```python
# tests/controllers/test_students.py
def test_student_report_controller():
    # Test HTTP routing and context generation
    pass
```

### Service Tests:
```python
# tests/services/test_students.py  
def test_get_student_grades():
    # Test business logic and data calculations
    pass
```

## 🎯 MVC Avantajları

### ✅ Kod Okunabilirliği
- Her katmanın sorumluluğu net
- Kod organizasyonu düzenli
- Debugging kolaylaşır

### ✅ Test Edilebilirlik  
- Her katman ayrı ayrı test edilebilir
- Unit testler daha spesifik
- Mock'lama kolaylaşır

### ✅ Bakım Kolaylığı
- Değişiklikler izole edilir
- Kod tekrarı azalır
- Yeni özellik ekleme kolaylaşır

### ✅ Takım Çalışması
- Farklı geliştiriciler farklı katmanlarda çalışabilir
- Merge conflict'leri azalır
- Code review süreci iyileşir

## 🔧 Uygulama Rehberi

### Adım 1: Service Katmanı Oluştur
- Tüm database işlemlerini services.py'ye taşı
- Business logic'i merkezi hale getir

### Adım 2: Controller Katmanı Oluştur  
- View'lardan iş mantığını controllers.py'ye taşı
- Service çağrıları yap, context döndür

### Adım 3: View Katmanını Temizle
- Sadece Controller çağrısı ve render işlemi bırak
- Tüm business logic'i kaldır

### Adım 4: Test Et
- Her katman için unit testler yaz
- Integration testler ekle

## 📊 Başarı Metrikleri

- ✅ Her View fonksiyonu max 5 satır
- ✅ Controller'lar sadece Service çağrısı yapar  
- ✅ Service'ler sadece Model ile etkileşir
- ✅ Kod tekrarı %90 azalır
- ✅ Test coverage %100 artar