"""
DOSYA: apps/courses/serializers.py
AMAÇ: DRF Serializers - API için veri serialization
KULLANIM: Model verilerini JSON formatına çevirmek için
"""
from rest_framework import serializers
from django.db.models import Sum, Count, Q
from .models import (
    Course, CourseGroup, Enrollment, Assignment, Submission,
    Announcement, CourseContent, Quiz, QuizQuestion, QuizChoice,
    QuizAttempt, QuizAnswer, ExampleQuestion,
    # Yeni Udemy platform modelleri
    CourseModule, Lesson, LessonProgress, CourseEnrollment,
    CourseExam, ExamAttempt, Certificate
)
from apps.students.models import Student
from apps.teachers.models import Teacher


# ============================================================================
# MEVCUT SİSTEM SERİALİZERLARI (Üniversite Sistemi)
# ============================================================================

class CourseSerializer(serializers.ModelSerializer):
    """Temel kurs serializer"""
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'credits', 'description', 'department',
            'semester', 'capacity', 'is_elective', 'status', 'course_type',
            'is_self_paced', 'estimated_duration_hours', 'level', 'thumbnail'
        ]


class CourseGroupSerializer(serializers.ModelSerializer):
    """Ders grubu serializer"""
    course = CourseSerializer(read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    
    class Meta:
        model = CourseGroup
        fields = [
            'id', 'course', 'teacher', 'teacher_name', 'name', 
            'semester', 'classroom', 'schedule', 'status'
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    """Kayıt serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_name = serializers.CharField(source='group.course.name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'student_name', 'group', 'course_name',
            'enrollment_date', 'attendance', 'midterm_grade', 'final_grade',
            'makeup_grade', 'project_grade', 'grade', 'status'
        ]


# ============================================================================
# UDEMY PLATFORM SERİALİZERLARI (Online Kurs Sistemi)
# ============================================================================

class CourseModuleSerializer(serializers.ModelSerializer):
    """
    Kurs modülü serializer
    Modül içindeki ders sayısı ve toplam süre hesaplanır
    """
    lessons_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseModule
        fields = [
            'id', 'course', 'title', 'description', 'order', 
            'is_active', 'lessons_count', 'total_duration', 'lessons',
            'created_at', 'updated_at'
        ]
    
    def get_lessons_count(self, obj):
        """Modüldeki ders sayısı"""
        return obj.lessons.filter(is_mandatory=True).count()
    
    def get_total_duration(self, obj):
        """Toplam video süresi (dakika)"""
        total_seconds = obj.lessons.aggregate(
            total=Sum('video_duration')
        )['total'] or 0
        return total_seconds // 60
    
    def get_lessons(self, obj):
        """Modüldeki dersleri döndür"""
        request = self.context.get('request')
        lessons = obj.lessons.order_by('order')
        return LessonSerializer(lessons, many=True, context={'request': request}).data


class LessonSerializer(serializers.ModelSerializer):
    """
    Ders içeriği serializer
    Öğrenci ilerleme durumu da dahil edilir
    """
    module_title = serializers.CharField(source='module.title', read_only=True)
    progress = serializers.SerializerMethodField()
    duration_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'module', 'module_title', 'title', 'description', 
            'content_type', 'order', 'video_url', 'video_duration', 
            'pdf_file', 'text_content', 'quiz', 'is_assignment_optional',
            'assignment_description', 'assignment_file', 'is_preview', 
            'is_mandatory', 'duration_display', 'progress',
            'created_at', 'updated_at'
        ]
    
    def get_progress(self, obj):
        """Öğrencinin bu dersteki ilerleme durumu"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                student = request.user.student
                enrollment = CourseEnrollment.objects.get(
                    student=student,
                    course=obj.module.course
                )
                progress = LessonProgress.objects.get(
                    student=student,
                    lesson=obj,
                    enrollment=enrollment
                )
                return {
                    'status': progress.status,
                    'completion_percentage': progress.completion_percentage,
                    'watched_duration': progress.watched_duration,
                    'quiz_score': progress.quiz_score,
                    'quiz_passed': progress.quiz_passed,
                    'assignment_submitted': progress.assignment_submitted,
                    'last_accessed': progress.last_accessed,
                }
            except (Student.DoesNotExist, CourseEnrollment.DoesNotExist, LessonProgress.DoesNotExist):
                return None
        return None


class LessonProgressSerializer(serializers.ModelSerializer):
    """Ders ilerleme detay serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)
    
    class Meta:
        model = LessonProgress
        fields = [
            'id', 'student', 'student_name', 'lesson', 'lesson_title',
            'enrollment', 'status', 'watched_duration', 'completion_percentage',
            'quiz_score', 'quiz_passed', 'quiz_attempt', 'assignment_submitted',
            'assignment_file', 'assignment_notes', 'assignment_submitted_at',
            'started_at', 'completed_at', 'last_accessed'
        ]
        read_only_fields = ['started_at', 'completed_at', 'last_accessed']


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Kurs kaydı serializer
    Kurs detayları ve ilerleme durumu
    """
    course = CourseSerializer(read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    progress_display = serializers.ReadOnlyField()
    can_take_exam = serializers.ReadOnlyField()
    current_module = serializers.SerializerMethodField()
    next_lesson = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'student', 'student_name', 'course', 'enrolled_at', 
            'status', 'progress_percentage', 'completed_lessons_count',
            'total_lessons_count', 'progress_display', 'is_eligible_for_exam',
            'can_take_exam', 'exam_access_date', 'completed_at',
            'certificate_issued', 'certificate_issued_at', 'last_accessed',
            'current_module', 'next_lesson'
        ]
        read_only_fields = [
            'enrolled_at', 'progress_percentage', 'completed_lessons_count',
            'is_eligible_for_exam', 'exam_access_date', 'completed_at',
            'certificate_issued', 'certificate_issued_at', 'last_accessed'
        ]
    
    def get_current_module(self, obj):
        """Son erişilen dersin modülü"""
        last_progress = obj.lesson_progress.order_by('-last_accessed').first()
        if last_progress:
            return {
                'id': last_progress.lesson.module.id,
                'title': last_progress.lesson.module.title,
                'order': last_progress.lesson.module.order,
            }
        return None
    
    def get_next_lesson(self, obj):
        """Öğrencinin tamamlaması gereken sonraki ders"""
        from .services import LessonProgressService
        next_lesson = LessonProgressService.get_next_lesson(
            obj.student, 
            obj.course
        )
        if next_lesson:
            return {
                'id': next_lesson.id,
                'title': next_lesson.title,
                'module_title': next_lesson.module.title,
                'content_type': next_lesson.content_type,
            }
        return None


class CourseExamSerializer(serializers.ModelSerializer):
    """Kurs sınavı serializer"""
    course_name = serializers.CharField(source='course.name', read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    
    class Meta:
        model = CourseExam
        fields = [
            'id', 'course', 'course_name', 'quiz', 'quiz_title',
            'passing_score', 'max_attempts', 'duration_minutes',
            'instructions', 'is_active', 'created_at', 'updated_at'
        ]


class ExamAttemptSerializer(serializers.ModelSerializer):
    """Sınav denemesi serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_name = serializers.CharField(source='exam.course.name', read_only=True)
    is_passed = serializers.ReadOnlyField()
    
    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'enrollment', 'exam', 'student', 'student_name',
            'course_name', 'attempt_number', 'score', 'status',
            'started_at', 'completed_at', 'quiz_attempt', 'is_passed'
        ]
        read_only_fields = ['started_at', 'completed_at', 'score', 'status']


class CertificateSerializer(serializers.ModelSerializer):
    """Sertifika serializer"""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    is_revoked = serializers.ReadOnlyField()
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'enrollment', 'student', 'student_name', 'course',
            'course_name', 'course_code', 'certificate_id', 'issue_date',
            'exam_score', 'completion_date', 'certificate_file',
            'verification_url', 'is_valid', 'is_revoked', 'revoked_at',
            'revoked_reason', 'created_at'
        ]
        read_only_fields = [
            'certificate_id', 'issue_date', 'verification_url', 
            'created_at'
        ]


# ============================================================================
# DASHBOARD VE ÖZET SERİALİZERLARI
# ============================================================================

class OnlineCourseListSerializer(serializers.ModelSerializer):
    """
    Online kurs listesi için özet serializer
    Kart görünümü için gerekli bilgiler
    """
    modules_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'description', 'department',
            'level', 'estimated_duration_hours', 'thumbnail',
            'modules_count', 'lessons_count', 'enrolled_count', 'status'
        ]
    
    def get_modules_count(self, obj):
        """Modül sayısı"""
        return obj.modules.filter(is_active=True).count()
    
    def get_lessons_count(self, obj):
        """Toplam ders sayısı"""
        return Lesson.objects.filter(
            module__course=obj,
            module__is_active=True,
            is_mandatory=True
        ).count()
    
    def get_enrolled_count(self, obj):
        """Kayıtlı öğrenci sayısı"""
        return obj.course_enrollments.filter(status='active').count()


class OnlineCourseDetailSerializer(serializers.ModelSerializer):
    """
    Online kurs detay serializer
    Tüm modüller ve dersler dahil
    """
    modules = CourseModuleSerializer(many=True, read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()
    has_exam = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'code', 'name', 'description', 'department', 'level',
            'estimated_duration_hours', 'thumbnail', 'course_type',
            'is_self_paced', 'status', 'modules', 'enrollment_status',
            'total_duration', 'lessons_count', 'has_exam'
        ]
    
    def get_enrollment_status(self, obj):
        """Kullanıcının bu kurstaki kayıt durumu"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                student = request.user.student
                enrollment = CourseEnrollment.objects.get(
                    student=student,
                    course=obj
                )
                return {
                    'enrolled': True,
                    'enrollment_id': enrollment.id,
                    'progress': enrollment.progress_percentage,
                    'status': enrollment.status,
                }
            except (Student.DoesNotExist, CourseEnrollment.DoesNotExist):
                return {'enrolled': False}
        return {'enrolled': False}
    
    def get_total_duration(self, obj):
        """Toplam video süresi (dakika)"""
        total_seconds = Lesson.objects.filter(
            module__course=obj,
            module__is_active=True
        ).aggregate(total=Sum('video_duration'))['total'] or 0
        return total_seconds // 60
    
    def get_lessons_count(self, obj):
        """Toplam ders sayısı"""
        return Lesson.objects.filter(
            module__course=obj,
            module__is_active=True,
            is_mandatory=True
        ).count()
    
    def get_has_exam(self, obj):
        """Final sınavı var mı?"""
        return hasattr(obj, 'final_exam') and obj.final_exam.is_active


class StudentDashboardSerializer(serializers.Serializer):
    """
    Öğrenci dashboard serializer
    Tüm aktif ve tamamlanan kurslar
    """
    active_courses = serializers.ListField(child=serializers.DictField())
    completed_courses = CourseEnrollmentSerializer(many=True)
    total_active = serializers.IntegerField()
    total_completed = serializers.IntegerField()


# ============================================================================
# UPDATE SERİALİZERLARI (POST/PUT için)
# ============================================================================

class UpdateVideoProgressSerializer(serializers.Serializer):
    """Video ilerleme güncelleme serializer"""
    watched_duration = serializers.IntegerField(min_value=0)
    
    def validate_watched_duration(self, value):
        """İzlenen süre video süresinden fazla olamaz"""
        lesson = self.context.get('lesson')
        if lesson and lesson.video_duration > 0:
            if value > lesson.video_duration + 10:  # 10 saniye tolerans
                raise serializers.ValidationError(
                    'İzlenen süre video süresinden fazla olamaz'
                )
        return value


class SubmitOptionalAssignmentSerializer(serializers.Serializer):
    """Opsiyonel ödev gönderme serializer"""
    assignment_file = serializers.FileField()
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class SubmitExamSerializer(serializers.Serializer):
    """Sınav cevapları gönderme serializer"""
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    def validate_answers(self, value):
        """Cevaplar formatını kontrol et"""
        # Format: [{'question_id': 1, 'choice_id': 3}, ...]
        for answer in value:
            if 'question_id' not in answer or 'choice_id' not in answer:
                raise serializers.ValidationError(
                    'Her cevap question_id ve choice_id içermelidir'
                )
        return value
