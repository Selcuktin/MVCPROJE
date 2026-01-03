"""
Students Admin - Öğrenci Yönetimi
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Student
from apps.courses.models import Enrollment


class StudentEnrollmentInline(admin.TabularInline):
    """Öğrencinin dersleri - Hızlı ekleme/çıkarma"""
    model = Enrollment
    extra = 1
    fields = ['group', 'status', 'enrollment_date']
    readonly_fields = ['enrollment_date']
    verbose_name = "Ders Kaydı"
    verbose_name_plural = "Ders Kayıtları"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Öğrenci Yönetimi"""
    
    list_display = [
        'school_number',
        'first_name',
        'last_name',
        'email',
        'phone',
        'durum_badge',
    ]
    
    list_filter = ['status', 'gender']
    
    search_fields = [
        'school_number',
        'first_name',
        'last_name',
        'email',
    ]
    
    actions = ['ogrencileri_aktif_et', 'ogrencileri_pasif_et']
    
    inlines = [StudentEnrollmentInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('school_number', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Durum', {
            'fields': ('status', 'gender')
        }),
    )
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'active': '#51cf66',
            'inactive': '#868e96',
            'suspended': '#ff6b6b',
            'graduated': '#339af0',
            'dropped': '#adb5bd'
        }
        labels = {
            'active': 'Aktif',
            'inactive': 'Pasif',
            'suspended': 'Askıda',
            'graduated': 'Mezun',
            'dropped': 'Ayrıldı'
        }
        color = colors.get(obj.status, '#868e96')
        label = labels.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 6px; font-weight: 600;">{}</span>',
            color,
            label
        )
    durum_badge.short_description = 'Durum'
    
    def ogrencileri_aktif_et(self, request, queryset):
        """Öğrencileri aktif et"""
        count = queryset.update(status='active')
        self.message_user(request, f'{count} öğrenci aktif edildi')
    ogrencileri_aktif_et.short_description = '✓ Seçilenleri aktif et'
    
    def ogrencileri_pasif_et(self, request, queryset):
        """Öğrencileri pasif et"""
        count = queryset.update(status='inactive')
        self.message_user(request, f'{count} öğrenci pasif edildi')
    ogrencileri_pasif_et.short_description = '✗ Seçilenleri pasif et'
