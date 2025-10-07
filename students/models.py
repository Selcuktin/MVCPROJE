from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Erkek'),
        ('F', 'Kadın'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('graduated', 'Mezun'),
        ('suspended', 'Askıda'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school_number = models.CharField(
        max_length=20, 
        unique=True,
        validators=[RegexValidator(r'^\d{4,20}$', 'Okul numarası 4-20 haneli olmalıdır')]
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Geçerli telefon numarası giriniz')]
    )
    birth_date = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField()
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Öğrenci'
        verbose_name_plural = 'Öğrenciler'
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"