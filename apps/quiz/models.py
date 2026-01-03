"""
Enhanced Quiz System with Question Bank
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from apps.courses.models import CourseGroup


class QuestionBank(models.Model):
    """Centralized question bank"""
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='question_banks',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    is_shared = models.BooleanField(
        default=False,
        help_text='Share with other teachers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Soru Bankası'
        verbose_name_plural = 'Soru Bankaları'
    
    def __str__(self):
        return self.name


class Question(models.Model):
    """Individual questions"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Çoktan Seçmeli'),
        ('true_false', 'Doğru/Yanlış'),
        ('short_answer', 'Kısa Cevap'),
        ('essay', 'Essay'),
        ('matching', 'Eşleştirme'),
        ('fill_blank', 'Boşluk Doldurma'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Kolay'),
        ('medium', 'Orta'),
        ('hard', 'Zor'),
    ]
    
    bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_LEVELS,
        default='medium'
    )
    
    question_text = models.TextField()
    question_image = models.ImageField(
        upload_to='quiz/questions/',
        null=True,
        blank=True
    )
    
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=1
    )
    
    # For multiple choice
    option_a = models.CharField(max_length=500, blank=True)
    option_b = models.CharField(max_length=500, blank=True)
    option_c = models.CharField(max_length=500, blank=True)
    option_d = models.CharField(max_length=500, blank=True)
    option_e = models.CharField(max_length=500, blank=True)
    
    correct_answer = models.TextField(help_text='Correct answer or answer key')
    explanation = models.TextField(blank=True, help_text='Explanation of correct answer')
    
    tags = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated tags'
    )
    
    usage_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Soru'
        verbose_name_plural = 'Sorular'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_question_type_display()} - {self.question_text[:50]}"


class Quiz(models.Model):
    """Quiz/Exam with enhanced features"""
    course_group = models.ForeignKey(
        CourseGroup,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(
        help_text='Duration in minutes (0 for unlimited)'
    )
    
    # Settings
    max_attempts = models.IntegerField(
        default=2,
        help_text='Maksimum giriş hakkı (varsayılan: 2)'
    )
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=60,
        help_text='Minimum percentage to pass'
    )
    use_best_attempt = models.BooleanField(
        default=True,
        help_text='En yüksek puanlı denemeyi not olarak kullan (False ise son deneme)'
    )
    
    # Features
    shuffle_questions = models.BooleanField(default=False)
    shuffle_options = models.BooleanField(default=False)
    show_results_immediately = models.BooleanField(default=False)
    allow_review = models.BooleanField(default=True)
    auto_submit = models.BooleanField(
        default=True,
        help_text='Auto-submit when time expires'
    )
    
    # Random question selection
    use_random_questions = models.BooleanField(
        default=False,
        help_text='Her öğrenciye rastgele sorular seç'
    )
    random_question_count = models.IntegerField(
        default=40,
        help_text='Her öğrenciye seçilecek soru sayısı'
    )
    random_question_pool_size = models.IntegerField(
        default=250,
        help_text='Rastgele seçim için soru havuzu boyutu (soru bankasından)'
    )
    
    # Restrictions
    require_password = models.BooleanField(default=False)
    password = models.CharField(max_length=100, blank=True)
    
    ip_restriction = models.TextField(
        blank=True,
        help_text='Comma-separated IP addresses or ranges'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quizler'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.course_group.course.code} - {self.title}"
    
    @property
    def is_available(self):
        """Check if quiz is currently available"""
        now = timezone.now()
        return (self.is_active and 
                self.start_time <= now <= self.end_time)
    
    def get_student_attempts_count(self, student):
        """Get number of attempts for a student"""
        return self.attempts.filter(student=student).count()
    
    def can_student_attempt(self, student):
        """Check if student can make another attempt"""
        attempts_count = self.get_student_attempts_count(student)
        return attempts_count < self.max_attempts
    
    def get_student_best_score(self, student):
        """Get student's best score from all attempts"""
        attempts = self.attempts.filter(
            student=student,
            status__in=['submitted', 'auto_submitted']
        ).exclude(score__isnull=True)
        
        if not attempts.exists():
            return None
        
        if self.use_best_attempt:
            # En yüksek puanlı deneme
            return attempts.order_by('-score').first()
        else:
            # Son deneme
            return attempts.order_by('-submitted_at').first()
    
    @property
    def total_points(self):
        """Calculate total points - always 100"""
        return Decimal('100.00')


class QuizQuestion(models.Model):
    """Questions in a quiz"""
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE
    )
    order = models.IntegerField(default=0)
    points = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text='Points for this question in this quiz'
    )
    # For random questions: which student this question is assigned to
    assigned_to_student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assigned_quiz_questions',
        help_text='If using random questions, which student this question is assigned to'
    )
    
    class Meta:
        ordering = ['order']
        unique_together = ['quiz', 'question', 'assigned_to_student']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizAttempt(models.Model):
    """Student quiz attempts with timer"""
    STATUS_CHOICES = [
        ('in_progress', 'Devam Ediyor'),
        ('submitted', 'Teslim Edildi'),
        ('auto_submitted', 'Otomatik Teslim'),
        ('abandoned', 'Terk Edildi'),
    ]
    
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    
    attempt_number = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress'
    )
    
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Quiz Denemesi'
        verbose_name_plural = 'Quiz Denemeleri'
        ordering = ['-started_at']
        unique_together = ['quiz', 'student', 'attempt_number']
    
    def __str__(self):
        return f"{self.student} - {self.quiz.title} (#{self.attempt_number})"
    
    @property
    def is_expired(self):
        """Check if attempt time has expired"""
        if self.quiz.duration_minutes == 0:
            return False
        
        if self.status != 'in_progress':
            return False
        
        elapsed = (timezone.now() - self.started_at).total_seconds() / 60
        return elapsed > self.quiz.duration_minutes
    
    @property
    def remaining_time_seconds(self):
        """Get remaining time in seconds"""
        if self.quiz.duration_minutes == 0:
            return None
        
        if self.status != 'in_progress':
            return 0
        
        elapsed = (timezone.now() - self.started_at).total_seconds()
        total = self.quiz.duration_minutes * 60
        remaining = max(0, total - elapsed)
        
        return int(remaining)
    
    def auto_submit_if_expired(self):
        """Auto-submit if time expired and auto_submit is enabled"""
        if self.is_expired and self.quiz.auto_submit:
            self.status = 'auto_submitted'
            self.submitted_at = timezone.now()
            self.save()
            return True
        return False


class QuizAnswer(models.Model):
    """Student answers to quiz questions"""
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    quiz_question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE
    )
    
    answer_text = models.TextField(blank=True)
    selected_option = models.CharField(max_length=1, blank=True)
    
    is_correct = models.BooleanField(null=True, blank=True)
    points_earned = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    teacher_feedback = models.TextField(blank=True)
    
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Quiz Cevabı'
        verbose_name_plural = 'Quiz Cevapları'
        unique_together = ['attempt', 'quiz_question']
    
    def __str__(self):
        return f"{self.attempt.student} - Q{self.quiz_question.order}"
    
    def check_answer(self):
        """Auto-grade the answer if possible"""
        question = self.quiz_question.question
        
        if question.question_type in ['multiple_choice', 'true_false']:
            self.is_correct = (self.selected_option.upper() == 
                             question.correct_answer.upper())
            self.points_earned = self.quiz_question.points if self.is_correct else 0
            self.save()
            return self.is_correct
        
        # Manual grading needed for essay, short answer, etc.
        return None



class SystemQuizSettings(models.Model):
    """Sistem Geneli Sınav Ayarları - Singleton Model"""
    
    # Varsayılan sınav ayarları
    default_duration = models.IntegerField(
        default=60,
        verbose_name='Varsayılan Sınav Süresi (dakika)',
        help_text='Yeni oluşturulan sınavlar için varsayılan süre'
    )
    default_max_attempts = models.IntegerField(
        default=1,
        verbose_name='Varsayılan Deneme Sayısı',
        help_text='Öğrencilerin sınava kaç kez girebileceği'
    )
    default_passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        verbose_name='Varsayılan Geçme Notu (%)',
        help_text='Sınavdan geçmek için gereken minimum puan yüzdesi'
    )
    
    # Sınav davranışları
    auto_submit_enabled = models.BooleanField(
        default=True,
        verbose_name='Otomatik Teslim Etkin',
        help_text='Süre bittiğinde sınavı otomatik olarak teslim et'
    )
    show_results_immediately = models.BooleanField(
        default=False,
        verbose_name='Sonuçları Hemen Göster',
        help_text='Sınav bitiminde sonuçları öğrenciye göster'
    )
    show_correct_answers = models.BooleanField(
        default=False,
        verbose_name='Doğru Cevapları Göster',
        help_text='Sınav sonunda doğru cevapları göster'
    )
    allow_review = models.BooleanField(
        default=True,
        verbose_name='İncelemeye İzin Ver',
        help_text='Öğrencilerin sınav sonrası cevaplarını incelemesine izin ver'
    )
    
    # Güvenlik ayarları
    require_password = models.BooleanField(
        default=False,
        verbose_name='Şifre Gerektir',
        help_text='Sınavlara giriş için şifre iste'
    )
    ip_restriction_enabled = models.BooleanField(
        default=False,
        verbose_name='IP Kısıtlaması Etkin',
        help_text='Sınavlara sadece belirli IP adreslerinden erişime izin ver'
    )
    prevent_tab_switch = models.BooleanField(
        default=True,
        verbose_name='Sekme Değiştirmeyi Engelle',
        help_text='Öğrenci sınav sırasında başka sekmeye geçerse uyar'
    )
    
    # Sınav sistemi durumu
    quiz_system_enabled = models.BooleanField(
        default=True,
        verbose_name='Sınav Sistemi Aktif',
        help_text='Tüm sınav sistemini aktif/pasif yap'
    )
    maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='Bakım Modu',
        help_text='Sınav sistemi bakımda (sadece adminler erişebilir)'
    )
    maintenance_message = models.TextField(
        blank=True,
        verbose_name='Bakım Mesajı',
        help_text='Bakım modunda gösterilecek mesaj'
    )
    
    # Bildirim ayarları
    notify_teacher_on_completion = models.BooleanField(
        default=True,
        verbose_name='Öğretmene Bildirim Gönder',
        help_text='Öğrenci sınavı tamamladığında öğretmene email gönder'
    )
    notify_student_on_grade = models.BooleanField(
        default=True,
        verbose_name='Öğrenciye Not Bildirimi',
        help_text='Sınav notlandırıldığında öğrenciye bildirim gönder'
    )
    
    # Metadata
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Son Güncellenme'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Güncelleyen'
    )
    
    class Meta:
        verbose_name = 'Sınav Sistem Ayarları'
        verbose_name_plural = 'Sınav Sistem Ayarları'
    
    def __str__(self):
        return "Sınav Sistem Ayarları"
    
    def save(self, *args, **kwargs):
        """Singleton pattern - sadece 1 kayıt olabilir"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Singleton - silinemez"""
        pass
    
    @classmethod
    def load(cls):
        """Ayarları yükle veya oluştur"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
