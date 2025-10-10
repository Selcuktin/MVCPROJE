"""
Teacher related models
"""
from django.db import models
from apps.users.models import User

class Teacher(models.Model):
    GENDER_CHOICES = [
        ('M', 'Erkek'),
        ('F', 'Kadın'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('retired', 'Emekli'),
        ('suspended', 'Askıda'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tc_no = models.CharField(max_length=11, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    title = models.CharField(max_length=100, help_text='Ör: Prof. Dr., Doç. Dr., Dr.')
    department = models.CharField(max_length=100)
    hire_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Öğretmen'
        verbose_name_plural = 'Öğretmenler'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.title} {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.title} {self.first_name} {self.last_name}"