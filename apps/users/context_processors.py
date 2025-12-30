"""
Context processors for users app
"""
from django.utils import timezone
from datetime import timedelta
from .models import NotificationStatus
from apps.courses.models import Assignment, Announcement


def notifications_context(request):
    """Add notification count and recent notifications to all templates"""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0, 
            'navbar_notifications': [],
            'active_quizzes_sidebar': []
        }
    
    try:
        # Get user type
        user_type = 'student'
        if hasattr(request.user, 'userprofile'):
            user_type = request.user.userprofile.user_type
        
        unread_count = 0
        active_quizzes_sidebar = []
        
        if user_type == 'student':
            try:
                from apps.students.models import Student
                from apps.quiz.models import Quiz
                from apps.courses.models import Enrollment
                
                student = Student.objects.get(user=request.user)
                
                # Get active quizzes for sidebar
                enrollments = Enrollment.objects.filter(
                    student=student,
                    status='enrolled'
                ).values_list('group_id', flat=True).distinct()
                
                now = timezone.now()
                active_quizzes_sidebar = Quiz.objects.filter(
                    course_group_id__in=enrollments,
                    is_active=True,
                    start_time__lte=now,
                    end_time__gte=now
                ).select_related('course_group__course').order_by('start_time')[:5]
                
                # Get assignments for student's enrolled courses
                assignments = Assignment.objects.filter(
                    group__enrollments__student=student,
                    status='active',
                    create_date__gte=timezone.now() - timedelta(days=30)
                )
                
                # Get announcements
                announcements = Announcement.objects.filter(
                    group__enrollments__student=student,
                    status='active',
                    create_date__gte=timezone.now() - timedelta(days=30)
                )
                
                # Count unread notifications
                for assignment in assignments:
                    notification_id = f'assignment_{assignment.id}'
                    try:
                        notification_status = NotificationStatus.objects.get(
                            user=request.user,
                            notification_id=notification_id
                        )
                        if not notification_status.is_read:
                            unread_count += 1
                    except NotificationStatus.DoesNotExist:
                        unread_count += 1  # New notification, not read yet
                
                for announcement in announcements:
                    notification_id = f'announcement_{announcement.id}'
                    try:
                        notification_status = NotificationStatus.objects.get(
                            user=request.user,
                            notification_id=notification_id
                        )
                        if not notification_status.is_read:
                            unread_count += 1
                    except NotificationStatus.DoesNotExist:
                        unread_count += 1  # New notification, not read yet
                        
            except Student.DoesNotExist:
                pass
                
        elif user_type == 'teacher':
            try:
                from apps.teachers.models import Teacher
                teacher = Teacher.objects.get(user=request.user)
                
                # Get teacher's recent assignments
                assignments = Assignment.objects.filter(
                    group__teacher=teacher,
                    create_date__gte=timezone.now() - timedelta(days=30)
                )
                
                # Count unread notifications
                for assignment in assignments:
                    notification_id = f'assignment_{assignment.id}'
                    try:
                        notification_status = NotificationStatus.objects.get(
                            user=request.user,
                            notification_id=notification_id
                        )
                        if not notification_status.is_read:
                            unread_count += 1
                    except NotificationStatus.DoesNotExist:
                        unread_count += 1  # New notification, not read yet
                        
            except Teacher.DoesNotExist:
                pass
        
        # Get recent notifications for navbar (last 4)
        from .services import UserService
        service = UserService()
        navbar_notifications = service.get_navbar_notifications(request.user, limit=4)
        
        return {
            'unread_notifications_count': unread_count,
            'navbar_notifications': navbar_notifications,
            'active_quizzes_sidebar': active_quizzes_sidebar
        }
        
    except Exception as e:
        # Fallback in case of any error
        return {
            'unread_notifications_count': 0, 
            'navbar_notifications': [],
            'active_quizzes_sidebar': []
        }