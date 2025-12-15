"""
Enrollment Service Layer
Business logic for enrollment operations
"""
from django.db import transaction
from django.utils import timezone
from django.db.models import Q

from .models import EnrollmentMethod, EnrollmentRule
from apps.courses.models import Enrollment, CourseGroup
from apps.students.models import Student
from apps.academic.models import AcademicTerm


class EnrollmentService:
    """Service for enrollment operations"""
    
    def can_student_enroll(self, student, course_group, enrollment_key=None):
        """
        Check if student can enroll in a course group
        Returns: {'can_enroll': bool, 'messages': [str], 'method': EnrollmentMethod}
        """
        messages = []
        
        # Check if already enrolled
        if Enrollment.objects.filter(
            student=student,
            group=course_group,
            status='enrolled'
        ).exists():
            return {
                'can_enroll': False,
                'messages': ['Bu derse zaten kayıtlısınız'],
                'method': None
            }
        
        # Get active enrollment methods
        methods = EnrollmentMethod.objects.filter(
            course_group=course_group,
            is_enabled=True
        )
        
        if not methods.exists():
            return {
                'can_enroll': False,
                'messages': ['Bu ders için kayıt yöntemi tanımlanmamış'],
                'method': None
            }
        
        # Try self or key enrollment
        suitable_method = None
        for method in methods:
            if method.method_type in ['self', 'key']:
                can_enroll, msg = method.can_enroll(student, key=enrollment_key)
                if can_enroll:
                    suitable_method = method
                    break
                else:
                    messages.append(msg)
        
        if not suitable_method:
            return {
                'can_enroll': False,
                'messages': messages or ['Kayıt yapamazsınız'],
                'method': None
            }
        
        # Check enrollment rules
        rules = EnrollmentRule.objects.filter(
            course_group=course_group,
            is_active=True
        )
        
        for rule in rules:
            passed, msg = rule.check_rule(student)
            if not passed:
                messages.append(msg)
                return {
                    'can_enroll': False,
                    'messages': messages,
                    'method': suitable_method
                }
        
        return {
            'can_enroll': True,
            'messages': ['Kayıt yapılabilir'],
            'method': suitable_method
        }
    
    @transaction.atomic
    def enroll_student(self, student, course_group, enrollment_key=None, enrolled_by=None):
        """
        Enroll a student in a course group
        Returns: {'success': bool, 'enrollment': Enrollment, 'message': str}
        """
        # Check if can enroll
        check_result = self.can_student_enroll(student, course_group, enrollment_key)
        
        if not check_result['can_enroll']:
            return {
                'success': False,
                'enrollment': None,
                'message': '; '.join(check_result['messages'])
            }
        
        # Create enrollment
        try:
            enrollment = Enrollment.objects.create(
                student=student,
                group=course_group,
                status='enrolled',
                enrollment_date=timezone.now()
            )
            
            return {
                'success': True,
                'enrollment': enrollment,
                'message': 'Kayıt başarılı'
            }
        except Exception as e:
            return {
                'success': False,
                'enrollment': None,
                'message': f'Kayıt hatası: {str(e)}'
            }
    
    def get_available_courses_for_student(self, student, academic_term=None):
        """
        Get courses available for student enrollment
        """
        if not academic_term:
            academic_term = AcademicTerm.get_active_term()
        
        if not academic_term:
            return []
        
        # Get course groups with active self/key enrollment
        course_groups = CourseGroup.objects.filter(
            academic_term=academic_term,
            status='active',
            enrollment_methods__is_enabled=True,
            enrollment_methods__method_type__in=['self', 'key']
        ).distinct().select_related('course', 'teacher')
        
        # Filter out already enrolled courses
        enrolled_groups = Enrollment.objects.filter(
            student=student,
            status='enrolled'
        ).values_list('group_id', flat=True)
        
        course_groups = course_groups.exclude(id__in=enrolled_groups)
        
        # Build course list with enrollment info
        available_courses = []
        for group in course_groups:
            methods = group.enrollment_methods.filter(
                is_enabled=True,
                method_type__in=['self', 'key']
            )
            
            for method in methods:
                if method.is_enrollment_open:
                    available_courses.append({
                        'group': group,
                        'method': method,
                        'has_capacity': method.has_capacity,
                        'requires_key': method.method_type == 'key'
                    })
                    break
        
        return available_courses
    
    @transaction.atomic
    def drop_enrollment(self, enrollment_id, student):
        """
        Drop an enrollment (student withdraws from course)
        Returns: {'success': bool, 'message': str}
        """
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id, student=student)
        except Enrollment.DoesNotExist:
            return {
                'success': False,
                'message': 'Kayıt bulunamadı'
            }
        
        # Check if enrollment is active
        if enrollment.status != 'enrolled':
            return {
                'success': False,
                'message': 'Bu kayıt aktif değil'
            }
        
        # Check if drop is allowed
        method = EnrollmentMethod.objects.filter(
            course_group=enrollment.group,
            is_enabled=True,
            method_type__in=['self', 'key'],
            allow_self_unenroll=True
        ).first()
        
        if not method:
            return {
                'success': False,
                'message': 'Bu dersi bırakamazsınız (izin yok)'
            }
        
        # Update enrollment status
        enrollment.status = 'dropped'
        enrollment.save()
        
        return {
            'success': True,
            'message': 'Ders bırakıldı'
        }
    
    def get_student_enrollments(self, student, academic_term=None):
        """
        Get student's enrollments for a term
        """
        query = Enrollment.objects.filter(student=student)
        
        if academic_term:
            query = query.filter(group__academic_term=academic_term)
        
        return query.select_related(
            'group__course',
            'group__teacher',
            'group__academic_term'
        ).order_by('-enrollment_date')
    
    def get_enrollment_statistics(self, course_group):
        """
        Get enrollment statistics for a course group
        """
        enrollments = Enrollment.objects.filter(group=course_group)
        
        total = enrollments.count()
        enrolled = enrollments.filter(status='enrolled').count()
        dropped = enrollments.filter(status='dropped').count()
        completed = enrollments.filter(status='completed').count()
        
        methods = EnrollmentMethod.objects.filter(course_group=course_group)
        max_capacity = methods.filter(max_students__isnull=False).first()
        max_students = max_capacity.max_students if max_capacity else None
        
        return {
            'total_enrollments': total,
            'currently_enrolled': enrolled,
            'dropped': dropped,
            'completed': completed,
            'max_students': max_students,
            'capacity_percentage': (enrolled / max_students * 100) if max_students else None
        }
