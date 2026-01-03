"""
Quiz Admin - Sınav Yönetimi
Admin: Sistem ayarlarını yönetir
Öğretmen: Sınav ve soru oluşturur (öğretmen panelinden)
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import QuestionBank, Question, Quiz, QuizAttempt, SystemQuizSettings


@admin.register(SystemQuizSettings)
class SystemQuizSettingsAdmin(admin.ModelAdmin):
    """Sınav Sistem Ayarları - Admin İşlevi"""
    
    def has_add_permission(self, request):
        """Singleton - yeni kayıt eklenemez"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Singleton - silinemez"""
        return False
    
    fieldsets = (
        ('Varsayılan Sınav Ayarları', {
            'fields': (
                'default_duration',
                'default_max_attempts',
                'default_passing_score',
            ),
            'description': 'Yeni oluşturulan sınavlar için varsayılan değerler'
        }),
        ('Sınav Davranışları', {
            'fields': (
                'auto_submit_enabled',
                'show_results_immediately',
                'show_correct_answers',
                'allow_review',
            ),
            'description': 'Sınav sırasında ve sonrasında davranışlar'
        }),
        ('Güvenlik Ayarları', {
            'fields': (
                'require_password',
                'ip_restriction_enabled',
                'prevent_tab_switch',
            ),
            'description': 'Sınav güvenliği için ayarlar'
        }),
        ('Sistem Durumu', {
            'fields': (
                'quiz_system_enabled',
                'maintenance_mode',
                'maintenance_message',
            ),
            'description': 'Sınav sisteminin genel durumu'
        }),
        ('Bildirim Ayarları', {
            'fields': (
                'notify_teacher_on_completion',
                'notify_student_on_grade',
            ),
            'description': 'Email bildirimleri'
        }),
        ('Sistem Bilgileri', {
            'fields': ('updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['updated_at', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        """Güncelleyen kullanıcıyı kaydet"""
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context=None):
        """Singleton - direkt düzenleme sayfasına yönlendir"""
        obj = SystemQuizSettings.load()
        return self.changeform_view(request, str(obj.pk), '', extra_context)


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    """Soru Bankası - Basit"""
    
    list_display = ['name', 'course_group_name', 'question_count']
    
    list_filter = ['course_group']
    
    search_fields = ['name', 'course_group__course__name', 'course_group__course__code']
    
    def course_group_name(self, obj):
        """Ders grubu adı"""
        if obj.course_group:
            return f"{obj.course_group.course.code} - {obj.course_group.name}"
        return "-"
    course_group_name.short_description = 'Ders Grubu'
    
    def question_count(self, obj):
        """Soru sayısı"""
        return obj.questions.count()
    question_count.short_description = 'Soru Sayısı'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Soru Yönetimi - Basit"""
    
    list_display = [
        'question_text_short',
        'question_type',
        'difficulty',
        'points',
        'bank_name',
    ]
    
    list_filter = ['question_type', 'difficulty', 'bank']
    
    search_fields = ['question_text', 'bank__name']
    
    def question_text_short(self, obj):
        """Soru metni (kısa)"""
        if len(obj.question_text) > 50:
            return obj.question_text[:50] + "..."
        return obj.question_text
    question_text_short.short_description = 'Soru'
    
    def bank_name(self, obj):
        """Soru bankası"""
        return obj.bank.name if obj.bank else "-"
    bank_name.short_description = 'Soru Bankası'


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Sınav Yönetimi - Basit"""
    
    list_display = [
        'title',
        'course_name',
        'start_time',
        'end_time',
        'duration_minutes',
        'status_badge',
    ]
    
    list_filter = ['start_time', 'end_time', 'course_group__course']
    
    search_fields = ['title', 'course_group__course__name', 'course_group__course__code']
    
    def course_name(self, obj):
        """Ders adı"""
        return f"{obj.course_group.course.code} - {obj.course_group.course.name}"
    course_name.short_description = 'Ders'
    
    def status_badge(self, obj):
        """Durum badge'i"""
        from django.utils import timezone
        now = timezone.now()
        
        if now < obj.start_time:
            color = '#ffa94d'
            status = 'Başlamadı'
        elif now > obj.end_time:
            color = '#adb5bd'
            status = 'Bitti'
        else:
            color = '#51cf66'
            status = 'Devam Ediyor'
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    status_badge.short_description = 'Durum'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Sınav Denemeleri - Basit"""
    
    list_display = [
        'student_name',
        'quiz_name',
        'score',
        'started_at',
        'status_badge',
    ]
    
    list_filter = ['status', 'started_at', 'quiz']
    
    search_fields = [
        'student__first_name',
        'student__last_name',
        'student__school_number',
        'quiz__title',
    ]
    
    def student_name(self, obj):
        """Öğrenci adı"""
        return f"{obj.student.first_name} {obj.student.last_name}"
    student_name.short_description = 'Öğrenci'
    
    def quiz_name(self, obj):
        """Sınav adı"""
        return obj.quiz.title
    quiz_name.short_description = 'Sınav'
    
    def status_badge(self, obj):
        """Durum badge'i"""
        colors = {
            'in_progress': '#ffa94d',
            'completed': '#51cf66',
            'abandoned': '#ff6b6b',
            'graded': '#339af0'
        }
        color = colors.get(obj.status, '#868e96')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Durum'
