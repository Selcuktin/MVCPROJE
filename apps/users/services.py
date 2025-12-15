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
from apps.courses.models import Course, Enrollment, Assignment, Announcement
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
        """Get statistics for control panel based on user type"""
        user_type = 'student'
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
        
        if user_type == 'student':
            return self._get_student_statistics(user)
        elif user_type == 'teacher':
            return self._get_teacher_statistics(user)
        else:
            return self._get_admin_statistics()
    
    def _get_student_statistics(self, user):
        """Get statistics for student"""
        try:
            student = Student.objects.get(user=user)
            total_courses = student.enrollments.filter(status='enrolled').count()
            total_assignments = Assignment.objects.filter(
                group__enrollments__student=student,
                status='active',
                due_date__gt=timezone.now()
            ).count()
        except Student.DoesNotExist:
            total_courses = 0
            total_assignments = 0
        
        return {
            'total_courses': total_courses,
            'total_assignments': total_assignments,
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count()
        }
    
    def _get_teacher_statistics(self, user):
        """Get statistics for teacher"""
        try:
            teacher = Teacher.objects.get(user=user)
            total_courses = teacher.course_groups.filter(status='active').count()
            total_assignments = Assignment.objects.filter(
                group__teacher=teacher,
                status='active'
            ).count()
        except Teacher.DoesNotExist:
            total_courses = 0
            total_assignments = 0
        
        return {
            'total_courses': total_courses,
            'total_assignments': total_assignments,
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count()
        }
    
    def _get_admin_statistics(self):
        """Get statistics for admin"""
        return {
            'total_courses': Course.objects.filter(status='active').count(),
            'total_students': Student.objects.filter(status='active').count(),
            'total_teachers': Teacher.objects.filter(status='active').count(),
            'total_assignments': Assignment.objects.filter(status='active').count()
        }
    
    def get_recent_activities(self, user):
        """Get recent activities for user"""
        user_type = 'student'
        if hasattr(user, 'userprofile'):
            user_type = user.userprofile.user_type
        
        recent_activities = []
        
        if user_type == 'student':
            recent_activities = self._get_student_activities(user)
        elif user_type == 'teacher':
            recent_activities = self._get_teacher_activities(user)
        
        return recent_activities
    
    def _get_student_activities(self, user):
        """Get recent activities for student"""
        from django.urls import reverse
        activities = []
        
        try:
            student = Student.objects.get(user=user)
            
            # Recent assignments
            assignments = Assignment.objects.filter(
                group__enrollments__student=student,
                status='active',
                create_date__gte=timezone.now() - timedelta(days=7)
            ).order_by('-create_date')[:5]
            
            for assignment in assignments:
                time_diff = timezone.now() - assignment.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                activities.append({
                    'title': 'Yeni Ödev Atandı',
                    'description': f'{assignment.group.course.name} - {assignment.title}',
                    'time': time_str,
                    'icon': 'fas fa-tasks',
                    'color': '#667eea',
                    'url': reverse('courses:assignment_detail', kwargs={'pk': assignment.pk})
                })
            
            # Recent announcements
            announcements = Announcement.objects.filter(
                group__enrollments__student=student,
                status='active',
                create_date__gte=timezone.now() - timedelta(days=7)
            ).order_by('-create_date')[:3]
            
            for announcement in announcements:
                time_diff = timezone.now() - announcement.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                activities.append({
                    'title': 'Yeni Duyuru',
                    'description': f'{announcement.group.course.name} - {announcement.title}',
                    'time': time_str,
                    'icon': 'fas fa-bullhorn',
                    'color': '#2ed573',
                    'url': reverse('courses:announcement_detail', kwargs={'pk': announcement.pk})
                })
                
        except Student.DoesNotExist:
            pass
        
        # Sort activities by time (most recent first)
        activities.sort(key=lambda x: x['time'], reverse=False)
        
        return activities[:5]  # Return only 5 most recent
    
    def _get_teacher_activities(self, user):
        """Get recent activities for teacher"""
        from django.urls import reverse
        activities = []
        
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Recent assignments created
            assignments = Assignment.objects.filter(
                group__teacher=teacher,
                create_date__gte=timezone.now() - timedelta(days=7)
            ).order_by('-create_date')[:5]
            
            for assignment in assignments:
                time_diff = timezone.now() - assignment.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                activities.append({
                    'title': 'Ödev Oluşturuldu',
                    'description': f'{assignment.group.course.name} - {assignment.title}',
                    'time': time_str,
                    'icon': 'fas fa-plus-circle',
                    'color': '#2ed573',
                    'url': reverse('courses:assignment_detail', kwargs={'pk': assignment.pk})
                })
            
            # Recent announcements created
            announcements = Announcement.objects.filter(
                group__teacher=teacher,
                create_date__gte=timezone.now() - timedelta(days=7)
            ).order_by('-create_date')[:3]
            
            for announcement in announcements:
                time_diff = timezone.now() - announcement.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                activities.append({
                    'title': 'Duyuru Yayınlandı',
                    'description': f'{announcement.group.course.name} - {announcement.title}',
                    'time': time_str,
                    'icon': 'fas fa-bullhorn',
                    'color': '#ffa502',
                    'url': reverse('courses:announcement_detail', kwargs={'pk': announcement.pk})
                })
                
        except Teacher.DoesNotExist:
            pass
        
        # Sort activities by time (most recent first)
        activities.sort(key=lambda x: x['time'], reverse=False)
        
        return activities[:5]  # Return only 5 most recent
    
    def get_calendar_data(self, user, year, month):
        """Get calendar data for specific month"""
        try:
            cal = calendar.monthcalendar(year, month)
            calendar_days = []
            
            # Get assignments for requested month
            month_start = date(year, month, 1)
            if month == 12:
                month_end = date(year + 1, 1, 1)
            else:
                month_end = date(year, month + 1, 1)
            
            # Get user type
            user_type = 'student'
            if hasattr(user, 'userprofile'):
                user_type = user.userprofile.user_type
            
            assignments_in_month = {}
            if user_type == 'student':
                assignments_in_month = self._get_student_calendar_assignments(user, month_start, month_end)
            elif user_type == 'teacher':
                assignments_in_month = self._get_teacher_calendar_assignments(user, month_start, month_end)
            
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
                        has_event = day in assignments_in_month
                        assignment_title = ''
                        course_name = ''
                        
                        assignment_id = None
                        if has_event and assignments_in_month[day]:
                            # Get first assignment for this day
                            first_assignment = assignments_in_month[day][0]
                            assignment_title = first_assignment['title']
                            course_name = first_assignment['course']
                            assignment_id = first_assignment['id']
                        
                        calendar_days.append({
                            'number': day,
                            'is_today': is_today,
                            'has_event': has_event,
                            'assignment_title': assignment_title,
                            'course_name': course_name,
                            'assignment_id': assignment_id
                        })
            
            return {'calendar_days': calendar_days}
            
        except Exception as e:
            return {'calendar_days': [], 'error': str(e)}
    
    def _get_student_calendar_assignments(self, user, month_start, month_end):
        """Get calendar assignments for student"""
        assignments_in_month = {}
        
        try:
            student = Student.objects.get(user=user)
            assignments = Assignment.objects.filter(
                group__enrollments__student=student,
                status='active',
                due_date__date__gte=month_start,
                due_date__date__lt=month_end
            ).select_related('group__course')
            
            for assignment in assignments:
                day = assignment.due_date.day
                if day not in assignments_in_month:
                    assignments_in_month[day] = []
                assignments_in_month[day].append({
                    'id': assignment.id,
                    'title': assignment.title,
                    'course': assignment.group.course.name
                })
        except Student.DoesNotExist:
            pass
        
        return assignments_in_month
    
    def _get_teacher_calendar_assignments(self, user, month_start, month_end):
        """Get calendar assignments for teacher"""
        assignments_in_month = {}
        
        try:
            teacher = Teacher.objects.get(user=user)
            assignments = Assignment.objects.filter(
                group__teacher=teacher,
                status='active',
                due_date__date__gte=month_start,
                due_date__date__lt=month_end
            ).select_related('group__course')
            
            for assignment in assignments:
                day = assignment.due_date.day
                if day not in assignments_in_month:
                    assignments_in_month[day] = []
                assignments_in_month[day].append({
                    'id': assignment.id,
                    'title': assignment.title,
                    'course': assignment.group.course.name
                })
        except Teacher.DoesNotExist:
            pass
        
        return assignments_in_month
    
    def get_unread_notifications_count(self, user):
        """Get unread notification count only (fast method for AJAX)"""
        data = self.get_notifications_data(user)
        return data.get('unread_count', 0)
    
    def get_navbar_notifications(self, user, limit=4):
        """Get recent notifications for navbar dropdown"""
        data = self.get_notifications_data(user)
        notifications = data.get('notifications', [])
        return notifications[:limit]
    
    def get_notifications_data(self, user):
        """Get notifications for user"""
        user_type = 'student'
        if hasattr(user, 'userprofile') and user.userprofile:
            user_type = user.userprofile.user_type
        
        notifications = []
        
        if user_type == 'student':
            notifications = self._get_student_notifications(user)
        elif user_type == 'teacher':
            notifications = self._get_teacher_notifications(user)
        
        # Add default notification if empty
        if not notifications:
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
        
        unread_count = len([n for n in notifications if not n.get('is_read')])
        read_count = len(notifications) - unread_count
        
        return {
            'notifications': notifications,
            'unread_count': unread_count,
            'read_count': read_count,
            'total_count': len(notifications)
        }
    
    def _get_student_notifications(self, user):
        """Get notifications for student"""
        notifications = []
        
        try:
            student = Student.objects.get(user=user)
            
            # Get assignments for student's enrolled courses
            assignments = Assignment.objects.filter(
                group__enrollments__student=student,
                status='active',
                create_date__gte=timezone.now() - timedelta(days=30)
            ).order_by('-create_date')
            
            for assignment in assignments:
                time_diff = timezone.now() - assignment.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                # Check if assignment is due soon
                due_diff = assignment.due_date - timezone.now()
                is_urgent = due_diff.total_seconds() < 86400  # Less than 24 hours
                
                notification_id = f'assignment_{assignment.id}'
                
                # Check if user has read this notification
                notification_status, created = NotificationStatus.objects.get_or_create(
                    user=user,
                    notification_id=notification_id,
                    defaults={
                        'notification_type': 'assignment',
                        'is_read': False
                    }
                )
                
                notifications.append({
                    'id': notification_id,
                    'title': 'Yeni Ödev Atandı' if time_diff.days < 1 else 'Ödev Hatırlatması',
                    'message': f'{assignment.group.course.name} dersi için: "{assignment.title}"',
                    'time': time_str,
                    'type': 'assignment',
                    'is_read': notification_status.is_read,
                    'icon': 'fas fa-tasks',
                    'color': 'danger' if is_urgent else 'primary'
                })
            
            # Get announcements
            announcements = Announcement.objects.filter(
                group__enrollments__student=student,
                status='active',
                create_date__gte=timezone.now() - timedelta(days=30)
            ).order_by('-create_date')
            
            for announcement in announcements:
                time_diff = timezone.now() - announcement.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                notification_id = f'announcement_{announcement.id}'
                
                # Check if user has read this notification
                notification_status, created = NotificationStatus.objects.get_or_create(
                    user=user,
                    notification_id=notification_id,
                    defaults={
                        'notification_type': 'announcement',
                        'is_read': False
                    }
                )
                
                notifications.append({
                    'id': notification_id,
                    'title': 'Yeni Duyuru',
                    'message': f'{announcement.group.course.name}: {announcement.title}',
                    'time': time_str,
                    'type': 'announcement',
                    'is_read': notification_status.is_read,
                    'icon': 'fas fa-bullhorn',
                    'color': 'info'
                })
            
        except Student.DoesNotExist:
            pass
        
        return notifications
    
    def _get_teacher_notifications(self, user):
        """Get notifications for teacher"""
        notifications = []
        
        try:
            teacher = Teacher.objects.get(user=user)
            
            # Get teacher's recent assignments
            assignments = Assignment.objects.filter(
                group__teacher=teacher,
                create_date__gte=timezone.now() - timedelta(days=30)
            ).order_by('-create_date')
            
            for assignment in assignments:
                time_diff = timezone.now() - assignment.create_date
                if time_diff.days == 0:
                    time_str = f"{time_diff.seconds // 3600} saat önce"
                else:
                    time_str = f"{time_diff.days} gün önce"
                
                notifications.append({
                    'id': f'assignment_{assignment.id}',
                    'title': 'Ödev Oluşturuldu',
                    'message': f'{assignment.group.course.name} dersi için "{assignment.title}" ödevi oluşturuldu',
                    'time': time_str,
                    'type': 'assignment',
                    'is_read': True,
                    'icon': 'fas fa-tasks',
                    'color': 'primary'
                })
            
        except Teacher.DoesNotExist:
            pass
        
        return notifications
    
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