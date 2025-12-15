"""
Enrollment Models
Gelişmiş kayıt sistemi - Moodle/Selçuk benzeri
"""
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings


class EnrollmentMethod(models.Model):
    """
    Kayıt Yöntemi
    Moodle'daki enrollment plugins benzeri sistem
    """
    METHOD_TYPE_CHOICES = [
        ('manual', 'Manuel Kayıt'),      # Admin/Teacher ekler
        ('self', 'Öğrenci Kayıt'),       # Öğrenci kendisi seçer
        ('key', 'Anahtar ile Kayıt'),    # Enrollment key ile kayıt
        ('cohort', 'Toplu Kayıt'),       # Grup bazlı otomatik kayıt
    ]
    
    course_group = models.ForeignKey(
        'courses.CourseGroup',
        on_delete=models.CASCADE,
        related_name='enrollment_methods'
    )
    method_type = models.CharField(
        max_length=20,
        choices=METHOD_TYPE_CHOICES,
        default='manual'
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text='Bu kayıt yöntemi aktif mi?'
    )
    
    # Enrollment key (sadece 'key' tipi için)
    enrollment_key = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Kayıt anahtarı (key tipi için gerekli)'
    )
    
    # Kapasite
    max_students = models.IntegerField(
        null=True,
        blank=True,
        help_text='Maksimum öğrenci sayısı (boş = sınırsız)'
    )
    
    # Self-enrollment için ayarlar
    allow_self_unenroll = models.BooleanField(
        default=True,
        help_text='Öğrenci kendi kayıtını iptal edebilir mi?'
    )
    
    # Tarih kısıtlamaları
    enrollment_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Kayıt başlangıç tarihi'
    )
    enrollment_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Kayıt bitiş tarihi'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_enrollment_methods'
    )
    
    class Meta:
        verbose_name = 'Kayıt Yöntemi'
        verbose_name_plural = 'Kayıt Yöntemleri'
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.get_method_type_display()}"
    
    def clean(self):
        """Validate enrollment method"""
        # Key tipi için enrollment_key zorunlu
        if self.method_type == 'key' and not self.enrollment_key:
            raise ValidationError({
                'enrollment_key': 'Anahtar ile kayıt için enrollment key gerekli'
            })
        
        # Tarih validasyonu
        if self.enrollment_start and self.enrollment_end:
            if self.enrollment_start >= self.enrollment_end:
                raise ValidationError({
                    'enrollment_end': 'Bitiş tarihi başlangıçtan sonra olmalı'
                })
    
    @property
    def is_enrollment_open(self):
        """Check if enrollment is currently open"""
        if not self.is_enabled:
            return False
        
        now = timezone.now()
        
        # Check date restrictions
        if self.enrollment_start and now < self.enrollment_start:
            return False
        
        if self.enrollment_end and now > self.enrollment_end:
            return False
        
        return True
    
    @property
    def current_enrollment_count(self):
        """Get current enrollment count for this method"""
        from apps.courses.models import Enrollment
        return Enrollment.objects.filter(
            group=self.course_group,
            status='enrolled'
        ).count()
    
    @property
    def has_capacity(self):
        """Check if there's available capacity"""
        if not self.max_students:
            return True  # Unlimited
        
        return self.current_enrollment_count < self.max_students
    
    def can_enroll(self, student, key=None):
        """
        Check if student can enroll with this method
        Returns (can_enroll: bool, message: str)
        """
        # Check if method is enabled
        if not self.is_enabled:
            return False, 'Bu kayıt yöntemi aktif değil'
        
        # Check enrollment period
        if not self.is_enrollment_open:
            return False, 'Kayıt dönemi kapalı'
        
        # Check capacity
        if not self.has_capacity:
            return False, 'Kontenjan dolu'
        
        # Check if already enrolled
        from apps.courses.models import Enrollment
        if Enrollment.objects.filter(
            student=student,
            group=self.course_group,
            status='enrolled'
        ).exists():
            return False, 'Bu derse zaten kayıtlısınız'
        
        # Key validation for 'key' type
        if self.method_type == 'key':
            if not key:
                return False, 'Kayıt anahtarı gerekli'
            if key != self.enrollment_key:
                return False, 'Geçersiz kayıt anahtarı'
        
        # Self enrollment is not allowed for 'manual' and 'cohort'
        if self.method_type in ['manual', 'cohort']:
            return False, 'Bu yöntemle kayıt yapamazsınız'
        
        return True, 'Kayıt yapılabilir'


class EnrollmentRule(models.Model):
    """
    Kayıt Kuralları
    Prerequisite, co-requisite, department restrictions vb.
    """
    RULE_TYPE_CHOICES = [
        ('prerequisite', 'Ön Koşul'),
        ('corequisite', 'Eş Koşul'),
        ('department', 'Bölüm Kısıtı'),
        ('year', 'Yarıyıl Kısıtı'),
        ('grade', 'Not Kısıtı'),
    ]
    
    course_group = models.ForeignKey(
        'courses.CourseGroup',
        on_delete=models.CASCADE,
        related_name='enrollment_rules'
    )
    rule_type = models.CharField(
        max_length=20,
        choices=RULE_TYPE_CHOICES
    )
    is_active = models.BooleanField(default=True)
    
    # Prerequisite için
    prerequisite_course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='prerequisite_for'
    )
    min_grade = models.CharField(
        max_length=2,
        blank=True,
        help_text='Minimum geçer not (örn: DD)'
    )
    
    # Department restriction
    allowed_departments = models.TextField(
        blank=True,
        help_text='İzin verilen bölümler (virgülle ayrılmış)'
    )
    
    # Year restriction
    allowed_years = models.CharField(
        max_length=50,
        blank=True,
        help_text='İzin verilen yarıyıllar (örn: 1,2,3)'
    )
    
    # Custom message
    error_message = models.TextField(
        blank=True,
        help_text='Kural ihlalinde gösterilecek özel mesaj'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Kayıt Kuralı'
        verbose_name_plural = 'Kayıt Kuralları'
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.get_rule_type_display()}"
    
    def check_rule(self, student):
        """
        Check if student satisfies this rule
        Returns (passed: bool, message: str)
        """
        if not self.is_active:
            return True, ''
        
        if self.rule_type == 'prerequisite':
            return self._check_prerequisite(student)
        elif self.rule_type == 'department':
            return self._check_department(student)
        elif self.rule_type == 'year':
            return self._check_year(student)
        
        return True, ''
    
    def _check_prerequisite(self, student):
        """Check prerequisite requirement"""
        if not self.prerequisite_course:
            return True, ''
        
        from apps.courses.models import Enrollment
        
        # Check if student has taken and passed the prerequisite
        prereq_enrollment = Enrollment.objects.filter(
            student=student,
            group__course=self.prerequisite_course,
            status__in=['completed', 'enrolled']
        ).first()
        
        if not prereq_enrollment:
            msg = self.error_message or f'{self.prerequisite_course.code} dersini almış olmalısınız'
            return False, msg
        
        # Check minimum grade if specified
        if self.min_grade and prereq_enrollment.grade:
            grade_map = {
                'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
                'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FD': 0.5, 'FF': 0.0
            }
            
            student_grade = grade_map.get(prereq_enrollment.grade, 0)
            min_grade_value = grade_map.get(self.min_grade, 0)
            
            if student_grade < min_grade_value:
                msg = self.error_message or f'{self.prerequisite_course.code} dersinden en az {self.min_grade} almanız gerekli'
                return False, msg
        
        return True, ''
    
    def _check_department(self, student):
        """Check department restriction"""
        if not self.allowed_departments:
            return True, ''
        
        allowed = [d.strip() for d in self.allowed_departments.split(',')]
        
        if student.department not in allowed:
            msg = self.error_message or 'Bu ders sizin bölümünüze kapalı'
            return False, msg
        
        return True, ''
    
    def _check_year(self, student):
        """Check year restriction"""
        if not self.allowed_years:
            return True, ''
        
        allowed = [y.strip() for y in self.allowed_years.split(',')]
        
        if str(student.current_year) not in allowed:
            msg = self.error_message or f'Bu ders sadece {self.allowed_years}. yarıyıl öğrencilerine açık'
            return False, msg
        
        return True, ''
