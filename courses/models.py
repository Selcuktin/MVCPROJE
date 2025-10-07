from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from students.models import Student
from teachers.models import Teacher

class Course(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('archived', 'Arşivlenmiş'),
    ]
    
    SEMESTER_CHOICES = [
        ('fall', 'Güz'),
        ('spring', 'Bahar'),
        ('summer', 'Yaz'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    description = models.TextField()
    department = models.CharField(max_length=100)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    capacity = models.IntegerField(validators=[MinValueValidator(1)])
    is_elective = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Ders'
        verbose_name_plural = 'Dersler'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class CourseGroup(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('completed', 'Tamamlandı'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='course_groups')
    semester = models.CharField(max_length=20)
    classroom = models.CharField(max_length=50)
    schedule = models.CharField(max_length=200, help_text='Ör: Pazartesi 09:00-12:00')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Ders Grubu'
        verbose_name_plural = 'Ders Grupları'
        unique_together = ['course', 'teacher', 'semester']
    
    def __str__(self):
        return f"{self.course.code} - {self.teacher.full_name} ({self.semester})"

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('enrolled', 'Kayıtlı'),
        ('dropped', 'Bıraktı'),
        ('completed', 'Tamamladı'),
        ('failed', 'Başarısız'),
    ]
    
    GRADE_CHOICES = [
        ('AA', 'AA'),
        ('BA', 'BA'),
        ('BB', 'BB'),
        ('CB', 'CB'),
        ('CC', 'CC'),
        ('DC', 'DC'),
        ('DD', 'DD'),
        ('FF', 'FF'),
        ('NA', 'Henüz Değerlendirilmedi'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    attendance = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Numerical grades
    midterm_grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Vize Notu')
    final_grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Final Notu')
    makeup_grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Büt Notu')
    project_grade = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name='Proje Notu')
    
    # Letter grade (calculated from numerical grades)
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES, default='NA')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='enrolled')
    
    class Meta:
        verbose_name = 'Kayıt'
        verbose_name_plural = 'Kayıtlar'
        unique_together = ['student', 'group']
    
    def calculate_letter_grade(self):
        """Calculate letter grade based on numerical grades"""
        if not self.final_grade:
            return 'NA'
        
        # Use makeup grade if it exists and is higher than final
        final_score = self.final_grade
        if self.makeup_grade and self.makeup_grade > final_score:
            final_score = self.makeup_grade
        
        # Calculate average (40% midterm, 60% final/makeup)
        if self.midterm_grade:
            average = (self.midterm_grade * 0.4) + (final_score * 0.6)
        else:
            average = final_score
        
        # Add project grade if exists (10% bonus)
        if self.project_grade:
            average = min(100, average + (self.project_grade * 0.1))
        
        # Convert to letter grade
        if average >= 90:
            return 'AA'
        elif average >= 85:
            return 'BA'
        elif average >= 80:
            return 'BB'
        elif average >= 75:
            return 'CB'
        elif average >= 70:
            return 'CC'
        elif average >= 65:
            return 'DC'
        elif average >= 60:
            return 'DD'
        else:
            return 'FF'
    
    def save(self, *args, **kwargs):
        # Auto-calculate letter grade
        self.grade = self.calculate_letter_grade()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.group.course.name}"

class Assignment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('expired', 'Süresi Dolmuş'),
    ]
    
    group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    file_url = models.FileField(upload_to='assignments/', blank=True, null=True)
    create_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    max_score = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Ödev'
        verbose_name_plural = 'Ödevler'
        ordering = ['-create_date']
    
    def __str__(self):
        return f"{self.group.course.code} - {self.title}"

class Submission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Teslim Edildi'),
        ('graded', 'Notlandırıldı'),
        ('late', 'Geç Teslim'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    submission_date = models.DateTimeField(auto_now_add=True)
    file_url = models.FileField(upload_to='submissions/')
    score = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    class Meta:
        verbose_name = 'Teslim'
        verbose_name_plural = 'Teslimler'
        unique_together = ['assignment', 'student']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"

class Announcement(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('inactive', 'Pasif'),
        ('expired', 'Süresi Dolmuş'),
    ]
    
    group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='announcements')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True)
    expire_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Duyuru'
        verbose_name_plural = 'Duyurular'
        ordering = ['-create_date']
    
    def __str__(self):
        return f"{self.group.course.code} - {self.title}"