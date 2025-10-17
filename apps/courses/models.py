"""
DOSYA: apps/courses/models.py
AMAÇ: Ders yönetim sistemi veritabanı modelleri
KULLANIM: 
- Course: Ders tanımları (kod, isim, kredi, kapasite)
- CourseGroup: Ders grupları (öğretmen ataması, sınıf, program)
- Enrollment: Öğrenci-ders kayıtları (notlar, devam, durum)
- Assignment: Ödevler (teslim tarihi, puan)
- Submission: Ödev teslimleri (dosya, puan, geri bildirim)
- Announcement: Duyurular (başlık, içerik, son kullanma)
- CourseContent: Ders materyalleri (hafta bazlı dökümanlar)

İLİŞKİLER:
- Course → CourseGroup (1-N)
- CourseGroup → Enrollment (1-N)
- CourseGroup → Assignment (1-N)
- Student → Enrollment (1-N)
- Student → Submission (1-N)
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

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
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='course_groups')
    name = models.CharField(max_length=50, default='A')
    semester = models.CharField(max_length=20)
    classroom = models.CharField(max_length=50)
    schedule = models.CharField(max_length=200, help_text='Ör: Pazartesi 09:00-12:00')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Ders Grubu'
        verbose_name_plural = 'Ders Grupları'
        unique_together = ['course', 'teacher', 'semester']
    
    def __str__(self):
        return f"{self.course.code} - {self.name} ({self.semester})"

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
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='enrollments')
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
    
    @property
    def is_expired(self):
        """Check if assignment is expired"""
        from django.utils import timezone
        return timezone.now() > self.due_date
    
    @property
    def time_remaining(self):
        """Get time remaining until due date"""
        from django.utils import timezone
        if self.is_expired:
            return None
        
        time_diff = self.due_date - timezone.now()
        days = time_diff.days
        hours = time_diff.seconds // 3600
        minutes = (time_diff.seconds % 3600) // 60
        
        return {
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'total_seconds': time_diff.total_seconds()
        }
    
    @property
    def urgency_level(self):
        """Get urgency level of assignment"""
        if self.is_expired:
            return 'expired'
        
        remaining = self.time_remaining
        if remaining:
            total_hours = remaining['total_seconds'] / 3600
            if total_hours <= 6:
                return 'urgent'
            elif total_hours <= 24:
                return 'warning'
            else:
                return 'safe'
        return 'expired'
    
    @property
    def submission_count(self):
        """Get number of submissions"""
        return self.submissions.count()
    
    @property
    def submission_percentage(self):
        """Get submission percentage"""
        total_students = self.group.enrollments.count()
        if total_students == 0:
            return 0
        return (self.submission_count / total_students) * 100

class Submission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Teslim Edildi'),
        ('graded', 'Notlandırıldı'),
        ('late', 'Geç Teslim'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='submissions')
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
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='announcements')
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

class CourseContent(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('lecture', 'Ders Notları'),
        ('presentation', 'Sunum'),
        ('video', 'Video'),
        ('document', 'Doküman'),
        ('other', 'Diğer'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='contents')
    week_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(16)], verbose_name='Hafta')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='document', verbose_name='İçerik Tipi')
    file = models.FileField(upload_to='course_contents/', blank=True, null=True, verbose_name='Dosya')
    url = models.URLField(blank=True, null=True, verbose_name='Link')
    upload_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    
    class Meta:
        verbose_name = 'Ders İçeriği'
        verbose_name_plural = 'Ders İçerikleri'
        ordering = ['course', 'week_number']
        unique_together = ['course', 'week_number', 'title']
    
    def __str__(self):
        return f"{self.course.code} - Hafta {self.week_number}: {self.title}"