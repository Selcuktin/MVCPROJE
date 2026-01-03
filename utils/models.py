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


class SystemAnnouncement(models.Model):
    """Sistem Geneli Duyurular - Admin tarafından yönetilir"""
    
    PRIORITY_CHOICES = [
        ('low', 'Düşük'),
        ('normal', 'Normal'),
        ('high', 'Yüksek'),
        ('urgent', 'Acil'),
    ]
    
    TARGET_AUDIENCE_CHOICES = [
        ('all', 'Tüm Kullanıcılar'),
        ('students', 'Öğrenciler'),
        ('teachers', 'Öğretmenler'),
        ('admins', 'Adminler'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Taslak'),
        ('active', 'Aktif'),
        ('expired', 'Süresi Dolmuş'),
        ('archived', 'Arşivlendi'),
    ]
    
    title = models.CharField(
        max_length=200,
        verbose_name='Başlık'
    )
    content = models.TextField(
        verbose_name='İçerik'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='Öncelik'
    )
    target_audience = models.CharField(
        max_length=20,
        choices=TARGET_AUDIENCE_CHOICES,
        default='all',
        verbose_name='Hedef Kitle'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='Durum'
    )
    start_date = models.DateTimeField(
        verbose_name='Başlangıç Tarihi',
        help_text='Duyurunun gösterilmeye başlanacağı tarih'
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Bitiş Tarihi',
        help_text='Duyurunun gösterilmeyi durduracağı tarih (opsiyonel)'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_announcements',
        verbose_name='Oluşturan'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Oluşturulma Tarihi'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Güncellenme Tarihi'
    )
    
    class Meta:
        verbose_name = 'Sistem Duyurusu'
        verbose_name_plural = 'Sistem Duyuruları'
        ordering = ['-priority', '-start_date']
        indexes = [
            models.Index(fields=['-start_date']),
            models.Index(fields=['status', '-start_date']),
            models.Index(fields=['target_audience', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    def save(self, *args, **kwargs):
        """Auto-update status based on dates"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.status == 'active':
            if now < self.start_date:
                self.status = 'draft'
            elif self.end_date and now > self.end_date:
                self.status = 'expired'
        
        super().save(*args, **kwargs)
    
    def is_visible_for_user(self, user):
        """Check if announcement is visible for given user"""
        from django.utils import timezone
        
        # Status check
        if self.status != 'active':
            return False
        
        # Date check
        now = timezone.now()
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        # Audience check
        if self.target_audience == 'all':
            return True
        elif self.target_audience == 'students' and hasattr(user, 'student'):
            return True
        elif self.target_audience == 'teachers' and hasattr(user, 'teacher'):
            return True
        elif self.target_audience == 'admins' and user.is_staff:
            return True
        
        return False

