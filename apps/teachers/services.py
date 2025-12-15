"""
Service Layer: Business logic and data processing operations.
Bu dosya öğretmen işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Teacher
from apps.courses.models import CourseGroup, Assignment, Announcement, Enrollment, Submission
from apps.students.models import Student


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
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen bulunamadı'}
        
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
            
            # Get teacher's course groups and remove duplicates (course+semester)
            all_course_groups = CourseGroup.objects.filter(
                teacher=teacher, 
                status='active'
            ).select_related('course').order_by('course__code', 'semester', 'name')
            
            seen = set()
            teacher_course_groups = []
            for group in all_course_groups:
                key = (group.course.code, group.semester)
                if key not in seen:
                    seen.add(key)
                    teacher_course_groups.append(group)
            
            # Calculate total students
            total_students = 0
            for group in teacher_course_groups:
                total_students += group.enrollments.filter(status='enrolled').count()
            
            # Get recent assignments and announcements
            recent_assignments = Assignment.objects.filter(
                group__in=teacher_course_groups
            ).select_related('group__course').order_by('-create_date')
            
            recent_announcements = Announcement.objects.filter(
                group__in=teacher_course_groups
            ).select_related('group__course').order_by('-create_date')
            
            # Pending assignments to grade (with ungraded submissions)
            from apps.courses.models import Submission
            pending_grading_queryset = Assignment.objects.filter(
                group__teacher=teacher,
                status__in=['active', 'published']
            ).annotate(
                ungraded_count=Count('submissions', filter=Q(submissions__score__isnull=True))
            ).filter(ungraded_count__gt=0).select_related('group__course')
            
            pending_grading_count = pending_grading_queryset.count()
            
            pending_assignments_list = list(pending_grading_queryset[:5])
            
            # Active quizzes
            try:
                from apps.quiz.models import Quiz
                active_quizzes = Quiz.objects.filter(
                    course_group__teacher=teacher,
                    is_active=True,
                    start_time__lte=timezone.now(),
                    end_time__gte=timezone.now()
                ).select_related('course_group__course')
                active_quizzes_count = active_quizzes.count()
            except Exception:
                active_quizzes = []
                active_quizzes_count = 0
            
            # Unread messages
            try:
                from apps.forum.models import DirectMessage
                unread_messages = DirectMessage.objects.filter(
                    recipient=teacher.user,
                    is_read=False
                ).count()
            except Exception:
                unread_messages = 0
            
            # Annotate courses with student count
            group_ids = [g.id for g in teacher_course_groups]
            teacher_course_groups_queryset = CourseGroup.objects.filter(id__in=group_ids)
            teacher_course_groups_annotated = teacher_course_groups_queryset.annotate(
                student_count=Count('enrollments', filter=Q(enrollments__status='enrolled'))
            )
            
            return {
                'teacher': teacher,
                'my_courses': teacher_course_groups_annotated,
                'my_courses_count': len(teacher_course_groups),
                'teacher_courses': teacher_course_groups_queryset,
                'total_students': total_students,
                'pending_grading': pending_grading_count,
                'pending_assignments': pending_assignments_list,
                'active_quizzes': active_quizzes,
                'active_quizzes_count': active_quizzes_count,
                'unread_messages': unread_messages,
                'recent_assignments': list(recent_assignments[:5]),
                'recent_announcements': list(recent_announcements[:5]),
                'course_groups': teacher_course_groups_queryset,
                'now': timezone.now()
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_courses_data(self, user):
        """Get courses data for teacher - show each course only once (by code)"""
        try:
            teacher = Teacher.objects.get(user=user)
            course_groups = CourseGroup.objects.filter(
                teacher=teacher, 
                status='active'
            ).select_related('course').order_by('course__code', 'semester', 'name')
            
            # Remove duplicates: keep only one group per course code (ignore semester)
            seen = set()
            unique_groups = []
            for group in course_groups:
                key = group.course.code  # sadece ders koduna göre eşsizleştir
                if key not in seen:
                    seen.add(key)
                    unique_groups.append(group)
            
            # student_count anotasyonu
            group_ids = [g.id for g in unique_groups]
            annotated_groups = CourseGroup.objects.filter(id__in=group_ids).annotate(
                student_count=Count('enrollments', filter=Q(enrollments__status='enrolled'))
            )
            
            return {
                'teacher': teacher,
                'course_groups': annotated_groups,
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğretmen profili bulunamadı.'}
    
    def get_teacher_students_data(self, user):
        """Get students data for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Filtre: sadece bu öğretmenin aktif ders grupları
            teacher_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            
            # Aktif derslere kayıtlı öğrenciler (distinct)
            students_qs = Student.objects.filter(
                enrollments__group__in=teacher_groups,
                enrollments__status='enrolled'
            ).distinct()
            
            # Öğrenci kartları için zengin veri
            student_data = []
            for student in students_qs:
                enrollments = Enrollment.objects.filter(
                    student=student,
                    group__in=teacher_groups,
                    status='enrolled'
                ).select_related('group__course')
                
                # Get completed assignments (with submissions)
                completed_assignments = Submission.objects.filter(
                    student=student,
                    assignment__group__in=teacher_groups,
                    status__in=['submitted', 'graded']
                ).count()
                
                # Get pending assignments (active assignments without submissions)
                active_assignments = Assignment.objects.filter(
                    group__in=teacher_groups,
                    status='active',
                    due_date__gte=timezone.now()
                )
                pending_assignments = active_assignments.exclude(
                    submissions__student=student
                ).count()
                
                # Calculate average grade from enrollments
                from apps.gradebook.models import Grade
                grades = Grade.objects.filter(
                    enrollment__student=student,
                    enrollment__group__in=teacher_groups
                ).exclude(score__isnull=True)
                
                average_grade = None
                if grades.exists():
                    total_score = sum(float(g.score) for g in grades if g.score)
                    average_grade = total_score / grades.count() if grades.count() > 0 else None
                
                student_data.append({
                    'student': student,
                    'enrollments': enrollments,
                    'completed_assignments': completed_assignments,
                    'pending_assignments': pending_assignments,
                    'average_grade': average_grade,
                })
            
            # Calculate statistics
            total_students = len(student_data)
            my_courses_count = teacher_groups.count()
            active_assignments_count = Assignment.objects.filter(
                group__in=teacher_groups,
                status='active'
            ).count()
            
            # Calculate class average
            all_grades = []
            for sd in student_data:
                if sd['average_grade'] is not None:
                    all_grades.append(sd['average_grade'])
            class_average = sum(all_grades) / len(all_grades) if all_grades else 0
            
            return {
                'students': student_data,
                'total_students': total_students,
                'my_courses': my_courses_count,
                'active_assignments': active_assignments_count,
                'class_average': class_average,
                'my_course_groups': teacher_groups,
            }
            
        except Teacher.DoesNotExist:
            return {'error': 'Öğrenci verileri alınamadı.'}
