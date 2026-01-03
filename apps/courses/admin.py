"""
Courses Admin - Admin Paneli (Sistem Yöneticisi Görevleri)
Admin: Ders tanımlar, öğretmen atar, öğrencileri derslere kaydeder
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Enrollment, Assignment, Announcement


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Ders Yönetimi - Admin İşlevi"""
    
    list_display = [
        'code',
        'name',
        'credits',
        'department',
        'semester',
        'durum_badge',
    ]
    
    list_filter = ['status', 'department', 'semester']
    
    search_fields = ['code', 'name', 'department']
    
    actions = ['dersleri_aktif_et', 'dersleri_pasif_et']
    
    # Sadece gerekli alanlar
    fields = [
        'code',
        'name',
        'department',
        'credits',
        'semester',
        'description',
        'status',
    ]
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'active': '#51cf66',
            'inactive': '#868e96',
            'archived': '#adb5bd'
        }
        labels = {
            'active': 'Aktif',
            'inactive': 'Pasif',
            'archived': 'Arşivlendi'
        }
        color = colors.get(obj.status, '#868e96')
        label = labels.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            label
        )
    durum_badge.short_description = 'Durum'
    
    def dersleri_aktif_et(self, request, queryset):
        """Dersleri aktif et"""
        count = queryset.update(status='active')
        self.message_user(request, f'{count} ders aktif edildi')
    dersleri_aktif_et.short_description = '✓ Seçilenleri aktif et'
    
    def dersleri_pasif_et(self, request, queryset):
        """Dersleri pasif et"""
        count = queryset.update(status='inactive')
        self.message_user(request, f'{count} ders pasif edildi')
    dersleri_pasif_et.short_description = '✗ Seçilenleri pasif et'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Ders Kaydı Yönetimi - Admin İşlevi"""
    
    list_display = [
        'ogrenci_bilgi',
        'ders_kodu',
        'ders_adi',
        'grup',
        'durum_badge',
        'kayit_tarihi',
    ]
    
    list_filter = ['status', 'group__course__department', 'group__course']
    
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__school_number',
        'group__course__name',
        'group__course__code',
    ]
    
    autocomplete_fields = ['student']
    
    actions = ['derse_kaydet', 'dersten_cikar']
    
    # Sadece gerekli alanlar
    fields = ['student', 'group', 'status']
    
    list_per_page = 50  # Sayfa başına 50 kayıt
    
    def ogrenci_bilgi(self, obj):
        """Öğrenci bilgisi - Kompakt"""
        return format_html(
            '<div style="line-height: 1.4;"><strong>{}</strong><br><small style="color: #666;">{}</small></div>',
            f"{obj.student.first_name} {obj.student.last_name}",
            obj.student.school_number
        )
    ogrenci_bilgi.short_description = 'Öğrenci'
    
    def ders_kodu(self, obj):
        """Ders kodu"""
        return obj.group.course.code
    ders_kodu.short_description = 'Kod'
    
    def ders_adi(self, obj):
        """Ders adı"""
        return obj.group.course.name
    ders_adi.short_description = 'Ders'
    
    def grup(self, obj):
        """Grup"""
        return obj.group.name
    grup.short_description = 'Grup'
    
    def kayit_tarihi(self, obj):
        """Kayıt tarihi"""
        return obj.enrollment_date.strftime('%d.%m.%Y')
    kayit_tarihi.short_description = 'Kayıt Tarihi'
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'enrolled': '#51cf66',
            'pending': '#ffa94d',
            'dropped': '#ff6b6b',
            'completed': '#339af0'
        }
        labels = {
            'enrolled': 'Kayıtlı',
            'pending': 'Beklemede',
            'dropped': 'Çıkarıldı',
            'completed': 'Tamamlandı'
        }
        color = colors.get(obj.status, '#868e96')
        label = labels.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            label
        )
    durum_badge.short_description = 'Durum'
    
    def derse_kaydet(self, request, queryset):
        """Öğrencileri derse kaydet"""
        count = queryset.update(status='enrolled')
        self.message_user(request, f'{count} öğrenci derse kaydedildi')
    derse_kaydet.short_description = '✓ Seçilenleri derse kaydet'
    
    def dersten_cikar(self, request, queryset):
        """Öğrencileri dersten çıkar"""
        count = queryset.update(status='dropped')
        self.message_user(request, f'{count} öğrenci dersten çıkarıldı')
    dersten_cikar.short_description = '✗ Seçilenleri dersten çıkar'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Duyuru Yönetimi"""
    
    list_display = ['title', 'ders_adi', 'teacher', 'durum_badge', 'create_date']
    list_filter = ['status', 'create_date', 'group__course']
    search_fields = ['title', 'content', 'group__course__name']
    date_hierarchy = 'create_date'
    
    def ders_adi(self, obj):
        return f"{obj.group.course.code} - {obj.group.course.name}"
    ders_adi.short_description = 'Ders'
    
    def durum_badge(self, obj):
        colors = {'active': '#51cf66', 'inactive': '#868e96', 'archived': '#adb5bd'}
        color = colors.get(obj.status, '#868e96')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    durum_badge.short_description = 'Durum'
