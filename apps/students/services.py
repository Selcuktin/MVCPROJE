"""
Service Layer: Business logic and data processing operations.
Bu dosya öğrenci işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Student
from apps.courses.models import Course, Enrollment, Assignment, Announcement, Submission


class StudentService:
    """Student business logic service"""
    
    def get_filtered_students(self, filters):
        """Get students with applied filters"""
        queryset = Student.objects.all()
        
        if filters.get('search'):
            queryset = queryset.filter(
                Q(first_name__icontains=filters['search']) |
                Q(last_name__icontains=filters['search']) |
                Q(school_number__icontains=filters['search']) |
                Q(email__icontains=filters['search'])
            )
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        return queryset.order_by('first_name', 'last_name')
    
    def get_student_detail(self, student_id):
        """Get student detail with related data"""
        student = Student.objects.get(id=student_id)
        
        # Get student's enrollments
        enrollments = Enrollment.objects.filter(
            student=student, 
            status='enrolled'
        ).select_related('group__course', 'group__teacher')
        
        # Get student's assignments
        assignments = Assignment.objects.filter(
            group__enrollments__student=student,
            status='active'
        ).select_related('group__course').order_by('-create_date')
        
        return {
            'student': student,
            'enrollments': enrollments,
            'assignments': assignments,
            'total_courses': enrollments.count(),
            'total_assignments': assignments.count()
        }
    
    def get_student_dashboard_data(self, user):
        """Get dashboard data for student"""
        try:
            student = Student.objects.get(user=user)
            
            # Get enrollments
            enrollments = Enrollment.objects.filter(student=student, status='enrolled')
            enrolled_groups = [enrollment.group for enrollment in enrollments]
            
            # Get recent assignments
            recent_assignments = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).order_by('-create_date')[:5]
            
            # Get recent announcements
            recent_announcements = Announcement.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).order_by('-create_date')[:5]
            
            # Get pending submissions count
            pending_submissions = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active',
                due_date__gte=timezone.now()
            ).exclude(
                submissions__student=student
            ).count()
            
            return {
                'student': student,
                'enrollments': enrollments,
                'recent_assignments': recent_assignments,
                'recent_announcements': recent_announcements,
                'pending_submissions': pending_submissions,
                'now': timezone.now()
            }
            
        except Student.DoesNotExist:
            return {'error': 'Öğrenci profili bulunamadı.'}
    
    def get_student_courses_data(self, user):
        """Get courses data for student"""
        try:
            student = Student.objects.get(user=user)
            
            # Get enrolled course groups
            enrollments = Enrollment.objects.filter(student=student, status='enrolled')
            
            # Get available course groups (not enrolled)
            enrolled_group_ids = enrollments.values_list('group_id', flat=True)
            from apps.courses.models import CourseGroup
            available_groups = CourseGroup.objects.filter(
                status='active'
            ).exclude(id__in=enrolled_group_ids)
            
            return {
                'student': student,
                'enrollments': enrollments,
                'available_groups': available_groups
            }
            
        except Student.DoesNotExist:
            return {'error': 'Öğrenci profili bulunamadı.'}
    
    def create_student(self, form_data):
        """Create new student"""
        student = Student.objects.create(**form_data)
        return student
    
    def update_student(self, student_id, form_data):
        """Update existing student"""
        student = Student.objects.get(id=student_id)
        for key, value in form_data.items():
            setattr(student, key, value)
        student.save()
        return student
    
    def delete_student(self, student_id):
        """Delete student (soft delete)"""
        student = Student.objects.get(id=student_id)
        student.status = 'inactive'
        student.save()
        return True
    
    def get_student_statistics(self, student):
        """Get statistics for a specific student"""
        enrollments = Enrollment.objects.filter(student=student, status='enrolled')
        
        # Calculate GPA
        grades = [e.grade for e in enrollments if e.grade]
        gpa = sum(grades) / len(grades) if grades else 0
        
        # Get assignment statistics
        total_assignments = Assignment.objects.filter(
            group__enrollments__student=student,
            status='active'
        ).count()
        
        completed_assignments = Submission.objects.filter(
            student=student,
            assignment__status='active'
        ).count()
        
        return {
            'total_courses': enrollments.count(),
            'gpa': round(gpa, 2),
            'total_assignments': total_assignments,
            'completed_assignments': completed_assignments,
            'completion_rate': round((completed_assignments / total_assignments * 100), 2) if total_assignments > 0 else 0
        }