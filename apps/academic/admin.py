"""
Academic Admin - Akademik Dönem Yönetimi (Admin Görevi)
Admin: Dönem oluşturur, aktif dönem belirler, kayıt dönemlerini yönetir
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import AcademicTerm


@admin.register(AcademicTerm)
class AcademicTermAdmin(admin.ModelAdmin):
    """Akademik Dönem Yönetimi - Admin İşlevi"""
    
    list_display = [
        'name',
        'donem_tipi',
        'tarih_araligi',
        'kayit_durumu',
        'durum_badge',
        'aktif_badge',
    ]
    
    list_filter = ['term_type', 'status', 'is_active', 'year_start']
    
    search_fields = ['name', 'description']
    
    actions = ['donemi_aktif_et', 'donemi_tamamla', 'donemi_arsivle']
    
    fieldsets = (
        ('Dönem Bilgileri', {
            'fields': ('name', 'year_start', 'year_end', 'term_type', 'description')
        }),
        ('Tarihler', {
            'fields': ('start_date', 'end_date', 'registration_start', 'registration_end'),
            'description': 'Dönem ve kayıt tarihleri'
        }),
        ('Durum', {
            'fields': ('status', 'is_active'),
            'description': 'is_active: Aynı anda sadece 1 dönem aktif olabilir'
        }),
    )
    
    readonly_fields = []
    
    def donem_tipi(self, obj):
        """Dönem tipi"""
        icons = {
            'fall': '🍂',
            'spring': '🌸',
            'summer': '☀️'
        }
        icon = icons.get(obj.term_type, '📅')
        return f"{icon} {obj.get_term_type_display()}"
    donem_tipi.short_description = 'Dönem'
    
    def tarih_araligi(self, obj):
        """Tarih aralığı"""
        start = obj.start_date.strftime('%d.%m.%Y')
        end = obj.end_date.strftime('%d.%m.%Y')
        
        # Kalan gün hesapla
        if obj.is_current:
            days = obj.days_remaining
            return format_html(
                '{} - {}<br><span style="color: #51cf66; font-size: 0.85em;">⏱️ {} gün kaldı</span>',
                start, end, days
            )
        return f"{start} - {end}"
    tarih_araligi.short_description = 'Tarih Aralığı'
    
    def kayit_durumu(self, obj):
        """Kayıt durumu"""
        if not obj.registration_start or not obj.registration_end:
            return format_html('<span style="color: #868e96;">Kayıt dönemi yok</span>')
        
        if obj.is_registration_open:
            return format_html(
                '<span style="background: #51cf66; color: white; padding: 3px 8px; border-radius: 3px;">✓ Kayıt Açık</span>'
            )
        else:
            today = timezone.now().date()
            if today < obj.registration_start:
                return format_html('<span style="color: #ffa94d;">Kayıt henüz başlamadı</span>')
            else:
                return format_html('<span style="color: #868e96;">Kayıt kapandı</span>')
    kayit_durumu.short_description = 'Kayıt Durumu'
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'planned': '#868e96',
            'active': '#51cf66',
            'completed': '#339af0',
            'archived': '#adb5bd'
        }
        icons = {
            'planned': '📋',
            'active': '✓',
            'completed': '✔️',
            'archived': '📦'
        }
        color = colors.get(obj.status, '#868e96')
        icon = icons.get(obj.status, '📋')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    durum_badge.short_description = 'Durum'
    
    def aktif_badge(self, obj):
        """Aktif badge'i"""
        if obj.is_active:
            return format_html(
                '<span style="background: #7c4dff; color: white; padding: 3px 10px; border-radius: 3px;">⭐ AKTİF DÖNEM</span>'
            )
        return format_html('<span style="color: #868e96;">-</span>')
    aktif_badge.short_description = 'Aktif Mi?'
    
    def donemi_aktif_et(self, request, queryset):
        """Dönemi aktif et"""
        if queryset.count() > 1:
            self.message_user(request, 'Aynı anda sadece 1 dönem aktif edilebilir', level='error')
            return
        
        term = queryset.first()
        term.activate()
        self.message_user(request, f'{term.name} dönemi aktif edildi')
    donemi_aktif_et.short_description = '⭐ Seçileni aktif dönem yap'
    
    def donemi_tamamla(self, request, queryset):
        """Dönemi tamamla"""
        count = 0
        for term in queryset:
            term.complete()
            count += 1
        self.message_user(request, f'{count} dönem tamamlandı olarak işaretlendi')
    donemi_tamamla.short_description = '✔️ Seçilenleri tamamla'
    
    def donemi_arsivle(self, request, queryset):
        """Dönemi arşivle"""
        count = 0
        for term in queryset:
            term.archive()
            count += 1
        self.message_user(request, f'{count} dönem arşivlendi')
    donemi_arsivle.short_description = '📦 Seçilenleri arşivle'
    
    def get_readonly_fields(self, request, obj=None):
        """Aktif dönem için bazı alanları readonly yap"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_active:
            readonly.extend(['year_start', 'year_end', 'term_type'])
        return readonly
