"""
Gradebook Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import GradeCategory, GradeItem, Grade


@admin.register(GradeCategory)
class GradeCategoryAdmin(admin.ModelAdmin):
    """Admin for GradeCategory"""
    list_display = ['name', 'course_group', 'category_type_badge', 'weight_display', 'is_active', 'items_count']
    list_filter = ['category_type', 'is_active', 'course_group__course']
    search_fields = ['name', 'course_group__course__name', 'course_group__course__code']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Temel Bilgiler', {
            'fields': ['course_group', 'name', 'category_type']
        }),
        ('Ağırlık', {
            'fields': ['weight', 'description']
        }),
        ('Durum', {
            'fields': ['is_active', 'created_at']
        }),
    ]
    
    def category_type_badge(self, obj):
        colors = {
            'exam': 'danger',
            'quiz': 'warning',
            'homework': 'info',
            'project': 'primary',
            'lab': 'success',
            'attendance': 'secondary',
            'participation': 'dark',
            'other': 'light'
        }
        color = colors.get(obj.category_type, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_category_type_display()
        )
    category_type_badge.short_description = 'Tip'
    
    def weight_display(self, obj):
        if obj.weight >= 50:
            color = 'danger'
        elif obj.weight >= 30:
            color = 'warning'
        else:
            color = 'info'
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            f'{obj.weight}%'
        )
    weight_display.short_description = 'Ağırlık'
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Kalem Sayısı'


@admin.register(GradeItem)
class GradeItemAdmin(admin.ModelAdmin):
    """Admin for GradeItem"""
    list_display = ['name', 'category', 'max_score', 'weight_in_category', 'status_badge', 'due_date', 'is_extra_credit']
    list_filter = ['status', 'is_extra_credit', 'category__category_type', 'category__course_group']
    search_fields = ['name', 'description', 'category__name', 'category__course_group__course__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'due_date'
    
    fieldsets = [
        ('Temel Bilgiler', {
            'fields': ['category', 'name', 'description']
        }),
        ('Puanlama', {
            'fields': ['max_score', 'weight_in_category', 'is_extra_credit']
        }),
        ('Tarih & Durum', {
            'fields': ['due_date', 'status']
        }),
        ('Sistem', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def status_badge(self, obj):
        colors = {
            'draft': 'secondary',
            'published': 'primary',
            'graded': 'success',
            'archived': 'dark'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Durum'


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin for Grade"""
    list_display = ['student', 'item', 'score_display', 'percentage_display', 'is_late', 'is_excused', 'graded_at']
    list_filter = ['is_late', 'is_excused', 'item__category__category_type', 'graded_at']
    search_fields = ['student__first_name', 'student__last_name', 'student__school_number', 'item__name']
    readonly_fields = ['created_at', 'updated_at', 'percentage', 'weighted_score']
    date_hierarchy = 'graded_at'
    
    fieldsets = [
        ('Öğrenci & Kalem', {
            'fields': ['student', 'item', 'enrollment']
        }),
        ('Not', {
            'fields': ['score', 'percentage', 'weighted_score', 'feedback']
        }),
        ('Durum', {
            'fields': ['is_excused', 'is_late', 'submitted_at', 'graded_at']
        }),
        ('Sistem', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def score_display(self, obj):
        if obj.score is None:
            return format_html('<span class="text-muted">-</span>')
        
        percentage = obj.percentage
        if percentage is not None:
            if percentage >= 90:
                color = 'success'
            elif percentage >= 70:
                color = 'primary'
            elif percentage >= 50:
                color = 'warning'
            else:
                color = 'danger'
        else:
            color = 'secondary'
        
        return format_html(
            '<span class="badge bg-{}">{} / {}</span>',
            color,
            obj.score,
            obj.item.max_score
        )
    score_display.short_description = 'Puan'
    
    def percentage_display(self, obj):
        percentage = obj.percentage
        if percentage is None:
            return '-'
        return f'{percentage:.1f}%'
    percentage_display.short_description = 'Yüzde'
