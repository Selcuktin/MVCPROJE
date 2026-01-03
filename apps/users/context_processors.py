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
            'active_quizzes_sidebar': [],
            'unread_messages': 0
        }
    
    try:
        # Get user type
        user_type = 'student'
        if hasattr(request.user, 'userprofile'):
            user_type = request.user.userprofile.user_type
        
        active_quizzes_sidebar = []
        
        # Only load active quizzes for student dashboard/quiz pages
        if user_type == 'student' and (request.path.startswith('/students/') or request.path.startswith('/quiz/')):
            try:
                from apps.students.models import Student
                from apps.quiz.models import Quiz
                from apps.courses.models import Enrollment
                
                student = Student.objects.get(user=request.user)
                
                # Get active quizzes - optimized query
                enrollments = Enrollment.objects.filter(
                    student=student,
                    status='enrolled'
                ).values_list('group_id', flat=True)
                
                now = timezone.now()
                active_quizzes_sidebar = Quiz.objects.filter(
                    course_group_id__in=enrollments,
                    is_active=True,
                    start_time__lte=now,
                    end_time__gte=now
                ).select_related('course_group__course').only(
                    'id', 'title', 'start_time', 'end_time',
                    'course_group__course__name', 'course_group__course__code'
                ).order_by('start_time')[:5]
                        
            except Student.DoesNotExist:
                pass
        
        # Get ALL notifications (not just navbar) for accurate count
        from .services import UserService
        service = UserService()
        
        # Get full notification data
        notification_data = service.get_notifications_data(request.user)
        all_notifications = notification_data.get('notifications', [])
        
        # Only show unread notifications in navbar dropdown (limit to 10 for performance)
        navbar_notifications = [n for n in all_notifications if not n.get('is_read', False)][:10]
        
        # Count ALL unread notifications (not just first 10)
        unread_count = notification_data.get('unread_count', 0)
        
        # Get unread messages count
        unread_messages = 0
        try:
            from apps.forum.models import DirectMessage
            unread_messages = DirectMessage.objects.filter(
                recipient=request.user,
                is_read=False
            ).count()
        except Exception:
            pass
        
        return {
            'unread_notifications_count': unread_count,
            'navbar_notifications': navbar_notifications,
            'active_quizzes_sidebar': active_quizzes_sidebar,
            'unread_messages': unread_messages
        }
        
    except Exception as e:
        # Fallback in case of any error
        return {
            'unread_notifications_count': 0, 
            'navbar_notifications': [],
            'active_quizzes_sidebar': [],
            'unread_messages': 0
        }
