"""
DOSYA: apps/users/models.py
AMAÇ: Kullanıcı ve profil modelleri - Authentication sistemi
KULLANIM:
- User: Django'nun AbstractUser'ından türetilmiş custom user model
- UserProfile: Kullanıcı profil bilgileri (rol, telefon, avatar, bio)

ROLLER:
- student: Öğrenci
- teacher: Öğretmen  
- admin: Yönetici

AUTH TİPLERİ:
1. Session-based (Web): LOGIN/LOGOUT ile çerezler
2. JWT-based (API): Token ile stateless authentication
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User model extending AbstractUser"""
    pass

class UserProfile(models.Model):
    """Extended user profile"""
    USER_TYPE_CHOICES = [
        ('student', 'Öğrenci'),
        ('teacher', 'Öğretmen'),
        ('admin', 'Yönetici'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kullanıcı Profili'
        verbose_name_plural = 'Kullanıcı Profilleri'
    
    def __str__(self):
        return f"{self.user.get_full_name()} Profile"


class NotificationStatus(models.Model):
    """Track notification read status for users"""
    NOTIFICATION_TYPES = [
        ('assignment', 'Ödev'),
        ('announcement', 'Duyuru'),
        ('grade', 'Not'),
        ('welcome', 'Hoş Geldin'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_statuses')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    notification_id = models.CharField(max_length=100)  # e.g., "assignment_123"
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'notification_id']
        verbose_name = 'Bildirim Durumu'
        verbose_name_plural = 'Bildirim Durumları'
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_id} ({'Okundu' if self.is_read else 'Okunmadı'})"