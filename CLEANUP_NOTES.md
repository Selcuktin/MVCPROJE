# Temizlik İşlemi - Assignment, Submission, Announcement Kaldırma

## Tamamlanan İşlemler

1. ✅ `apps/courses/models.py` - Assignment, Submission, Announcement, PlagiarismReport modelleri silindi
2. ✅ `apps/courses/admin.py` - İlgili admin kayıtları silindi
3. ✅ `apps/courses/urls.py` - Assignment, Submission, Announcement URL'leri silindi
4. ✅ `apps/courses/views.py` - İlgili view class'ları ve fonksiyonları silindi
5. ✅ `apps/users/views.py` - ControlPanelView silindi
6. ✅ `apps/users/urls.py` - control_panel URL'i kaldırıldı

## Yapılması Gerekenler

### Dosya Silmeleri
- [ ] `apps/courses/forms.py` - AssignmentForm, SubmissionForm, AnnouncementForm sil
- [ ] `apps/users/services.py` - Assignment/Announcement referanslarını kaldır veya yorum satırına al
- [ ] `apps/users/controllers.py` - get_control_panel_context fonksiyonunu kaldır
- [ ] `apps/courses/controllers.py` - AssignmentController'ı kaldır (varsa)
- [ ] `apps/courses/services.py` - Assignment/Submission işlevlerini kaldır (varsa)

### Template Silmeleri
- [ ] `apps/users/templates/users/control_panel.html` - Dosyayı sil
- [ ] `apps/courses/templates/courses/assignment_*.html` - Tüm assignment template'lerini sil
- [ ] `apps/courses/templates/courses/submission_*.html` - Tüm submission template'lerini sil  
- [ ] `apps/courses/templates/courses/announcement_*.html` - Tüm announcement template'lerini sil
- [ ] `apps/students/templates/students/assignments.html` - Öğrenci ödev sayfasını sil (varsa)
- [ ] `apps/teachers/templates/teachers/assignments.html` - Öğretmen ödev sayfasını sil (varsa)

### Dashboard Güncellemeleri
- [ ] `apps/users/templates/users/home.html` - Duyurular widget'ını kaldır
- [ ] `templates/base.html` - Menüden "Ödevler", "Duyurular", "Kontrol Paneli" linklerini kaldır

### Migration ve Database
- [ ] Migration oluştur: `python manage.py makemigrations courses --name remove_assignment_submission_announcement`
- [ ] Migration'ı çalıştır: `python manage.py migrate`

### Test ve Temizlik
- [ ] Projeyi çalıştır ve hataları kontrol et
- [ ] Kullanılmayan import'ları temizle
- [ ] Hala referans veren kodları düzelt

## Notlar

- Assignment, Submission, Announcement modelleri ve ilişkili tüm kodlar tamamen kaldırılıyor
- Control Panel sayfası tamamen kaldırılıyor
- Dashboard'daki duyurular bölümü kaldırılacak
- Ödevler sayfaları (student ve teacher) tamamen kaldırılacak
