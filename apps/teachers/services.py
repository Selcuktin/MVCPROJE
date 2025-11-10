"""
Service Layer: Business logic and data processing operations.
Bu dosya öğretmen işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Teacher
from apps.courses.models import CourseGroup, Enrollment


class TeacherService:
    """Teacher business logic service"""
    
    def get_filtered_teachers(self, filters):
        """Get teachers with applied filters"""
        queryset = Teacher.objects.select_related().prefetch_related('course_groups__course')
        
        if filters.get('search'):
            queryset = queryset.filter(
                Q(first_name__icontains=filters['search']) |
                Q(last_name__icontains=filters['search']) |
                Q(tc_no__icontains=filters['search']) |
                Q(email__icontains=filters['search']) |
                Q(department__icontains=filters['search'])
            )
        
        if filters.get('department'):
            queryset = queryset.filter(department__icontains=filters['department'])
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        return queryset.order_by('department', 'first_name', 'last_name')
    
    def get_teacher_detail(self, teacher_id):
        """Get teacher detail with related data"""
        teacher = Teacher.objects.get(id=teacher_id)
        
        # Get teacher's course groups
        course_groups = CourseGroup.objects.filter(
            teacher=teacher
        ).select_related('course').prefetch_related('enrollments')
        
        return {
            'teacher': teacher,
            'course_groups': course_groups
        }
    
    def get_teacher_dashboard_data(self, user):
        """Get dashboard data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Get teacher's course groups
            teacher_course_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            
            # Calculate total students
            total_students = 0
            for group in teacher_course_groups:
                total_students += group.enrollments.filter(status='enrolled').count()
            
            # Assignments and announcements removed - return empty lists
            recent_assignments = []
            recent_announcements = []
            
            return {
                'teacher': teacher,
                'teacher_courses': teacher_course_groups,
                'total_students': total_students,
                'recent_assignments': recent_assignments,
                'recent_announcements': recent_announcements,
                'course_groups': teacher_course_groups,
                'now': timezone.now()
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_courses_data(self, user):
        """Get courses data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            course_groups = CourseGroup.objects.filter(
                teacher=teacher, 
                status='active'
            ).select_related('course').order_by('course__code')
            
            return {
                'teacher': teacher,
                'course_groups': course_groups
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_students_data(self, user):
        """Get students data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Get students from teacher's course groups
            teacher_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            students = []
            for group in teacher_groups:
                group_students = Enrollment.objects.filter(
                    group=group, 
                    status='enrolled'
                ).select_related('student')
                for enrollment in group_students:
                    if enrollment.student not in students:
                        students.append(enrollment.student)
            
            return {
                'teacher': teacher,
                'students': students
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_assignments_data(self, user):
        """Get assignments data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Assignments removed - return empty list
            assignments = []
            
            return {
                'teacher': teacher,
                'assignments': assignments
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_announcements_data(self, user):
        """Get announcements data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Announcements removed - return empty list
            announcements = []
            
            return {
                'teacher': teacher,
                'announcements': announcements
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def create_teacher(self, form_data):
        """Create new teacher"""
        teacher = Teacher.objects.create(**form_data)
        return teacher
    
    def update_teacher(self, teacher_id, form_data):
        """Update existing teacher"""
        teacher = Teacher.objects.get(id=teacher_id)
        for key, value in form_data.items():
            setattr(teacher, key, value)
        teacher.save()
        return teacher
    
    def delete_teacher(self, teacher_id):
        """Delete teacher (soft delete)"""
        teacher = Teacher.objects.get(id=teacher_id)
        teacher.status = 'inactive'
        teacher.save()
        return True
    
    def get_teacher_statistics(self, teacher):
        """Get statistics for a specific teacher"""
        course_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
        
        # Calculate total students across all course groups
        total_students = 0
        for group in course_groups:
            total_students += group.enrollments.filter(status='enrolled').count()
        
        # Assignments and announcements removed - return zeros
        total_assignments = 0
        
        # Get announcement statistics
        total_announcements = 0
        
        return {
            'total_courses': course_groups.count(),
            'total_students': total_students,
            'total_assignments': total_assignments,
            'total_announcements': total_announcements
        }