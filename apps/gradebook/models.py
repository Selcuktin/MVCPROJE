"""
Gradebook Models
Advanced grade management system
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from apps.courses.models import CourseGroup, Enrollment
from apps.students.models import Student


class GradeCategory(models.Model):
    """
    Grade categories for course assessments
    Examples: Midterm, Final, Quiz, Project, Homework
    """
    CATEGORY_TYPE_CHOICES = [
        ('exam', 'Sınav'),
        ('quiz', 'Quiz'),
        ('homework', 'Ödev'),
        ('project', 'Proje'),
        ('lab', 'Laboratuvar'),
        ('attendance', 'Devam'),
        ('participation', 'Katılım'),
        ('other', 'Diğer'),
    ]
    
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='grade_categories'
    )
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=CATEGORY_TYPE_CHOICES,
        default='other'
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Yüzdelik ağırlık (toplam 100 olmalı)'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Not Kategorisi'
        verbose_name_plural = 'Not Kategorileri'
        ordering = ['-weight', 'name']
        unique_together = ['course_group', 'name']
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.name} ({self.weight}%)"
    
    def clean(self):
        """Validate total weight doesn't exceed 100%"""
        if self.course_group_id:
            total_weight = GradeCategory.objects.filter(
                course_group=self.course_group,
                is_active=True
            ).exclude(id=self.id).aggregate(
                total=models.Sum('weight')
            )['total'] or Decimal('0')
            
            if total_weight + self.weight > 100:
                raise ValidationError({
                    'weight': f'Toplam ağırlık 100\'ü geçemez. Mevcut: {total_weight}%'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class GradeItem(models.Model):
    """
    Individual grade items (assignments, exams, etc.)
    Replaces the old Note model gradually
    """
    STATUS_CHOICES = [
        ('draft', 'Taslak'),
        ('published', 'Yayınlandı'),
        ('graded', 'Notlandırıldı'),
        ('archived', 'Arşivlendi'),
    ]
    
    category = models.ForeignKey(
        GradeCategory,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(0)]
    )
    weight_in_category = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Kategori içindeki ağırlık %'
    )
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_extra_credit = models.BooleanField(
        default=False,
        help_text='Ek puan mı? (Ortalamayı yükseltir)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Not Kalemi'
        verbose_name_plural = 'Not Kalemleri'
        ordering = ['-due_date', 'name']
    
    def __str__(self):
        return f"{self.category.course_group.course.code} - {self.name}"
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        if self.due_date:
            return timezone.now() > self.due_date
        return False
    
    @property
    def course_group(self):
        """Shortcut to course group"""
        return self.category.course_group
    
    def clean(self):
        """Validation"""
        if self.category_id:
            # Check total weight in category
            total_weight = GradeItem.objects.filter(
                category=self.category,
                is_extra_credit=False
            ).exclude(id=self.id).aggregate(
                total=models.Sum('weight_in_category')
            )['total'] or Decimal('0')
            
            if not self.is_extra_credit and total_weight + self.weight_in_category > 100:
                raise ValidationError({
                    'weight_in_category': f'Kategori içi toplam ağırlık 100\'ü geçemez. Mevcut: {total_weight}%'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Grade(models.Model):
    """
    Individual student grades for grade items
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    item = models.ForeignKey(
        GradeItem,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='item_grades',
        null=True,
        blank=True
    )
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_excused = models.BooleanField(
        default=False,
        help_text='Mazeret (hesaplamaya katılmaz)'
    )
    is_late = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Not'
        verbose_name_plural = 'Notlar'
        unique_together = ['student', 'item']
        ordering = ['-graded_at', '-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.item.name}: {self.score}/{self.item.max_score}"
    
    @property
    def percentage(self):
        """Calculate percentage score"""
        if self.score is not None and self.item.max_score > 0:
            score = Decimal(str(self.score))
            max_score = Decimal(str(self.item.max_score))
            return float((score / max_score) * Decimal('100'))
        return None
    
    @property
    def weighted_score(self):
        """Calculate weighted score in course"""
        if self.score is None or self.is_excused:
            return Decimal('0')
        
        percentage = self.percentage
        if percentage is None:
            return Decimal('0')
        
        # Weight in category * category weight in course
        item_weight = Decimal(str(self.item.weight_in_category)) / Decimal('100')
        category_weight = Decimal(str(self.item.category.weight)) / Decimal('100')
        
        return Decimal(str(percentage)) * item_weight * category_weight
    
    def clean(self):
        """Validation"""
        if self.score is not None and self.item.max_score:
            score = Decimal(str(self.score))
            max_score = Decimal(str(self.item.max_score))
            if score > max_score:
                raise ValidationError({
                    'score': f'Not maksimum puandan ({self.item.max_score}) büyük olamaz'
                })
        
        # Auto-set late flag
        if self.submitted_at and self.item.due_date:
            self.is_late = self.submitted_at > self.item.due_date
    
    def save(self, *args, **kwargs):
        if self.score is not None and not self.graded_at:
            self.graded_at = timezone.now()
        
        self.full_clean()
        super().save(*args, **kwargs)
