"""
DOSYA: apps/courses/models.py
AMAÇ: Ders yönetim sistemi veritabanı modelleri
KULLANIM: 
- Course: Ders tanımları (kod, isim, kredi, kapasite)
- CourseGroup: Ders grupları (öğretmen ataması, sınıf, program)
- Enrollment: Öğrenci-ders kayıtları (notlar, devam, durum)
- CourseContent: Ders materyalleri (hafta bazlı dökümanlar)

İLİŞKİLER:
- Course → CourseGroup (1-N)
- CourseGroup → Enrollment (1-N)
- Student → Enrollment (1-N)
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
    
    COURSE_TYPE_CHOICES = [
        ('university', 'Üniversite Dersi'),
        ('online', 'Online Kurs'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'Başlangıç'),
        ('intermediate', 'Orta'),
        ('advanced', 'İleri'),
        ('expert', 'Uzman'),
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
    
    # Yeni alanlar - Udemy platformu için
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, 
                                   default='university', verbose_name='Kurs Tipi')
    is_self_paced = models.BooleanField(default=False, verbose_name='Kendi Hızında',
                                        help_text='Öğrenci kendi hızında mı ilerleyecek?')
    estimated_duration_hours = models.PositiveIntegerField(default=0, 
                                                           verbose_name='Tahmini Süre (Saat)')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True,
                            verbose_name='Seviye')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True,
                                 verbose_name='Kurs Görseli')
    
    class Meta:
        verbose_name = 'Ders'
        verbose_name_plural = 'Dersler'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def is_online_course(self):
        """Online kurs mu?"""
        return self.course_type == 'online'

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


# ============================================================================
# UDEMY PLATFORM MODELS - Online Kurs Sistemi
# ============================================================================

class CourseModule(models.Model):
    """
    Kursun ana bölümleri/modülleri (Sections)
    Örnek: "1. Giriş", "2. Temel Kavramlar", "3. İleri Seviye"
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    order = models.PositiveIntegerField(default=1, verbose_name='Sıra')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kurs Modülü'
        verbose_name_plural = 'Kurs Modülleri'
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
    
    def __str__(self):
        return f"{self.course.code} - {self.title}"
    
    @property
    def lessons_count(self):
        """Modüldeki ders sayısı"""
        return self.lessons.count()
    
    @property
    def total_duration(self):
        """Toplam video süresi (dakika)"""
        from django.db.models import Sum
        total_seconds = self.lessons.aggregate(
            total=Sum('video_duration')
        )['total'] or 0
        return total_seconds // 60


class Lesson(models.Model):
    """
    Modül içindeki tek bir ders/içerik
    Video, PDF, Quiz veya Opsiyonel Ödev olabilir
    """
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('pdf', 'PDF Döküman'),
        ('quiz', 'Quiz'),
        ('text', 'Metin İçerik'),
        ('assignment', 'Opsiyonel Ödev'),
    ]
    
    module = models.ForeignKey(CourseModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200, verbose_name='Başlık')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, verbose_name='İçerik Tipi')
    order = models.PositiveIntegerField(default=1, verbose_name='Sıra')
    
    # Video için
    video_url = models.URLField(blank=True, null=True, verbose_name='Video URL', 
                                help_text='YouTube, Vimeo veya diğer video platformları')
    video_duration = models.PositiveIntegerField(default=0, verbose_name='Video Süresi', 
                                                 help_text='Süre (saniye)')
    
    # PDF için
    pdf_file = models.FileField(upload_to='lessons/pdfs/', blank=True, null=True, verbose_name='PDF Dosyası')
    
    # Metin için
    text_content = models.TextField(blank=True, verbose_name='Metin İçerik')
    
    # Quiz için (mevcut Quiz modeline bağlantı)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='lesson_links', verbose_name='Quiz')
    
    # Opsiyonel ödev için
    is_assignment_optional = models.BooleanField(default=True, verbose_name='Ödev Opsiyonel mi?')
    assignment_description = models.TextField(blank=True, verbose_name='Ödev Açıklaması')
    assignment_file = models.FileField(upload_to='lessons/assignments/', blank=True, null=True, 
                                       verbose_name='Ödev Referans Dosyası')
    
    is_preview = models.BooleanField(default=False, verbose_name='Önizleme',
                                     help_text='Kayıt olmadan izlenebilir mi?')
    is_mandatory = models.BooleanField(default=True, verbose_name='Zorunlu',
                                       help_text='Tamamlanması zorunlu mu?')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ders'
        verbose_name_plural = 'Dersler'
        ordering = ['module', 'order']
        unique_together = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    @property
    def duration_display(self):
        """Süreyi okunabilir formatta döndür"""
        if self.video_duration:
            minutes = self.video_duration // 60
            seconds = self.video_duration % 60
            return f"{minutes}:{seconds:02d}"
        return "N/A"


class LessonProgress(models.Model):
    """
    Öğrencinin ders içeriği ilerleme takibi
    Video izleme, PDF okuma, quiz çözme ve ödev gönderme durumları
    """
    STATUS_CHOICES = [
        ('not_started', 'Başlanmadı'),
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, 
                               related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, 
                              related_name='student_progress')
    enrollment = models.ForeignKey('CourseEnrollment', on_delete=models.CASCADE, 
                                  related_name='lesson_progress')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started',
                            verbose_name='Durum')
    
    # Video için
    watched_duration = models.PositiveIntegerField(default=0, verbose_name='İzlenen Süre',
                                                   help_text='İzlenen süre (saniye)')
    completion_percentage = models.FloatField(default=0.0, verbose_name='Tamamlanma Yüzdesi',
                                             validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Quiz için
    quiz_score = models.FloatField(null=True, blank=True, verbose_name='Quiz Puanı')
    quiz_passed = models.BooleanField(default=False, verbose_name='Quiz Geçildi')
    quiz_attempt = models.ForeignKey(QuizAttempt, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='lesson_progress')
    
    # Opsiyonel ödev için
    assignment_submitted = models.BooleanField(default=False, verbose_name='Ödev Gönderildi')
    assignment_file = models.FileField(upload_to='optional_assignments/', blank=True, null=True,
                                       verbose_name='Ödev Dosyası')
    assignment_notes = models.TextField(blank=True, verbose_name='Öğrenci Notları')
    assignment_submitted_at = models.DateTimeField(null=True, blank=True)
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Başlangıç')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Tamamlanma')
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='Son Erişim')
    
    class Meta:
        verbose_name = 'Ders İlerlemesi'
        verbose_name_plural = 'Ders İlerlemeleri'
        unique_together = ['student', 'lesson', 'enrollment']
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.lesson.title} ({self.get_status_display()})"


class CourseEnrollment(models.Model):
    """
    Udemy tarzı kurs kaydı - dönem/grup bağımsız, bireysel kayıt
    Her öğrenci istediği zaman kursa kaydolabilir
    """
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('completed', 'Tamamlandı'),
        ('expired', 'Süresi Dolmuş'),
        ('cancelled', 'İptal Edildi'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, 
                               related_name='course_enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='course_enrollments')
    
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Kayıt Tarihi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',
                            verbose_name='Durum')
    
    # İlerleme takibi
    progress_percentage = models.FloatField(default=0.0, verbose_name='İlerleme %',
                                           validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_lessons_count = models.PositiveIntegerField(default=0, 
                                                          verbose_name='Tamamlanan Ders Sayısı')
    total_lessons_count = models.PositiveIntegerField(default=0, 
                                                      verbose_name='Toplam Ders Sayısı')
    
    # Sınav erişimi
    is_eligible_for_exam = models.BooleanField(default=False, 
                                               verbose_name='Sınava Uygun',
                                               help_text='Tüm içerik tamamlandı mı?')
    exam_access_date = models.DateTimeField(null=True, blank=True, 
                                           verbose_name='Sınav Erişim Tarihi')
    
    # Tamamlanma
    completed_at = models.DateTimeField(null=True, blank=True, 
                                       verbose_name='Tamamlanma Tarihi')
    
    # Sertifika
    certificate_issued = models.BooleanField(default=False, verbose_name='Sertifika Verildi')
    certificate_issued_at = models.DateTimeField(null=True, blank=True, 
                                                verbose_name='Sertifika Tarihi')
    
    last_accessed = models.DateTimeField(auto_now=True, verbose_name='Son Erişim')
    
    class Meta:
        verbose_name = 'Kurs Kaydı'
        verbose_name_plural = 'Kurs Kayıtları'
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.name}"
    
    @property
    def can_take_exam(self):
        """Sınava girebilir mi?"""
        return self.is_eligible_for_exam and self.status == 'active'
    
    @property
    def progress_display(self):
        """İlerlemeyi okunabilir formatta"""
        return f"{self.completed_lessons_count}/{self.total_lessons_count} (%{self.progress_percentage:.1f})"


class CourseExam(models.Model):
    """
    Kursun final sınavı - tüm içerik %100 tamamlanınca erişilebilir
    Her kursun bir final sınavı olabilir
    """
    course = models.OneToOneField(Course, on_delete=models.CASCADE, 
                                 related_name='final_exam')
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE, 
                               related_name='course_exam_link')
    
    passing_score = models.FloatField(default=70.0, verbose_name='Geçme Notu',
                                     validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.PositiveIntegerField(default=3, verbose_name='Maksimum Deneme')
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name='Süre (Dakika)')
    
    instructions = models.TextField(blank=True, verbose_name='Talimatlar',
                                   help_text='Sınav hakkında öğrencilere verilecek talimatlar')
    
    is_active = models.BooleanField(default=True, verbose_name='Aktif')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Kurs Sınavı'
        verbose_name_plural = 'Kurs Sınavları'
    
    def __str__(self):
        return f"{self.course.name} - Final Sınavı"


class ExamAttempt(models.Model):
    """
    Öğrencinin sınav denemesi
    Her öğrenci maksimum deneme hakkı kadar sınava girebilir
    """
    STATUS_CHOICES = [
        ('in_progress', 'Devam Ediyor'),
        ('completed', 'Tamamlandı'),
        ('passed', 'Başarılı'),
        ('failed', 'Başarısız'),
    ]
    
    enrollment = models.ForeignKey(CourseEnrollment, on_delete=models.CASCADE, 
                                  related_name='exam_attempts')
    exam = models.ForeignKey(CourseExam, on_delete=models.CASCADE, 
                           related_name='attempts')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, 
                               related_name='exam_attempts')
    
    attempt_number = models.PositiveIntegerField(default=1, verbose_name='Deneme No')
    score = models.FloatField(null=True, blank=True, verbose_name='Puan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='in_progress', verbose_name='Durum')
    
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Başlangıç')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Tamamlanma')
    
    # QuizAttempt ile ilişki (mevcut quiz sistemini kullan)
    quiz_attempt = models.OneToOneField(QuizAttempt, on_delete=models.CASCADE, 
                                       related_name='exam_attempt_link')
    
    class Meta:
        verbose_name = 'Sınav Denemesi'
        verbose_name_plural = 'Sınav Denemeleri'
        ordering = ['-started_at']
        unique_together = ['enrollment', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.exam.course.name} (Deneme {self.attempt_number})"
    
    @property
    def is_passed(self):
        """Sınavı geçti mi?"""
        return self.status == 'passed'


class Certificate(models.Model):
    """
    Otomatik oluşturulan kurs tamamlama sertifikaları
    Sınav başarılı olunca otomatik PDF oluşturulur
    """
    enrollment = models.OneToOneField(CourseEnrollment, on_delete=models.CASCADE, 
                                     related_name='certificate')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, 
                               related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                              related_name='certificates')
    
    certificate_id = models.CharField(max_length=100, unique=True, 
                                     verbose_name='Sertifika No')
    issue_date = models.DateTimeField(auto_now_add=True, 
                                     verbose_name='Düzenlenme Tarihi')
    
    # Sınav bilgileri
    exam_score = models.FloatField(verbose_name='Sınav Puanı')
    completion_date = models.DateTimeField(verbose_name='Tamamlanma Tarihi')
    
    # PDF dosyası
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True,
                                       verbose_name='Sertifika PDF')
    
    # Doğrulama
    verification_url = models.URLField(blank=True, verbose_name='Doğrulama URL')
    is_valid = models.BooleanField(default=True, verbose_name='Geçerli')
    revoked_at = models.DateTimeField(null=True, blank=True, 
                                     verbose_name='İptal Tarihi')
    revoked_reason = models.TextField(blank=True, verbose_name='İptal Nedeni')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Sertifika'
        verbose_name_plural = 'Sertifikalar'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.certificate_id} - {self.student.full_name}"
    
    @property
    def is_revoked(self):
        """Sertifika iptal edilmiş mi?"""
        return not self.is_valid and self.revoked_at is not None