"""
Service Layer: Business logic and data processing operations.
Bu dosya öğrenci işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Student
from apps.courses.models import Course, Enrollment, Assignment, Announcement, Submission
from apps.notes.models import Note
from apps.gradebook.models import GradeCategory




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
        
        # Get student's enrollments and remove duplicates
        all_enrollments = Enrollment.objects.filter(
            student=student, 
            status='enrolled'
        ).select_related('group__course', 'group__teacher').order_by('group__course__code', 'group__semester')
        
        # Remove duplicates: keep only one enrollment per course code + semester
        seen = set()
        enrollments = []
        for enrollment in all_enrollments:
            key = (enrollment.group.course.code, enrollment.group.semester)
            if key not in seen:
                seen.add(key)
                enrollments.append(enrollment)
        
        # Get student's assignments
        assignments = Assignment.objects.filter(
            group__enrollments__student=student,
            status='active'
        ).select_related('group__course').order_by('-create_date')

        # Get student's submissions (for stats)
        submissions = Submission.objects.filter(student=student)

        # Collect notes per course and exam type
        notes = Note.objects.filter(student=student.user)
        notes_by_course = {}
        for note in notes:
            course_id = note.course_id
            notes_by_course.setdefault(course_id, {})[note.exam_type] = note

        # Attach course-specific notes to each enrollment for easy template access
        for enrollment in enrollments:
            enrollment.course_notes = notes_by_course.get(enrollment.group.course.id, {})
        
        return {
            'student': student,
            'enrollments': enrollments,
            'assignments': assignments,
            'submissions': submissions,
            'notes_by_course': notes_by_course,
            'total_courses': len(enrollments),
            'total_assignments': assignments.count(),
            'notes_count': notes.count(),
            'submissions_count': submissions.count(),
        }
    
    def get_student_dashboard_data(self, user):
        """Get dashboard data for student"""
        try:
            student = Student.objects.get(user=user)
            
            # Get enrollments and remove duplicates by course code + semester
            all_enrollments = Enrollment.objects.filter(
                student=student, 
                status='enrolled'
            ).select_related(
                'group__course', 
                'group__teacher'
            ).order_by('group__course__code', 'group__semester')
            
            # Remove duplicates: keep only one enrollment per course code + semester
            seen = set()
            enrollments = []
            for enrollment in all_enrollments:
                key = (enrollment.group.course.code, enrollment.group.semester)
                if key not in seen:
                    seen.add(key)
                    enrollments.append(enrollment)
            
            enrolled_groups = [enrollment.group for enrollment in enrollments]
            
            # Get recent assignments (son 5 ödev)
            recent_assignments = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).select_related('group__course').order_by('-create_date')[:5]
            
            # Get recent announcements (son 5 duyuru)
            recent_announcements = Announcement.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).select_related('group__course').order_by('-create_date')[:5]
            
            # Get pending submissions count (teslim edilmemiş ve süresi dolmamış ödevler)
            from django.utils import timezone
            now = timezone.now()
            
            # Öğrencinin teslim ettiği ödevler
            submitted_assignment_ids = Submission.objects.filter(
                student=student
            ).values_list('assignment_id', flat=True)
            
            # Aktif, süresi dolmamış ve teslim edilmemiş ödevler
            pending_submissions = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active',
                due_date__gte=now  # Sadece süresi dolmamış ödevler
            ).exclude(
                id__in=submitted_assignment_ids
            ).count()
            
            # Get grades count (not kategorileri)
            from apps.notes.models import Note
            grades_count = Note.objects.filter(
                student=user
            ).count()
            
            # Get GPA (ortalama)
            notes = Note.objects.filter(student=user)
            total_score = 0
            count = 0
            for note in notes:
                try:
                    score = float(note.score)
                    total_score += score
                    count += 1
                except (ValueError, TypeError):
                    pass
            
            gpa = round(total_score / count, 2) if count > 0 else 0.0
            
            # Get active quiz count for enrolled courses
            from apps.quiz.models import Quiz
            now = timezone.now()
            
            # Get all quizzes for enrolled groups
            all_quizzes = Quiz.objects.filter(
                course_group__in=enrolled_groups,
                is_active=True
            )
            
            # Filter by time range
            active_quizzes_count = sum(1 for q in all_quizzes if q.is_available)
            
            # Get active quizzes for sidebar (son 5 aktif sınav)
            active_quizzes_sidebar = [q for q in all_quizzes if q.is_available][:5]
            
            return {
                'student': student,
                'enrollments': enrollments,
                'enrolled_count': len(enrollments),
                'recent_assignments': recent_assignments,
                'recent_announcements': recent_announcements,
                'pending_submissions': pending_submissions,
                'grades_count': grades_count,
                'gpa': gpa,
                'active_quizzes_count': active_quizzes_count,
                'active_quizzes_sidebar': active_quizzes_sidebar,
                'now': timezone.now()
            }
            
        except Student.DoesNotExist:
            return {'error': 'Öğrenci profili bulunamadı.'}
    
    def get_student_courses_data(self, user):
        """Get courses data for student"""
        try:
            student = Student.objects.get(user=user)
            
            # Get enrollments (show active + completed) with related data
            enrollments_qs = Enrollment.objects.filter(
                student=student,
                status__in=['enrolled', 'completed']
            ).select_related(
                'group__course',
                'group__teacher'
            ).order_by('group__course__code', '-id')

            # De-dupe by course (students should not see same course twice even if multiple groups exist)
            enrollments = []
            seen_course_ids = set()
            for e in enrollments_qs:
                course_id = getattr(e.group, 'course_id', None)
                if course_id and course_id in seen_course_ids:
                    continue
                if course_id:
                    seen_course_ids.add(course_id)
                enrollments.append(e)

            active_enrollments_count = len([e for e in enrollments if e.status == 'enrolled'])
            completed_enrollments_count = len([e for e in enrollments if e.status == 'completed'])

            total_credits = 0
            for e in enrollments:
                try:
                    total_credits += int(getattr(e.group.course, 'credits', 0) or 0)
                except (TypeError, ValueError):
                    pass
            
            # Get available course groups (not enrolled)
            enrolled_group_ids = [e.group_id for e in enrollments]
            from apps.courses.models import CourseGroup
            available_groups = CourseGroup.objects.filter(
                status='active'
            ).exclude(id__in=enrolled_group_ids).select_related('course', 'teacher')
            
            return {
                'student': student,
                'enrollments': enrollments,
                'available_groups': available_groups,
                'active_enrollments_count': active_enrollments_count,
                'completed_enrollments_count': completed_enrollments_count,
                'total_credits': total_credits,
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
        """Delete student (soft delete) with dependency check"""
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return {'success': False, 'error': 'Öğrenci bulunamadı'}
        
        # Check for active enrollments
        active_enrollments = Enrollment.objects.filter(
            student=student,
            status='enrolled'
        ).count()
        
        if active_enrollments > 0:
            return {
                'success': False,
                'error': f'Bu öğrencinin {active_enrollments} aktif ders kaydı var. Önce kayıtları kaldırın.'
            }
        
        student.status = 'inactive'
        student.save()
        return {'success': True}
    
    def get_student_statistics(self, student):
        """Get statistics for a specific student"""
        enrollments = Enrollment.objects.filter(student=student, status='enrolled')
        
        # Calculate GPA - convert letter grades to numeric
        numeric_grades = [
            letter_grade_to_numeric(e.grade) 
            for e in enrollments 
            if e.grade and e.grade != 'NA' and letter_grade_to_numeric(e.grade) is not None
        ]
        gpa = sum(numeric_grades) / len(numeric_grades) if numeric_grades else 0
        
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