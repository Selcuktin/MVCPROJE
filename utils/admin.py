"""
Utils Admin - Sistem Logları ve Duyurular (Admin Görevi)
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ActivityLog, ChangeHistory, SystemAnnouncement


@admin.register(SystemAnnouncement)
class SystemAnnouncementAdmin(admin.ModelAdmin):
    """Sistem Duyuruları - Admin İşlevi"""
    
    list_display = [
        'title',
        'oncelik_badge',
        'hedef_kitle',
        'durum_badge',
        'start_date',
        'end_date',
        'created_by',
    ]
    
    list_filter = ['priority', 'target_audience', 'status', 'start_date']
    
    search_fields = ['title', 'content']
    
    actions = ['duyurulari_aktif_et', 'duyurulari_arsivle']
    
    fieldsets = (
        ('Duyuru Bilgileri', {
            'fields': ('title', 'content', 'priority', 'target_audience')
        }),
        ('Tarih ve Durum', {
            'fields': ('start_date', 'end_date', 'status'),
            'description': 'Duyurunun gösterileceği tarih aralığı'
        }),
    )
    
    readonly_fields = []
    
    def save_model(self, request, obj, form, change):
        """Oluşturan kullanıcıyı otomatik ata"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def oncelik_badge(self, obj):
        """Öncelik badge'i"""
        colors = {
            'low': '#868e96',
            'normal': '#339af0',
            'high': '#ffa94d',
            'urgent': '#ff6b6b'
        }
        icons = {
            'low': '⬇️',
            'normal': '➡️',
            'high': '⬆️',
            'urgent': '🔴'
        }
        color = colors.get(obj.priority, '#868e96')
        icon = icons.get(obj.priority, '➡️')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            color,
            icon,
            obj.get_priority_display()
        )
    oncelik_badge.short_description = 'Öncelik'
    
    def hedef_kitle(self, obj):
        """Hedef kitle"""
        icons = {
            'all': '👥',
            'students': '👨‍🎓',
            'teachers': '👨‍🏫',
            'admins': '👤'
        }
        icon = icons.get(obj.target_audience, '👥')
        return f"{icon} {obj.get_target_audience_display()}"
    hedef_kitle.short_description = 'Hedef Kitle'
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'draft': '#868e96',
            'active': '#51cf66',
            'expired': '#ffa94d',
            'archived': '#adb5bd'
        }
        color = colors.get(obj.status, '#868e96')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    durum_badge.short_description = 'Durum'
    
    def duyurulari_aktif_et(self, request, queryset):
        """Duyuruları aktif et"""
        count = queryset.update(status='active')
        self.message_user(request, f'{count} duyuru aktif edildi')
    duyurulari_aktif_et.short_description = '✓ Seçilenleri aktif et'
    
    def duyurulari_arsivle(self, request, queryset):
        """Duyuruları arşivle"""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} duyuru arşivlendi')
    duyurulari_arsivle.short_description = '📦 Seçilenleri arşivle'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Aktivite Logları - Sistem İzleme"""
    
    list_display = [
        'timestamp',
        'user',
        'action',
        'model_name',
        'object_repr',
        'ip_address',
    ]
    
    list_filter = ['action', 'model_name', 'timestamp']
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'object_repr',
        'ip_address',
    ]
    
    readonly_fields = [
        'timestamp',
        'user',
        'action',
        'model_name',
        'object_id',
        'object_repr',
        'ip_address',
        'user_agent',
    ]
    
    def has_add_permission(self, request):
        """Loglar eklenemez"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Loglar düzenlenemez"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Loglar silinemez"""
        return False


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    """Değişiklik Geçmişi - Detaylı İzleme"""
    
    list_display = [
        'activity_log',
        'field_name',
        'old_value_short',
        'new_value_short',
    ]
    
    list_filter = ['activity_log__model_name', 'field_name']
    
    search_fields = [
        'activity_log__user__username',
        'field_name',
        'old_value',
        'new_value',
    ]
    
    readonly_fields = [
        'activity_log',
        'field_name',
        'old_value',
        'new_value',
    ]
    
    def old_value_short(self, obj):
        """Eski değer (kısa)"""
        if obj.old_value and len(obj.old_value) > 50:
            return obj.old_value[:50] + "..."
        return obj.old_value or "-"
    old_value_short.short_description = 'Eski Değer'
    
    def new_value_short(self, obj):
        """Yeni değer (kısa)"""
        if obj.new_value and len(obj.new_value) > 50:
            return obj.new_value[:50] + "..."
        return obj.new_value or "-"
    new_value_short.short_description = 'Yeni Değer'
    
    def has_add_permission(self, request):
        """Değişiklik kayıtları eklenemez"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Değişiklik kayıtları düzenlenemez"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Değişiklik kayıtları silinemez"""
        return False
