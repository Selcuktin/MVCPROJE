"""
Academic Term Admin Interface
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import AcademicTerm


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    """Admin interface for Academic Term"""
    
    list_display = [
        'name',
        'term_type_badge',
        'start_date',
        'end_date',
        'status_badge',
        'is_active_badge',
        'registration_status',
        'days_remaining_display'
    ]
    
    list_filter = [
        'status',
        'term_type',
        'is_active',
        'year_start'
    ]
    
    search_fields = [
        'name',
        'description'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'is_current',
        'is_registration_open',
        'days_remaining'
    ]
    
    fieldsets = (
        ('Genel Bilgiler', {
            'fields': ('name', 'year_start', 'year_end', 'term_type', 'description')
        }),
        ('Tarihler', {
            'fields': ('start_date', 'end_date', 'registration_start', 'registration_end')
        }),
        ('Durum', {
            'fields': ('status', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_current', 'is_registration_open', 'days_remaining'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_term', 'complete_term', 'archive_term']
    
    def term_type_badge(self, obj):
        """Display term type with color badge"""
        colors = {
            'fall': '#ff6b6b',
            'spring': '#51cf66',
            'summer': '#ffd43b'
        }
        color = colors.get(obj.term_type, '#868e96')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_term_type_display()
        )
    term_type_badge.short_description = 'Dönem'
    
    def status_badge(self, obj):
        """Display status with color badge"""
        colors = {
            'planned': '#868e96',
            'active': '#51cf66',
            'completed': '#339af0',
            'archived': '#adb5bd'
        }
        color = colors.get(obj.status, '#868e96')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Durum'
    
    def is_active_badge(self, obj):
        """Display active status with icon"""
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 16px;">●</span> Aktif')
        return format_html('<span style="color: #ccc; font-size: 16px;">○</span> Pasif')
    is_active_badge.short_description = 'Aktif Mi?'
    
    def registration_status(self, obj):
        """Display registration status"""
        if obj.is_registration_open:
            return format_html('<span style="color: green;">✓ Açık</span>')
        elif obj.registration_start and obj.registration_end:
            return format_html('<span style="color: #868e96;">✗ Kapalı</span>')
        return format_html('<span style="color: #adb5bd;">-</span>')
    registration_status.short_description = 'Kayıt Durumu'
    
    def days_remaining_display(self, obj):
        """Display days remaining"""
        if obj.is_current:
            days = obj.days_remaining
            if days > 30:
                color = 'green'
            elif days > 7:
                color = 'orange'
            else:
                color = 'red'
            return format_html('<span style="color: {};">{} gün</span>', color, days)
        return '-'
    days_remaining_display.short_description = 'Kalan Gün'
    
    def activate_term(self, request, queryset):
        """Activate selected term"""
        if queryset.count() > 1:
            self.message_user(request, 'Sadece bir dönem seçebilirsiniz', level='error')
            return
        
        term = queryset.first()
        term.activate()
        self.message_user(request, f'{term.name} dönemi aktif edildi')
    activate_term.short_description = 'Seçili dönemi aktif et'
    
    def complete_term(self, request, queryset):
        """Mark selected terms as completed"""
        count = 0
        for term in queryset:
            term.complete()
            count += 1
        self.message_user(request, f'{count} dönem tamamlandı olarak işaretlendi')
    complete_term.short_description = 'Seçili dönemleri tamamla'
    
    def archive_term(self, request, queryset):
        """Archive selected terms"""
        count = 0
        for term in queryset:
            term.archive()
            count += 1
        self.message_user(request, f'{count} dönem arşivlendi')
    archive_term.short_description = 'Seçili dönemleri arşivle'
