# 🏗️ Sistem Servisleri Dokümantasyonu

## 📋 İçindekiler
1. [Mesajlaşma Sistemi](#mesajlaşma-sistemi)
2. [Tüm Servisler](#tüm-servisler)
3. [Servis Mimarisi](#servis-mimarisi)

---

## 💬 Mesajlaşma Sistemi

### Kullanılan Modeller
**Lokasyon:** `apps/forum/models.py`

#### 1. DirectMessage (1:1 Mesajlaşma)
```python
- sender: Mesajı gönderen kullanıcı
- recipient: Mesajı alan kullanıcı
- subject: Mesaj konusu
- message: Mesaj içeriği
- is_read: Okundu mu?
- read_at: Okunma zamanı
- parent_message: Yanıt mesajları için üst mesaj
```

**Özellikler:**
- ✅ 1:1 direkt mesajlaşma
- ✅ Okundu bilgisi
- ✅ Mesaj geçmişi
- ✅ Yanıt zincirleri

#### 2. MessageThread (Grup Mesajlaşma)
```python
- course_group: Ders grubu (opsiyonel)
- title: Konu başlığı
- participants: Katılımcılar (ManyToMany)
- created_by: Oluşturan kullanıcı
```

**Özellikler:**
- ✅ Grup sohbetleri
- ✅ Ders bazlı mesajlaşma
- ✅ Çoklu katılımcı

#### 3. ForumTopic & ForumReply (Forum Sistemi)
```python
ForumTopic:
- category: Forum kategorisi
- title: Konu başlığı
- author: Yazar
- is_pinned: Sabitlenmiş mi?
- is_locked: Kilitli mi?
- views_count: Görüntülenme sayısı

ForumReply:
- topic: Bağlı konu
- author: Yazar
- content: İçerik
- is_solution: Çözüm olarak işaretlenmiş mi?
```

### Kullanılan Views
**Lokasyon:** `apps/forum/views.py`

#### Web Views (Sayfa Görünümleri)
1. **inbox** - Gelen/Giden kutusu
2. **message_compose** - Yeni mesaj oluştur
3. **message_detail** - Mesaj detayı

#### API Endpoints (Floating Chat için)
1. **api_inbox** - Sohbet listesi (son 15 konuşma)
2. **api_send_message** - Mesaj gönder
3. **api_recipients** - Mesaj gönderebilecek kişiler listesi
4. **api_thread** - İki kullanıcı arası mesaj geçmişi
5. **api_clear_conversation** - Sohbet geçmişini temizle

### Mesajlaşma Akışı

```
┌─────────────┐
│   Kullanıcı │
└──────┬──────┘
       │
       ├─── Web Arayüzü ───┐
       │                   │
       │    ┌──────────────▼──────────────┐
       │    │  inbox (Gelen/Giden Kutusu) │
       │    └──────────────┬──────────────┘
       │                   │
       │    ┌──────────────▼──────────────┐
       │    │  message_compose (Yeni)     │
       │    └──────────────┬──────────────┘
       │                   │
       │                   ▼
       │            DirectMessage Model
       │
       └─── Floating Chat ───┐
                             │
            ┌────────────────▼────────────────┐
            │  api_inbox (Sohbet Listesi)    │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │  api_thread (Mesaj Geçmişi)    │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │  api_send_message (Gönder)     │
            └────────────────┬────────────────┘
                             │
                             ▼
                      DirectMessage Model
```

### Alıcı Belirleme Mantığı

**Öğrenci ise:**
- ✅ Kendi öğretmenleri
- ✅ Aynı derslerdeki sınıf arkadaşları

**Öğretmen ise:**
- ✅ Kendi öğrencileri
- ✅ Diğer öğretmenler

---

## 🔧 Tüm Servisler

### 1. UserService
**Lokasyon:** `apps/users/services.py`

**Görevler:**
- Kullanıcı yönetimi
- Profil işlemleri
- Kimlik doğrulama

**Metodlar:**
```python
- get_user_profile(user_id)
- update_user_profile(user_id, data)
- change_password(user_id, old_password, new_password)
```

---

### 2. TeacherService
**Lokasyon:** `apps/teachers/services.py`

**Görevler:**
- Öğretmen dashboard verileri
- Öğretmen-ders ilişkileri
- Öğretmen istatistikleri

**Metodlar:**
```python
- get_teacher_dashboard_data(user)
  └─ Verdiği dersler
  └─ Toplam öğrenci sayısı
  └─ Bekleyen notlandırmalar
  └─ Aktif sınavlar
  └─ Okunmamış mesajlar

- get_teacher_courses_data(user)
  └─ Öğretmenin tüm dersleri
  └─ Her dersin öğrenci sayısı

- get_teacher_students_data(user)
  └─ Öğretmenin tüm öğrencileri
  └─ Öğrenci istatistikleri
  └─ Tamamlanan/Bekleyen ödevler

- get_teacher_assignments_data(user)
  └─ Tüm ödevler
  └─ Aktif ödevler
  └─ Notlandırma bekleyenler

- get_teacher_announcements_data(user)
  └─ Tüm duyurular
  └─ Aktif duyurular
```

**Özellikler:**
- ✅ Öğretmen izolasyonu (her öğretmen sadece kendi verilerini görür)
- ✅ Benzersiz öğrenci sayısı hesaplama
- ✅ Gerçek zamanlı istatistikler

---

### 3. StudentService
**Lokasyon:** `apps/students/services.py`

**Görevler:**
- Öğrenci dashboard verileri
- Öğrenci-ders ilişkileri
- Öğrenci istatistikleri

**Metodlar:**
```python
- get_student_dashboard_data(user)
  └─ Kayıtlı dersler
  └─ Aktif ödevler
  └─ Yaklaşan sınavlar
  └─ Not ortalaması

- get_student_courses_data(user)
  └─ Tüm dersler
  └─ Ders detayları

- get_student_grades_data(user)
  └─ Tüm notlar
  └─ Harf notları
  └─ GPA hesaplama
```

---

### 4. CourseService
**Lokasyon:** `apps/courses/services.py`

**Görevler:**
- Ders yönetimi
- Ders filtreleme
- Ders istatistikleri

**Metodlar:**
```python
- get_filtered_courses(filters)
  └─ Arama
  └─ Bölüm filtresi
  └─ Dönem filtresi

- get_course_detail(course_id)
  └─ Ders bilgileri
  └─ Öğretmen bilgileri
  └─ Kayıtlı öğrenciler

- get_course_statistics(course_id)
  └─ Toplam öğrenci
  └─ Kapasite doluluk oranı
```

---

### 5. AssignmentService
**Lokasyon:** `apps/courses/services.py`

**Görevler:**
- Ödev yönetimi
- Teslim işlemleri
- Notlandırma

**Metodlar:**
```python
- create_assignment(data)
- update_assignment(assignment_id, data)
- delete_assignment(assignment_id)
- submit_assignment(student, assignment, file)
- grade_submission(submission_id, score, feedback)
- get_assignment_statistics(assignment_id)
  └─ Teslim sayısı
  └─ Notlandırılmış sayısı
  └─ Ortalama puan
```

---

### 6. GradebookService
**Lokasyon:** `apps/gradebook/services.py`

**Görevler:**
- Not hesaplama
- Harf notu belirleme
- Transkript oluşturma

**Metodlar:**
```python
- calculate_student_course_grade(student, course_group)
  └─ Vize (%40)
  └─ Final (%60)
  └─ Bütünleme (Final yerine geçer)
  └─ Toplam puan
  └─ Harf notu (AA, BA, BB, CB, CC, DC, DD, FF)

- update_enrollment_grades(enrollment)
  └─ Enrollment modelini güncelle

- get_course_grade_statistics(course_group)
  └─ Toplam öğrenci
  └─ Notlandırılmış öğrenci
  └─ Sınıf ortalaması
  └─ Harf notu dağılımı

- get_student_transcript(student)
  └─ Tüm dersler
  └─ Notlar
  └─ GPA hesaplama
  └─ Toplam kredi
```

**Not Hesaplama Sistemi:**
```
Vize: %40
Final: %60
Bütünleme: Final yerine geçer (girilirse)

Harf Notu Tablosu (Selçuk Üniversitesi):
88-100: AA (4.00) - Mükemmel
80-87:  BA (3.50) - Çok İyi
73-79:  BB (3.00) - İyi
66-72:  CB (2.50) - Orta
60-65:  CC (2.00) - Yeterli
55-59:  DC (1.50) - Şartlı Geçer
50-54:  DD (1.00) - Şartlı Geçer
0-49:   FF (0.00) - Başarısız
```

---

### 7. EnrollmentService
**Lokasyon:** `apps/enrollment/services.py`

**Görevler:**
- Ders kayıt işlemleri
- Kayıt onaylama/reddetme
- Kayıt istatistikleri

**Metodlar:**
```python
- enroll_student(student, course_group)
- approve_enrollment(enrollment_id)
- reject_enrollment(enrollment_id)
- drop_course(enrollment_id)
- get_enrollment_statistics(course_group)
```

---

### 8. NoteService
**Lokasyon:** `apps/notes/services.py`

**Görevler:**
- Not paylaşımı
- Not yönetimi
- Not kategorileri

**Metodlar:**
```python
- create_note(data)
- update_note(note_id, data)
- delete_note(note_id)
- get_course_notes(course_id)
- get_student_notes(student_id)
```

---

### 9. AcademicTermService
**Lokasyon:** `apps/academic/services.py`

**Görevler:**
- Akademik dönem yönetimi
- Dönem geçişleri
- Dönem istatistikleri

**Metodlar:**
```python
- get_current_term()
- create_term(data)
- activate_term(term_id)
- get_term_statistics(term_id)
```

---

### 10. ReportService
**Lokasyon:** `apps/courses/services.py`

**Görevler:**
- Rapor oluşturma
- Excel export
- İstatistik raporları

**Metodlar:**
```python
- generate_course_report(course_id)
- generate_student_report(student_id)
- generate_teacher_report(teacher_id)
- export_to_excel(data)
```

---

### 11. TeacherCourseAssignmentService
**Lokasyon:** `apps/courses/services.py`

**Görevler:**
- Öğretmen-ders atamaları
- Ders grubu yönetimi

**Metodlar:**
```python
- assign_teacher_to_course(teacher_id, course_id)
- remove_teacher_from_course(teacher_id, course_id)
- get_teacher_courses(teacher_id)
```

---

## 🏛️ Servis Mimarisi

### Katmanlı Mimari

```
┌─────────────────────────────────────────┐
│           PRESENTATION LAYER            │
│         (Views, Templates, API)         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          SERVICE LAYER (Business)       │
│  ┌──────────────────────────────────┐  │
│  │  UserService                     │  │
│  │  TeacherService                  │  │
│  │  StudentService                  │  │
│  │  CourseService                   │  │
│  │  AssignmentService               │  │
│  │  GradebookService                │  │
│  │  EnrollmentService               │  │
│  │  NoteService                     │  │
│  │  AcademicTermService             │  │
│  │  ReportService                   │  │
│  └──────────────────────────────────┘  │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          DATA ACCESS LAYER              │
│         (Models, ORM, Database)         │
└─────────────────────────────────────────┘
```

### Servis Kullanım Örneği

```python
# View'da servis kullanımı
from apps.teachers.services import TeacherService

def teacher_dashboard(request):
    service = TeacherService()
    data = service.get_teacher_dashboard_data(request.user)
    
    return render(request, 'teachers/dashboard.html', data)
```

### Servis Avantajları

✅ **Separation of Concerns** - İş mantığı view'lardan ayrı
✅ **Reusability** - Aynı mantık farklı yerlerde kullanılabilir
✅ **Testability** - Servisler kolayca test edilebilir
✅ **Maintainability** - Kod daha düzenli ve bakımı kolay
✅ **Scalability** - Sistem kolayca genişletilebilir

---

## 📊 Servis İstatistikleri

| Servis | Metod Sayısı | Kullanım Alanı |
|--------|--------------|----------------|
| TeacherService | 6 | Dashboard, Dersler, Öğrenciler, Ödevler |
| StudentService | 3 | Dashboard, Dersler, Notlar |
| CourseService | 3 | Ders Listesi, Detay, İstatistikler |
| AssignmentService | 6 | Ödev Yönetimi, Teslim, Notlandırma |
| GradebookService | 4 | Not Hesaplama, Transkript, İstatistikler |
| EnrollmentService | 5 | Kayıt İşlemleri, Onay/Red |
| NoteService | 5 | Not Paylaşımı, Yönetim |
| AcademicTermService | 4 | Dönem Yönetimi |
| ReportService | 4 | Rapor Oluşturma, Export |
| UserService | 3 | Kullanıcı Yönetimi |

**Toplam:** 10 Servis, 43+ Metod

---

## 🔐 Güvenlik ve İzolasyon

### Öğretmen İzolasyonu
```python
# Her öğretmen SADECE kendi verilerini görür
teacher_groups = CourseGroup.objects.filter(
    teacher=teacher,
    status='active'
)
```

### Öğrenci İzolasyonu
```python
# Her öğrenci SADECE kayıtlı olduğu dersleri görür
student_enrollments = Enrollment.objects.filter(
    student=student,
    status='enrolled'
)
```

### Mesajlaşma İzolasyonu
```python
# Kullanıcı sadece kendi mesajlarını görür
messages = DirectMessage.objects.filter(
    Q(sender=request.user) | Q(recipient=request.user)
)
```

---

## 📝 Notlar

- Tüm servisler Django ORM kullanır
- Servisler transaction yönetimi yapar
- Servisler hata yönetimi içerir
- Servisler performans için optimize edilmiştir (select_related, prefetch_related)
- Servisler izolasyon ve güvenlik sağlar

---

**Son Güncelleme:** 20 Aralık 2025
**Versiyon:** 1.0
