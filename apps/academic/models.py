"""
Academic Term Models
Dönem bazlı akademik takvim yönetimi (Selçuk/Moodle benzeri)
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class AcademicTerm(models.Model):
    """
    Akademik Dönem Modeli
    Örnek: 2024-2025 Güz, 2024-2025 Bahar, 2024-2025 Yaz
    """
    TERM_TYPE_CHOICES = [
        ('fall', 'Güz'),
        ('spring', 'Bahar'),
        ('summer', 'Yaz'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planlandı'),
        ('active', 'Aktif'),
        ('completed', 'Tamamlandı'),
        ('archived', 'Arşivlendi'),
    ]
    
    # Dönem bilgileri
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Örnek: 2024-2025 Güz"
    )
    year_start = models.IntegerField(
        help_text="Başlangıç yılı (örn: 2024)"
    )
    year_end = models.IntegerField(
        help_text="Bitiş yılı (örn: 2025)"
    )
    term_type = models.CharField(
        max_length=10,
        choices=TERM_TYPE_CHOICES,
        help_text="Dönem tipi"
    )
    
    # Tarihler
    start_date = models.DateField(
        help_text="Dönem başlangıç tarihi"
    )
    end_date = models.DateField(
        help_text="Dönem bitiş tarihi"
    )
    
    # Kayıt dönemi
    registration_start = models.DateField(
        null=True,
        blank=True,
        help_text="Ders kaydı başlangıç tarihi"
    )
    registration_end = models.DateField(
        null=True,
        blank=True,
        help_text="Ders kaydı bitiş tarihi"
    )
    
    # Durum
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Aktif dönem (aynı anda sadece 1 dönem aktif olabilir)"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Dönem hakkında notlar"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Akademik Dönem'
        verbose_name_plural = 'Akademik Dönemler'
        ordering = ['-year_start', '-term_type']
        unique_together = ['year_start', 'year_end', 'term_type']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate academic term data"""
        # Check date logic
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError({
                    'end_date': 'Bitiş tarihi başlangıç tarihinden sonra olmalı'
                })
        
        # Check registration dates
        if self.registration_start and self.registration_end:
            if self.registration_start >= self.registration_end:
                raise ValidationError({
                    'registration_end': 'Kayıt bitiş tarihi başlangıcından sonra olmalı'
                })
            
            if self.registration_end > self.end_date:
                raise ValidationError({
                    'registration_end': 'Kayıt bitiş tarihi dönem bitiş tarihinden sonra olamaz'
                })
        
        # Check year logic
        if self.year_start and self.year_end:
            if self.year_end < self.year_start:
                raise ValidationError({
                    'year_end': 'Bitiş yılı başlangıç yılından küçük olamaz'
                })
            
            # Güz/Bahar için year_end = year_start + 1, Yaz için eşit olabilir
            if self.term_type in ['fall', 'spring']:
                if self.year_end != self.year_start + 1:
                    raise ValidationError({
                        'year_end': f'{self.get_term_type_display()} dönemi için bitiş yılı başlangıç yılı + 1 olmalı'
                    })
            elif self.term_type == 'summer':
                if self.year_end != self.year_start:
                    raise ValidationError({
                        'year_end': 'Yaz dönemi için bitiş yılı başlangıç yılı ile aynı olmalı'
                    })
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active term"""
        # Auto-generate name if not provided
        if not self.name:
            term_name = self.get_term_type_display()
            if self.term_type == 'summer':
                self.name = f"{self.year_start} {term_name}"
            else:
                self.name = f"{self.year_start}-{self.year_end} {term_name}"
        
        # If this term is being set as active, deactivate others
        if self.is_active:
            AcademicTerm.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_registration_open(self):
        """Check if registration period is currently open"""
        if not self.registration_start or not self.registration_end:
            return False
        
        today = timezone.now().date()
        return self.registration_start <= today <= self.registration_end
    
    @property
    def is_current(self):
        """Check if term is currently running"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in term"""
        if not self.is_current:
            return 0
        
        today = timezone.now().date()
        delta = self.end_date - today
        return delta.days
    
    @classmethod
    def get_active_term(cls):
        """Get the currently active academic term"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None
        except cls.MultipleObjectsReturned:
            # Failsafe: if multiple active terms exist, return the most recent one
            return cls.objects.filter(is_active=True).order_by('-start_date').first()
    
    @classmethod
    def get_current_term(cls):
        """Get the term that is currently running (by date)"""
        today = timezone.now().date()
        return cls.objects.filter(
            start_date__lte=today,
            end_date__gte=today
        ).first()
    
    def activate(self):
        """Set this term as the active term"""
        # Deactivate all other terms
        AcademicTerm.objects.filter(is_active=True).update(is_active=False)
        
        # Activate this term
        self.is_active = True
        self.status = 'active'
        self.save()
    
    def complete(self):
        """Mark term as completed"""
        self.status = 'completed'
        self.is_active = False
        self.save()
    
    def archive(self):
        """Archive the term"""
        self.status = 'archived'
        self.is_active = False
        self.save()
