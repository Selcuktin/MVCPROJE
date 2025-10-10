"""
Utility models for logging and history tracking
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ActivityLog(models.Model):
    """Track user activities and changes"""
    
    ACTION_CHOICES = [
        ('create', 'Oluşturma'),
        ('update', 'Güncelleme'),
        ('delete', 'Silme'),
        ('login', 'Giriş'),
        ('logout', 'Çıkış'),
        ('view', 'Görüntüleme'),
        ('export', 'Dışa Aktarma'),
        ('enroll', 'Kayıt'),
        ('submit', 'Teslim'),
        ('grade', 'Notlandırma'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='activity_logs',
        verbose_name='Kullanıcı'
    )
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        verbose_name='İşlem'
    )
    model_name = models.CharField(
        max_length=50,
        verbose_name='Model Adı',
        help_text='Etkilenen model adı (örn: Student, Course)'
    )
    object_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Nesne ID'
    )
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nesne Gösterimi'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Açıklama'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Adresi'
    )
    user_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Tarayıcı Bilgisi'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Zaman'
    )
    
    class Meta:
        verbose_name = 'Aktivite Logu'
        verbose_name_plural = 'Aktivite Logları'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Anonim'
        return f"{user_str} - {self.get_action_display()} - {self.model_name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def log_activity(cls, user, action, model_name, object_id=None, object_repr='', 
                     description='', request=None):
        """Helper method to create activity log"""
        ip_address = None
        user_agent = ''
        
        if request:
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )


class ChangeHistory(models.Model):
    """Track field-level changes in models"""
    
    activity_log = models.ForeignKey(
        ActivityLog,
        on_delete=models.CASCADE,
        related_name='changes',
        verbose_name='Aktivite Logu'
    )
    field_name = models.CharField(
        max_length=100,
        verbose_name='Alan Adı'
    )
    old_value = models.TextField(
        blank=True,
        verbose_name='Eski Değer'
    )
    new_value = models.TextField(
        blank=True,
        verbose_name='Yeni Değer'
    )
    
    class Meta:
        verbose_name = 'Değişiklik Geçmişi'
        verbose_name_plural = 'Değişiklik Geçmişleri'
    
    def __str__(self):
        return f"{self.field_name}: {self.old_value} → {self.new_value}"

