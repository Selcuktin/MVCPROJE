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
    
    # Academic term integration (nullable for backward compatibility)
    academic_term = models.ForeignKey(
        'academic.AcademicTerm',
        on_delete=models.PROTECT,
        related_name='course_groups',
        null=True,
        blank=True,
        help_text='Akademik dönem (örn: 2024-2025 Güz)'
    )
    
    # Legacy field (will be deprecated)
    semester = models.CharField(
        max_length=20,
        help_text='Eski dönem formatı - kullanım dışı'
    )
    
    classroom = models.CharField(max_length=50)
    schedule = models.CharField(max_length=200, help_text='Ör: Pazartesi 09:00-12:00')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        verbose_name = 'Ders'
        verbose_name_plural = 'Dersler'
        unique_together = ['course', 'teacher', 'semester']
    
    def __str__(self):
        # Sadece ders kodu ve adı göster (grup bilgisi yok)
        return f"{self.course.code} - {self.course.name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate name if not provided (A, B, C, ...)"""
        if not self.pk and (not self.name or self.name == 'A'):
            # Get existing groups for this course and semester
            existing_groups = CourseGroup.objects.filter(
                course=self.course,
                semester=self.semester
            ).values_list('name', flat=True)
            
            # Generate next available letter
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            for letter in letters:
                if letter not in existing_groups:
                    self.name = letter
                    break
        
        super().save(*args, **kwargs)

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
        ('FD', 'FD'),
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
    
    def calculate_letter_grade(self):
        """Calculate letter grade from numerical grades"""
        # Eğer final veya büt notu yoksa NA döndür
        if not self.final_grade and not self.makeup_grade:
            return 'NA'
        
        # DEPRECATED: This calculation is now handled by GradebookService
        # Return existing grade if set, otherwise return 'NA'
        return self.grade if self.grade else 'NA'
    
    def save(self, *args, **kwargs):
        """Override save - grade is now set by GradebookService"""
        # Don't auto-calculate grade here anymore, it's handled by GradebookService
        super().save(*args, **kwargs)

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
    
    def save(self, *args, **kwargs):
        """Auto-update status based on deadline"""
        from django.utils import timezone
        if self.due_date and timezone.now() > self.due_date and self.status == 'active':
            self.status = 'expired'
        super().save(*args, **kwargs)
    
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
    
    def save(self, *args, **kwargs):
        """Auto-update status based on expiry date"""
        from django.utils import timezone
        if self.expire_date and timezone.now() > self.expire_date and self.status == 'active':
            self.status = 'expired'
        super().save(*args, **kwargs)

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

class AssignmentHistory(models.Model):
    """
    Öğretmen-ders atama geçmişi/log
    """
    ACTION_CHOICES = [
        ('assign', 'Atama'),
        ('remove', 'Çıkarma'),
        ('update', 'Güncelleme'),
        ('bulk_assign', 'Toplu Atama'),
        ('bulk_remove', 'Toplu Çıkarma'),
    ]
    
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='assignment_history', verbose_name='Ders Grubu')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='assignment_history', verbose_name='Öğretmen')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='İşlem')
    description = models.TextField(verbose_name='Açıklama')
    performed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name='performed_assignments', verbose_name='İşlemi Yapan')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='İşlem Tarihi')
    
    class Meta:
        verbose_name = 'Atama Geçmişi'
        verbose_name_plural = 'Atama Geçmişleri'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.teacher.full_name} - {self.course_group.course.code} ({self.timestamp})"

class ExampleQuestion(models.Model):
    """
    Öğretmenler tarafından eklenen örnek sorular.
    Öğrencilere görünür; "quiz" (çoklu soru seti) veya "solution" (tek çözüm anlatımı) tipi destekler.
    """
    QUESTION_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('solution', 'Çözüm Örneği'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Kayıtlı Öğrencilere Görünür'),
        ('hidden', 'Gizli'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='example_questions')
    created_by = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='example_questions')
    title = models.CharField(max_length=255)
    content = models.TextField(help_text='Soru metni veya açıklaması')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='solution')
    attachment = models.FileField(upload_to='example_questions/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')

    class Meta:
        verbose_name = 'Örnek Soru'
        verbose_name_plural = 'Örnek Sorular'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course.code} - {self.title}"


# --- Quiz Modelleri ---
class Quiz(models.Model):
    """Ders bazlı quiz/sınav/pratik tanımı."""
    QUIZ_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('exam', 'Sınav'),
        ('practice', 'Pratik'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    created_by = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quiz_type = models.CharField(max_length=16, choices=QUIZ_TYPE_CHOICES, default='quiz')
    duration_minutes = models.PositiveIntegerField(default=20)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizler'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.course.code} - {self.title}"


class QuizQuestion(models.Model):
    """Quiz sorusu. Çoktan seçmeli için şıklar ayrı tabloda tutulur."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    order = models.PositiveIntegerField(default=1)
    text = models.TextField()
    # İsteğe bağlı açıklama/çözüm
    explanation = models.TextField(blank=True)
    # Doğru şık opsiyonel (öğretmen sonra işaretleyebilir)
    correct_choice = models.ForeignKey('QuizChoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    class Meta:
        verbose_name = 'Quiz Sorusu'
        verbose_name_plural = 'Quiz Soruları'
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f"Q{self.order}: {self.text[:50]}"


class QuizChoice(models.Model):
    """Çoktan seçmeli şık."""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='choices')
    label = models.CharField(max_length=2, default='')  # A, B, C, D, E
    text = models.TextField()

    class Meta:
        verbose_name = 'Şık'
        verbose_name_plural = 'Şıklar'
        ordering = ['label']

    def __str__(self) -> str:
        return f"{self.label}) {self.text[:40]}"


class QuizAttempt(models.Model):
    """Öğrencinin quiz denemesi."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Quiz Denemesi'
        verbose_name_plural = 'Quiz Denemeleri'
        unique_together = ['quiz', 'student', 'started_at']

    def __str__(self) -> str:
        return f"{self.student.full_name} - {self.quiz.title}"


class QuizAnswer(models.Model):
    """Denemedeki tek bir soruya verilen cevap."""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.ForeignKey(QuizChoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    is_correct = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Cevap'
        verbose_name_plural = 'Cevaplar'
        unique_together = ['attempt', 'question']


class PlagiarismReport(models.Model):
    """
    Basit intihal raporu: bir teslimin metni ile diğer kaynaklar arasındaki benzerlik.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='plagiarism_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    method = models.CharField(max_length=50, default='ngram_jaccard')
    max_similarity = models.FloatField(default=0.0)
    details = models.JSONField(default=dict)

    class Meta:
        verbose_name = 'İntihal Raporu'
        verbose_name_plural = 'İntihal Raporları'
        ordering = ['-created_at']

    def __str__(self):
        return f"Submission {self.submission_id} - {self.max_similarity:.2f}"