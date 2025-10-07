from django.db import models
from django.contrib.auth.models import User
from courses.models import Course

class Note(models.Model):
    GRADE_CHOICES = [
        ('AA', 'AA (90-100)'),
        ('BA', 'BA (85-89)'),
        ('BB', 'BB (80-84)'),
        ('CB', 'CB (75-79)'),
        ('CC', 'CC (70-74)'),
        ('DC', 'DC (65-69)'),
        ('DD', 'DD (60-64)'),
        ('FD', 'FD (50-59)'),
        ('FF', 'FF (0-49)'),
    ]
    
    EXAM_TYPE_CHOICES = [
        ('vize', 'Vize'),
        ('final', 'Final'),
        ('but', 'Bütünleme'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='Ders')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_notes', verbose_name='Öğrenci')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes', verbose_name='Öğretmen')
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES, default='vize', verbose_name='Sınav Türü')
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, verbose_name='Not')
    score = models.IntegerField(verbose_name='Puan (0-100)', help_text='0-100 arası puan giriniz')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')
    
    class Meta:
        verbose_name = 'Not'
        verbose_name_plural = 'Notlar'
        ordering = ['-created_at']
        unique_together = ['course', 'student', 'exam_type']  # Aynı öğrenci, ders ve sınav türü için tek not
    
    def __str__(self):
        return f"{self.course.name} - {self.student.get_full_name()} ({self.get_exam_type_display()}: {self.grade})"
    
    def save(self, *args, **kwargs):
        # Puana göre otomatik harf notu belirleme
        if self.score >= 90:
            self.grade = 'AA'
        elif self.score >= 85:
            self.grade = 'BA'
        elif self.score >= 80:
            self.grade = 'BB'
        elif self.score >= 75:
            self.grade = 'CB'
        elif self.score >= 70:
            self.grade = 'CC'
        elif self.score >= 65:
            self.grade = 'DC'
        elif self.score >= 60:
            self.grade = 'DD'
        elif self.score >= 50:
            self.grade = 'FD'
        else:
            self.grade = 'FF'
        super().save(*args, **kwargs)
