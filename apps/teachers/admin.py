"""
Teachers Admin - Öğretmen Yönetimi
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Teacher
from apps.courses.models import CourseGroup


class TeacherCourseInline(admin.TabularInline):
    """Öğretmenin dersleri - Hızlı ekleme/çıkarma"""
    model = CourseGroup
    extra = 1
    fields = ['course', 'name', 'capacity']
    verbose_name = "Ders"
    verbose_name_plural = "Dersler"


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Öğretmen Yönetimi"""
    
    list_display = [
        'first_name',
        'last_name',
        'title',
        'email',
        'phone',
        'durum_badge',
    ]
    
    list_filter = ['status', 'title']
    
    search_fields = [
        'first_name',
        'last_name',
        'email',
        'title',
    ]
    
    actions = ['ogretmenleri_aktif_et', 'ogretmenleri_pasif_et']
    
    inlines = [TeacherCourseInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('first_name', 'last_name', 'title', 'email', 'phone')
        }),
        ('Durum', {
            'fields': ('status',)
        }),
    )
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'active': '#51cf66',
            'inactive': '#868e96',
            'on_leave': '#ffa94d',
            'retired': '#adb5bd'
        }
        labels = {
            'active': 'Aktif',
            'inactive': 'Pasif',
            'on_leave': 'İzinli',
            'retired': 'Emekli'
        }
        color = colors.get(obj.status, '#868e96')
        label = labels.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 6px; font-weight: 600;">{}</span>',
            color,
            label
        )
    durum_badge.short_description = 'Durum'
    
    def ogretmenleri_aktif_et(self, request, queryset):
        """Öğretmenleri aktif et"""
        count = queryset.update(status='active')
        self.message_user(request, f'{count} öğretmen aktif edildi')
    ogretmenleri_aktif_et.short_description = '✓ Seçilenleri aktif et'
    
    def ogretmenleri_pasif_et(self, request, queryset):
        """Öğretmenleri pasif et"""
        count = queryset.update(status='inactive')
        self.message_user(request, f'{count} öğretmen pasif edildi')
    ogretmenleri_pasif_et.short_description = '✗ Seçilenleri pasif et'
