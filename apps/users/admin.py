"""
Users Admin - Kullanıcı Yönetimi (Admin Görevleri)
Admin: Kullanıcı ekler, düzenler, rol atar, şifre sıfırlar
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import User, UserProfile


class CustomUserChangeForm(UserChangeForm):
    """Özel kullanıcı düzenleme formu"""
    class Meta:
        model = User
        fields = '__all__'


class CustomUserCreationForm(UserCreationForm):
    """Özel kullanıcı oluşturma formu"""
    class Meta:
        model = User
        fields = ('username', 'email')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Kullanıcı Yönetimi - Admin İşlevi"""
    
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    list_display = [
        'username',
        'email',
        'tam_ad',
        'kullanici_tipi',
        'durum_badge',
        'kayit_tarihi',
    ]
    
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined']
    
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    actions = ['kullanicilari_aktif_et', 'kullanicilari_pasif_et', 'sifre_sifirlama_emaili_gonder']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('username', 'password', 'email')
        }),
        ('Kişisel Bilgiler', {
            'fields': ('first_name', 'last_name')
        }),
        ('Durum ve Rol', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'description': 'is_active: Hesap aktif mi? | is_staff: Admin paneline erişim | is_superuser: Tam yetki'
        }),
        ('Önemli Tarihler', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Yeni Kullanıcı Oluştur', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
        ('Rol Seçimi', {
            'classes': ('wide',),
            'fields': ('is_staff', 'is_superuser'),
            'description': 'is_staff: Admin paneline erişim | is_superuser: Tam yetki'
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined']
    
    def tam_ad(self, obj):
        """Tam ad"""
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else "-"
    tam_ad.short_description = 'Ad Soyad'
    
    def kullanici_tipi(self, obj):
        """Kullanıcı tipi"""
        if obj.is_superuser:
            return "🔴 Süper Admin"
        elif obj.is_staff:
            return "🟡 Admin"
        elif hasattr(obj, 'teacher'):
            return "👨‍🏫 Öğretmen"
        elif hasattr(obj, 'student'):
            return "👨‍🎓 Öğrenci"
        else:
            return "👤 Kullanıcı"
    kullanici_tipi.short_description = 'Rol'
    
    def durum_badge(self, obj):
        """Durum badge'i"""
        if obj.is_active:
            return format_html(
                '<span style="background: #51cf66; color: white; padding: 3px 10px; border-radius: 3px;">✓ Aktif</span>'
            )
        else:
            return format_html(
                '<span style="background: #ff6b6b; color: white; padding: 3px 10px; border-radius: 3px;">✗ Pasif</span>'
            )
    durum_badge.short_description = 'Durum'
    
    def kayit_tarihi(self, obj):
        """Kayıt tarihi"""
        return obj.date_joined.strftime('%d.%m.%Y %H:%M')
    kayit_tarihi.short_description = 'Kayıt Tarihi'
    
    def kullanicilari_aktif_et(self, request, queryset):
        """Kullanıcıları aktif et"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'{count} kullanıcı aktif edildi')
    kullanicilari_aktif_et.short_description = '✓ Seçilenleri aktif et'
    
    def kullanicilari_pasif_et(self, request, queryset):
        """Kullanıcıları pasif et"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} kullanıcı pasif edildi')
    kullanicilari_pasif_et.short_description = '✗ Seçilenleri pasif et'
    
    def sifre_sifirlama_emaili_gonder(self, request, queryset):
        """Şifre sıfırlama emaili gönder"""
        # TODO: Email gönderme işlemi eklenecek
        count = queryset.count()
        self.message_user(request, f'{count} kullanıcıya şifre sıfırlama emaili gönderildi (TODO)')
    sifre_sifirlama_emaili_gonder.short_description = '📧 Şifre sıfırlama emaili gönder'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Kullanıcı Profili Yönetimi"""
    
    list_display = ['user', 'user_type', 'phone', 'created_at']
    list_filter = ['user_type']
    search_fields = ['user__username', 'user__email', 'phone']
    
    fieldsets = (
        ('Kullanıcı', {
            'fields': ('user',)
        }),
        ('Profil Bilgileri', {
            'fields': ('user_type', 'phone', 'bio', 'avatar')
        }),
    )
