from django.contrib import admin
from .models import (
    Course, CourseGroup, Enrollment, CourseContent, AssignmentHistory,
    # Yeni Udemy platform modelleri
    CourseModule, Lesson, LessonProgress, CourseEnrollment,
    CourseExam, ExamAttempt, Certificate
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'department', 'semester', 'capacity', 'is_elective', 'status']
    list_filter = ['department', 'semester', 'is_elective', 'status', 'credits']
    search_fields = ['code', 'name', 'department']

@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ['course', 'teacher', 'semester', 'classroom', 'status']
    list_filter = ['semester', 'status', 'course__department']
    search_fields = ['course__code', 'course__name', 'teacher__first_name', 'teacher__last_name']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'enrollment_date', 'attendance', 'grade', 'status']
    list_filter = ['status', 'grade', 'enrollment_date', 'group__course__department']
    search_fields = ['student__first_name', 'student__last_name', 'group__course__code']

@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ['course', 'week_number', 'title', 'content_type', 'upload_date', 'is_active']
    list_filter = ['content_type', 'is_active', 'week_number', 'course__department']
    search_fields = ['title', 'description', 'course__code', 'course__name']
    ordering = ['course', 'week_number']

@admin.register(AssignmentHistory)
class AssignmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'course_group', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp', 'course_group__course__department']
    search_fields = ['teacher__first_name', 'teacher__last_name', 'course_group__course__code', 'description']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']


# ============================================================================
# UDEMY PLATFORM ADMIN KAYITLARI - Online Kurs Sistemi
# ============================================================================

class LessonInline(admin.TabularInline):
    """Modül içinde ders inline"""
    model = Lesson
    extra = 1
    fields = ['title', 'content_type', 'order', 'is_mandatory', 'is_preview']
    ordering = ['order']


@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'order', 'lessons_count', 'total_duration', 'is_active']
    list_filter = ['course', 'is_active', 'course__department']
    search_fields = ['title', 'description', 'course__code', 'course__name']
    ordering = ['course', 'order']
    inlines = [LessonInline]
    
    def lessons_count(self, obj):
        """Ders sayısı"""
        return obj.lessons_count
    lessons_count.short_description = 'Ders Sayısı'
    
    def total_duration(self, obj):
        """Toplam süre"""
        duration = obj.total_duration
        return f"{duration} dk" if duration else "0 dk"
    total_duration.short_description = 'Toplam Süre'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'module', 'title', 'content_type', 'order', 
        'duration_display', 'is_mandatory', 'is_preview'
    ]
    list_filter = [
        'content_type', 'is_mandatory', 'is_preview', 
        'module__course__department'
    ]
    search_fields = ['title', 'description', 'module__title', 'module__course__code']
    ordering = ['module', 'order']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('module', 'title', 'description', 'content_type', 'order')
        }),
        ('Video İçeriği', {
            'fields': ('video_url', 'video_duration'),
            'classes': ('collapse',)
        }),
        ('Döküman İçeriği', {
            'fields': ('pdf_file', 'text_content'),
            'classes': ('collapse',)
        }),
        ('Quiz İçeriği', {
            'fields': ('quiz',),
            'classes': ('collapse',)
        }),
        ('Opsiyonel Ödev', {
            'fields': ('is_assignment_optional', 'assignment_description', 'assignment_file'),
            'classes': ('collapse',)
        }),
        ('Ayarlar', {
            'fields': ('is_preview', 'is_mandatory')
        }),
    )


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'lesson', 'enrollment', 'status', 
        'completion_percentage', 'quiz_passed', 'assignment_submitted',
        'last_accessed'
    ]
    list_filter = [
        'status', 'quiz_passed', 'assignment_submitted',
        'lesson__content_type', 'enrollment__course__department'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'lesson__title', 'enrollment__course__name'
    ]
    readonly_fields = ['started_at', 'completed_at', 'last_accessed']
    ordering = ['-last_accessed']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('student', 'lesson', 'enrollment', 'status')
        }),
        ('Video İlerleme', {
            'fields': ('watched_duration', 'completion_percentage'),
            'classes': ('collapse',)
        }),
        ('Quiz Sonucu', {
            'fields': ('quiz_score', 'quiz_passed', 'quiz_attempt'),
            'classes': ('collapse',)
        }),
        ('Ödev Durumu', {
            'fields': ('assignment_submitted', 'assignment_file', 'assignment_notes', 'assignment_submitted_at'),
            'classes': ('collapse',)
        }),
        ('Tarihler', {
            'fields': ('started_at', 'completed_at', 'last_accessed')
        }),
    )


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'course', 'status', 'progress_percentage',
        'progress_display', 'is_eligible_for_exam', 'certificate_issued',
        'enrolled_at'
    ]
    list_filter = [
        'status', 'is_eligible_for_exam', 'certificate_issued',
        'course__department', 'enrolled_at'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'course__code', 'course__name'
    ]
    readonly_fields = [
        'enrolled_at', 'progress_percentage', 'completed_lessons_count',
        'is_eligible_for_exam', 'exam_access_date', 'completed_at',
        'certificate_issued_at', 'last_accessed', 'progress_display'
    ]
    ordering = ['-enrolled_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('student', 'course', 'status', 'enrolled_at')
        }),
        ('İlerleme Durumu', {
            'fields': (
                'progress_percentage', 'completed_lessons_count',
                'total_lessons_count', 'progress_display'
            )
        }),
        ('Sınav Erişimi', {
            'fields': ('is_eligible_for_exam', 'exam_access_date')
        }),
        ('Tamamlanma', {
            'fields': ('completed_at',)
        }),
        ('Sertifika', {
            'fields': ('certificate_issued', 'certificate_issued_at')
        }),
        ('Son Erişim', {
            'fields': ('last_accessed',)
        }),
    )


@admin.register(CourseExam)
class CourseExamAdmin(admin.ModelAdmin):
    list_display = [
        'course', 'quiz', 'passing_score', 'max_attempts',
        'duration_minutes', 'is_active'
    ]
    list_filter = ['is_active', 'course__department']
    search_fields = ['course__code', 'course__name', 'quiz__title']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('course', 'quiz', 'instructions')
        }),
        ('Sınav Ayarları', {
            'fields': ('passing_score', 'max_attempts', 'duration_minutes')
        }),
        ('Durum', {
            'fields': ('is_active',)
        }),
    )


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'exam', 'attempt_number', 'score',
        'status', 'is_passed', 'started_at', 'completed_at'
    ]
    list_filter = [
        'status', 'exam__course__department', 'started_at'
    ]
    search_fields = [
        'student__first_name', 'student__last_name',
        'exam__course__code', 'exam__course__name'
    ]
    readonly_fields = ['started_at', 'completed_at', 'score', 'status', 'is_passed']
    ordering = ['-started_at']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('enrollment', 'exam', 'student', 'attempt_number')
        }),
        ('Sonuç', {
            'fields': ('score', 'status', 'is_passed')
        }),
        ('Quiz Denemesi', {
            'fields': ('quiz_attempt',)
        }),
        ('Tarihler', {
            'fields': ('started_at', 'completed_at')
        }),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = [
        'certificate_id', 'student', 'course', 'exam_score',
        'issue_date', 'is_valid', 'is_revoked'
    ]
    list_filter = [
        'is_valid', 'issue_date', 'course__department'
    ]
    search_fields = [
        'certificate_id', 'student__first_name', 'student__last_name',
        'course__code', 'course__name'
    ]
    readonly_fields = [
        'certificate_id', 'issue_date', 'verification_url',
        'created_at', 'is_revoked'
    ]
    ordering = ['-issue_date']
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('enrollment', 'student', 'course', 'certificate_id')
        }),
        ('Sınav Bilgileri', {
            'fields': ('exam_score', 'completion_date')
        }),
        ('Sertifika Dosyası', {
            'fields': ('certificate_file', 'verification_url')
        }),
        ('Geçerlilik', {
            'fields': ('is_valid', 'revoked_at', 'revoked_reason')
        }),
        ('Tarih', {
            'fields': ('issue_date', 'created_at')
        }),
    )
    
    actions = ['revoke_certificates']
    
    def revoke_certificates(self, request, queryset):
        """Seçili sertifikaları iptal et"""
        from django.utils import timezone
        count = queryset.update(
            is_valid=False,
            revoked_at=timezone.now(),
            revoked_reason='Admin tarafından iptal edildi'
        )
        self.message_user(request, f'{count} sertifika iptal edildi.')
    revoke_certificates.short_description = 'Seçili sertifikaları iptal et'