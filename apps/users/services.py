"""
Service Layer: Business logic and data processing operations.
Bu dosya kullanıcı işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth import login
from datetime import timedelta, date
import calendar

from .models import User, UserProfile, NotificationStatus
from apps.courses.models import Course, Enrollment
from apps.students.models import Student
from apps.teachers.models import Teacher


class UserService:
    """User business logic service"""
    
    def get_home_statistics(self):
        """Get statistics for home page"""
        return {
            'total_courses': Course.objects.filter(status='active').count(),
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count(),
            'total_enrollments': Enrollment.objects.filter(status='enrolled').count()
        }
    
    def create_user_with_profile(self, form_data, user_type='student'):
        """Create user with profile"""
        user = User.objects.create_user(**form_data)
        UserProfile.objects.create(
            user=user,
            user_type=user_type
        )
        return user
    
    def get_user_redirect_url(self, user):
        """Get redirect URL based on user type"""
        if hasattr(user, 'userprofile'):
            if user.userprofile.user_type == 'student':
                return 'students:dashboard'
            elif user.userprofile.user_type == 'teacher':
                return 'teachers:dashboard'
        return 'home'
    
    def get_control_panel_statistics(self, user):
        """Get statistics for control panel based on user type - DISABLED"""
        # Control panel has been removed
        return {
            'total_courses': 0,
            'total_assignments': 0,
            'total_students': 0,
            'total_teachers': 0
        }
    
    def _get_student_statistics(self, user):
        """Get statistics for student - DISABLED"""
        return {
            'total_courses': 0,
            'total_assignments': 0,
            'total_students': 0,
            'total_teachers': 0
        }
    
    def _get_teacher_statistics(self, user):
        """Get statistics for teacher - DISABLED"""
        return {
            'total_courses': 0,
            'total_assignments': 0,
            'total_students': 0,
            'total_teachers': 0
        }
    
    def _get_admin_statistics(self):
        """Get statistics for admin - DISABLED"""
        return {
            'total_courses': Course.objects.filter(status='active').count(),
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count(),
            'total_assignments': 0  # Assignments removed
        }
    
    def get_recent_activities(self, user):
        """Get recent activities for user - DISABLED"""
        # Recent activities removed (assignments/announcements)
        return []
    
    def _get_student_activities(self, user):
        """Get recent activities for student - DISABLED"""
        return []
    
    def _get_teacher_activities(self, user):
        """Get recent activities for teacher - DISABLED"""
        return []
    
    def get_calendar_data(self, user, year, month):
        """Get calendar data for specific month - DISABLED"""
        # Calendar data removed (assignments)
        try:
            cal = calendar.monthcalendar(year, month)
            calendar_days = []
            today = date.today()
            
            for week in cal:
                for day in week:
                    if day == 0:
                        calendar_days.append({
                            'number': '', 
                            'is_today': False, 
                            'has_event': False,
                            'assignment_title': '',
                            'course_name': ''
                        })
                    else:
                        is_today = (day == today.day and month == today.month and year == today.year)
                        calendar_days.append({
                            'number': day,
                            'is_today': is_today,
                            'has_event': False,
                            'assignment_title': '',
                            'course_name': '',
                            'assignment_id': None
                        })
            
            return {'calendar_days': calendar_days}
        except Exception as e:
            return {'calendar_days': [], 'error': str(e)}
    
    def _get_student_calendar_assignments(self, user, month_start, month_end):
        """Get calendar assignments for student - DISABLED"""
        return {}
    
    def _get_teacher_calendar_assignments(self, user, month_start, month_end):
        """Get calendar assignments for teacher - DISABLED"""
        return {}
    
    def get_notifications_data(self, user):
        """Get notifications for user"""
        user_type = 'student'
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
        
        notifications = []
        
        # Only welcome notification since assignments/announcements are removed
        notifications = [{
            'id': 1,
            'title': 'Hoş Geldiniz',
            'message': 'Kurs yönetim sistemine hoş geldiniz! Bildirimleriniz burada görünecek.',
            'time': '1 gün önce',
            'type': 'welcome',
            'is_read': False,
            'icon': 'fas fa-info-circle',
            'color': 'info'
        }]
        
        return {
            'notifications': notifications,
            'unread_count': 0,
            'total_count': len(notifications)
        }
    
    def _get_student_notifications(self, user):
        """Get notifications for student - DISABLED"""
        return []
    
    def _get_teacher_notifications(self, user):
        """Get notifications for teacher - DISABLED"""
        return []
    
    def mark_notification_as_read(self, user, notification_id):
        """Mark notification as read"""
        try:
            notification_status, created = NotificationStatus.objects.get_or_create(
                user=user,
                notification_id=notification_id,
                defaults={
                    'notification_type': notification_id.split('_')[0],  # Extract type from ID
                    'is_read': True,
                    'read_at': timezone.now()
                }
            )
            
            if not created and not notification_status.is_read:
                notification_status.is_read = True
                notification_status.read_at = timezone.now()
                notification_status.save()
            
            return True
        except Exception:
            return False