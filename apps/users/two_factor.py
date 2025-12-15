"""
Two-Factor Authentication (2FA)
"""
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache
import random
import string


class TwoFactorAuth(models.Model):
    """2FA settings for users"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='two_factor'
    )
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.TextField(blank=True, help_text='Comma-separated backup codes')
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'İki Faktörlü Doğrulama'
        verbose_name_plural = 'İki Faktörlü Doğrulamalar'
    
    def __str__(self):
        return f"{self.user.username} - 2FA: {'Aktif' if self.is_enabled else 'Pasif'}"
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes"""
        codes = []
        for _ in range(count):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            codes.append(code)
        
        self.backup_codes = ','.join(codes)
        self.save()
        return codes
    
    def verify_backup_code(self, code):
        """Verify and use a backup code"""
        if not self.backup_codes:
            return False
        
        codes = self.backup_codes.split(',')
        if code in codes:
            # Remove used code
            codes.remove(code)
            self.backup_codes = ','.join(codes)
            self.last_used = timezone.now()
            self.save()
            return True
        
        return False


class TwoFactorService:
    """Service for 2FA operations"""
    
    @staticmethod
    def send_code_via_email(user, code):
        """Send 2FA code via email"""
        subject = 'Giriş Doğrulama Kodu'
        message = f"""
        Merhaba {user.username},
        
        Giriş doğrulama kodunuz: {code}
        
        Bu kod 5 dakika geçerlidir.
        
        Eğer bu işlemi siz yapmadıysanız, lütfen derhal sistem yöneticisi ile iletişime geçin.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    
    @staticmethod
    def generate_code():
        """Generate 6-digit code"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def send_and_cache_code(user):
        """Generate, send and cache 2FA code"""
        code = TwoFactorService.generate_code()
        
        # Cache code for 5 minutes
        cache_key = f'2fa_code:{user.id}'
        cache.set(cache_key, code, 300)
        
        # Send via email
        TwoFactorService.send_code_via_email(user, code)
        
        return True
    
    @staticmethod
    def verify_code(user, code):
        """Verify 2FA code"""
        cache_key = f'2fa_code:{user.id}'
        cached_code = cache.get(cache_key)
        
        if cached_code and cached_code == code:
            # Delete code after successful verification
            cache.delete(cache_key)
            return True
        
        # Try backup codes
        try:
            two_factor = TwoFactorAuth.objects.get(user=user)
            if two_factor.verify_backup_code(code):
                return True
        except TwoFactorAuth.DoesNotExist:
            pass
        
        return False


# KVKK Compliance (Turkish Data Protection Law)
class DataProtectionConsent(models.Model):
    """KVKK compliance - user consent tracking"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='data_consents'
    )
    consent_type = models.CharField(
        max_length=50,
        choices=[
            ('data_processing', 'Veri İşleme'),
            ('marketing', 'Pazarlama'),
            ('analytics', 'Analitik'),
            ('third_party_sharing', 'Üçüncü Taraf Paylaşım'),
        ]
    )
    is_granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Veri İşleme Onayı'
        verbose_name_plural = 'Veri İşleme Onayları'
        unique_together = ['user', 'consent_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.consent_type}: {'Onaylı' if self.is_granted else 'Reddedildi'}"
    
    def grant(self, ip_address=None, user_agent=''):
        """Grant consent"""
        self.is_granted = True
        self.granted_at = timezone.now()
        self.revoked_at = None
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.save()
    
    def revoke(self):
        """Revoke consent"""
        self.is_granted = False
        self.revoked_at = timezone.now()
        self.save()
