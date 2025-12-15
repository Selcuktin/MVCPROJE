"""
Enrollment Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import EnrollmentMethod, EnrollmentRule


@admin.register(EnrollmentMethod)
class EnrollmentMethodAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment Method"""
    
    list_display = [
        'course_group',
        'method_type_badge',
        'is_enabled_badge',
        'enrollment_status',
        'current_capacity',
        'date_range'
    ]
    
    list_filter = [
        'method_type',
        'is_enabled',
        'course_group__course',
        'course_group__academic_term'
    ]
    
    search_fields = [
        'course_group__course__code',
        'course_group__course__name',
        'enrollment_key'
    ]
    
    fieldsets = (
        ('Genel', {
            'fields': ('course_group', 'method_type', 'is_enabled')
        }),
        ('Kapasite', {
            'fields': ('max_students',)
        }),
        ('Kayıt Anahtarı', {
            'fields': ('enrollment_key',),
            'classes': ('collapse',)
        }),
        ('Tarih Kısıtlamaları', {
            'fields': ('enrollment_start', 'enrollment_end')
        }),
        ('Self-Enrollment Ayarları', {
            'fields': ('allow_self_unenroll',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def method_type_badge(self, obj):
        """Display method type with color badge"""
        colors = {
            'manual': '#868e96',
            'self': '#51cf66',
            'key': '#ffd43b',
            'cohort': '#339af0'
        }
        color = colors.get(obj.method_type, '#868e96')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_method_type_display()
        )
    method_type_badge.short_description = 'Yöntem'
    
    def is_enabled_badge(self, obj):
        """Display enabled status"""
        if obj.is_enabled:
            return format_html('<span style="color: green;">✓ Aktif</span>')
        return format_html('<span style="color: red;">✗ Pasif</span>')
    is_enabled_badge.short_description = 'Durum'
    
    def enrollment_status(self, obj):
        """Display enrollment status"""
        if obj.is_enrollment_open:
            return format_html('<span style="color: green;">🟢 Açık</span>')
        return format_html('<span style="color: red;">🔴 Kapalı</span>')
    enrollment_status.short_description = 'Kayıt Durumu'
    
    def current_capacity(self, obj):
        """Display current capacity"""
        current = obj.current_enrollment_count
        max_val = obj.max_students or '∞'
        
        if obj.max_students:
            percentage = (current / obj.max_students) * 100
            if percentage >= 90:
                color = 'red'
            elif percentage >= 70:
                color = 'orange'
            else:
                color = 'green'
            return format_html(
                '<span style="color: {};">{} / {}</span>',
                color, current, max_val
            )
        return f'{current} / {max_val}'
    current_capacity.short_description = 'Kapasite'
    
    def date_range(self, obj):
        """Display enrollment date range"""
        if obj.enrollment_start and obj.enrollment_end:
            return f'{obj.enrollment_start.strftime("%d.%m.%Y")} - {obj.enrollment_end.strftime("%d.%m.%Y")}'
        return '-'
    date_range.short_description = 'Kayıt Tarihleri'


@admin.register(EnrollmentRule)
class EnrollmentRuleAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment Rule"""
    
    list_display = [
        'course_group',
        'rule_type_badge',
        'is_active_badge',
        'rule_details'
    ]
    
    list_filter = [
        'rule_type',
        'is_active',
        'course_group__course'
    ]
    
    search_fields = [
        'course_group__course__code',
        'course_group__course__name'
    ]
    
    fieldsets = (
        ('Genel', {
            'fields': ('course_group', 'rule_type', 'is_active')
        }),
        ('Önkoşul Ayarları', {
            'fields': ('prerequisite_course', 'min_grade'),
            'classes': ('collapse',)
        }),
        ('Bölüm/Yarıyıl Kısıtları', {
            'fields': ('allowed_departments', 'allowed_years'),
            'classes': ('collapse',)
        }),
        ('Özel Mesaj', {
            'fields': ('error_message',)
        })
    )
    
    def rule_type_badge(self, obj):
        """Display rule type with badge"""
        colors = {
            'prerequisite': '#ff6b6b',
            'corequisite': '#ffd43b',
            'department': '#51cf66',
            'year': '#339af0',
            'grade': '#845ef7'
        }
        color = colors.get(obj.rule_type, '#868e96')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_rule_type_display()
        )
    rule_type_badge.short_description = 'Kural Tipi'
    
    def is_active_badge(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Aktif</span>')
        return format_html('<span style="color: #ccc;">○ Pasif</span>')
    is_active_badge.short_description = 'Aktif'
    
    def rule_details(self, obj):
        """Display rule details"""
        if obj.rule_type == 'prerequisite' and obj.prerequisite_course:
            grade_text = f' (min: {obj.min_grade})' if obj.min_grade else ''
            return f'{obj.prerequisite_course.code}{grade_text}'
        elif obj.rule_type == 'department':
            return obj.allowed_departments or '-'
        elif obj.rule_type == 'year':
            return obj.allowed_years or '-'
        return '-'
    rule_details.short_description = 'Detay'
