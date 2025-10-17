"""
Users app views
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView, ListView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from apps.courses.models import Course, Enrollment
from apps.students.models import Student
from apps.teachers.models import Teacher
from .models import User, UserProfile

class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        context['total_courses'] = Course.objects.filter(status='active').count()
        context['total_students'] = Student.objects.filter(status='active').count()
        context['total_teachers'] = Teacher.objects.filter(status='active').count()
        context['total_enrollments'] = Enrollment.objects.filter(status='enrolled').count()
        
        return context

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Redirect based on user type
        user = self.request.user
        if hasattr(user, 'userprofile'):
            if user.userprofile.user_type == 'student':
                return reverse_lazy('students:dashboard')
            elif user.userprofile.user_type == 'teacher':
                return reverse_lazy('teachers:dashboard')
        
        # Default redirect for admin or users without profile
        return reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, f'Hoş geldiniz, {form.get_user().get_full_name() or form.get_user().username}!')
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Başarıyla çıkış yaptınız.')
        return super().dispatch(request, *args, **kwargs)

class RegisterView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Create UserProfile for new user
        UserProfile.objects.create(
            user=self.object,
            user_type='student'  # Default to student
        )
        messages.success(self.request, 'Hesabınız başarıyla oluşturuldu. Giriş yapabilirsiniz.')
        return response


class ControlPanelView(LoginRequiredMixin, TemplateView):
    template_name = 'users/control_panel.html'
    
    def get(self, request, *args, **kwargs):
        # AJAX request for calendar data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                year = int(request.GET.get('year', timezone.now().year))
                month = int(request.GET.get('month', timezone.now().month))
                
                # Validate year and month
                if not (1900 <= year <= 2100):
                    return JsonResponse({'error': 'Invalid year'}, status=400)
                if not (1 <= month <= 12):
                    return JsonResponse({'error': 'Invalid month'}, status=400)
                
                calendar_data = self.get_calendar_data(year, month)
                return JsonResponse(calendar_data)
            except ValueError as e:
                return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)
            except Exception as e:
                import traceback
                print(f"Calendar AJAX error: {str(e)}")
                print(traceback.format_exc())
                return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        from apps.courses.models import Course, Assignment
        from apps.students.models import Student
        from apps.teachers.models import Teacher
        from django.utils import timezone
        from datetime import timedelta
        
        # Get user-specific statistics
        user_type = 'student'
        if hasattr(self.request.user, 'userprofile'):
            user_type = self.request.user.userprofile.user_type
        
        if user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
                # Student's enrolled courses
                context['total_courses'] = student.enrollments.filter(status='enrolled').count()
                # Active assignments for student
                context['total_assignments'] = Assignment.objects.filter(
                    group__enrollments__student=student,
                    status='active',
                    due_date__gt=timezone.now()
                ).count()
                # Student count (just for display)
                context['total_students'] = Student.objects.filter(status='active').count()
                context['total_teachers'] = Teacher.objects.filter(status='active').count()
            except Student.DoesNotExist:
                context['total_courses'] = 0
                context['total_assignments'] = 0
                context['total_students'] = Student.objects.filter(status='active').count()
                context['total_teachers'] = Teacher.objects.filter(status='active').count()
        
        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                # Teacher's courses
                context['total_courses'] = teacher.course_groups.filter(status='active').count()
                # Teacher's assignments
                context['total_assignments'] = Assignment.objects.filter(
                    group__teacher=teacher,
                    status='active'
                ).count()
                context['total_students'] = Student.objects.filter(status='active').count()
                context['total_teachers'] = Teacher.objects.filter(status='active').count()
            except Teacher.DoesNotExist:
                context['total_courses'] = 0
                context['total_assignments'] = 0
                context['total_students'] = Student.objects.filter(status='active').count()
                context['total_teachers'] = Teacher.objects.filter(status='active').count()
        
        else:
            # Admin view
            context['total_courses'] = Course.objects.filter(status='active').count()
            context['total_students'] = Student.objects.filter(status='active').count()
            context['total_teachers'] = Teacher.objects.filter(status='active').count()
            context['total_assignments'] = Assignment.objects.filter(status='active').count()
        
        # Get recent activities
        recent_activities = []
        
        # Get user type
        user_type = 'student'
        if hasattr(self.request.user, 'userprofile'):
            user_type = self.request.user.userprofile.user_type
        
        if user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
                
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
                    
                    recent_activities.append({
                        'title': 'Yeni Ödev Atandı',
                        'description': f'{assignment.group.course.name} - {assignment.title}',
                        'time': time_str,
                        'icon': 'fas fa-tasks',
                        'color': '#667eea'
                    })
                
            except Student.DoesNotExist:
                pass
        
        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                
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
                    
                    recent_activities.append({
                        'title': 'Ödev Oluşturuldu',
                        'description': f'{assignment.group.course.name} - {assignment.title}',
                        'time': time_str,
                        'icon': 'fas fa-plus-circle',
                        'color': '#2ed573'
                    })
                
            except Teacher.DoesNotExist:
                pass
        
        context['recent_activities'] = recent_activities
        
        # Generate calendar days with real assignment data
        import calendar
        from datetime import date
        
        today = date.today()
        cal = calendar.monthcalendar(today.year, today.month)
        calendar_days = []
        
        # Get assignments for current month
        month_start = date(today.year, today.month, 1)
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1)
        else:
            month_end = date(today.year, today.month + 1, 1)
        
        assignments_in_month = {}
        if user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
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
                        'title': assignment.title,
                        'course': assignment.group.course.name
                    })
            except Student.DoesNotExist:
                pass
        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=self.request.user)
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
                        'title': assignment.title,
                        'course': assignment.group.course.name
                    })
            except Teacher.DoesNotExist:
                pass
        
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
                    is_today = day == today.day
                    has_event = day in assignments_in_month
                    assignment_title = ''
                    course_name = ''
                    
                    if has_event and assignments_in_month[day]:
                        # Get first assignment for this day
                        first_assignment = assignments_in_month[day][0]
                        assignment_title = first_assignment['title']
                        course_name = first_assignment['course']
                    
                    calendar_days.append({
                        'number': day,
                        'is_today': is_today,
                        'has_event': has_event,
                        'assignment_title': assignment_title,
                        'course_name': course_name
                    })
        
        context['calendar_days'] = calendar_days
        context['current_year'] = today.year
        context['current_month'] = today.month
        context['current_month_name'] = [
            'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ][today.month - 1]
        
        return context
    
    def get_calendar_data(self, year, month):
        """Get calendar data for AJAX requests"""
        import calendar
        from datetime import date
        from apps.courses.models import Assignment
        from apps.students.models import Student
        from apps.teachers.models import Teacher
        
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
            if hasattr(self.request.user, 'userprofile'):
                user_type = self.request.user.userprofile.user_type
            
            assignments_in_month = {}
            if user_type == 'student':
                try:
                    student = Student.objects.get(user=self.request.user)
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
                            'title': assignment.title,
                            'course': assignment.group.course.name
                        })
                except Student.DoesNotExist:
                    print(f"Student not found for user: {self.request.user.username}")
                    pass
            elif user_type == 'teacher':
                try:
                    teacher = Teacher.objects.get(user=self.request.user)
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
                            'title': assignment.title,
                            'course': assignment.group.course.name
                        })
                except Teacher.DoesNotExist:
                    print(f"Teacher not found for user: {self.request.user.username}")
                    pass
            
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
                        
                        if has_event and assignments_in_month[day]:
                            # Get first assignment for this day
                            first_assignment = assignments_in_month[day][0]
                            assignment_title = first_assignment['title']
                            course_name = first_assignment['course']
                        
                        calendar_days.append({
                            'number': day,
                            'is_today': is_today,
                            'has_event': has_event,
                            'assignment_title': assignment_title,
                            'course_name': course_name
                        })
            
            print(f"Calendar data generated for {year}-{month}: {len(calendar_days)} days")
            return {'calendar_days': calendar_days}
            
        except Exception as e:
            print(f"Error in get_calendar_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'calendar_days': [], 'error': str(e)}


class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/notifications.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get real notifications from database
        from apps.courses.models import Assignment, Announcement
        from apps.notes.models import Note
        from .models import NotificationStatus
        from django.utils import timezone
        from datetime import timedelta
        
        notifications = []
        
        # Get user type
        user_type = 'student'
        if hasattr(self.request.user, 'userprofile'):
            user_type = self.request.user.userprofile.user_type
        
        if user_type == 'student':
            try:
                from apps.students.models import Student
                student = Student.objects.get(user=self.request.user)
                
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
                        user=self.request.user,
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
                        user=self.request.user,
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
                
                # Get recent grades
                recent_notes = Note.objects.filter(
                    student=self.request.user,
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).order_by('-created_at')
                
                for note in recent_notes:
                    time_diff = timezone.now() - note.created_at
                    if time_diff.days == 0:
                        time_str = f"{time_diff.seconds // 3600} saat önce"
                    else:
                        time_str = f"{time_diff.days} gün önce"
                    
                    notifications.append({
                        'id': f'grade_{note.id}',
                        'title': 'Not Güncellendi',
                        'message': f'{note.course.name} dersi {note.get_exam_type_display().lower()} notunuz güncellendi: {note.score}',
                        'time': time_str,
                        'type': 'grade',
                        'is_read': False,
                        'icon': 'fas fa-star',
                        'color': 'success'
                    })
                
            except Student.DoesNotExist:
                pass
        
        elif user_type == 'teacher':
            try:
                from apps.teachers.models import Teacher
                teacher = Teacher.objects.get(user=self.request.user)
                
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
        
        # Sort notifications by time (newest first)
        notifications.sort(key=lambda x: x['time'], reverse=False)
        
        # Add some sample notifications if list is empty
        if not notifications:
            notifications = [
                {
                    'id': 1,
                    'title': 'Hoş Geldiniz',
                    'message': 'Kurs yönetim sistemine hoş geldiniz! Bildirimleriniz burada görünecek.',
                    'time': '1 gün önce',
                    'type': 'welcome',
                    'is_read': False,
                    'icon': 'fas fa-info-circle',
                    'color': 'info'
                }
            ]
        
        context['notifications'] = notifications
        context['unread_count'] = len([n for n in notifications if not n['is_read']])
        context['total_count'] = len(notifications)
        
        return context


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
def mark_notification_read(request):
    """Mark a notification as read via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            notification_id = data.get('notification_id')
            
            if notification_id:
                from .models import NotificationStatus
                from django.utils import timezone
                
                # Update or create notification status
                notification_status, created = NotificationStatus.objects.get_or_create(
                    user=request.user,
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
                
                return JsonResponse({'success': True, 'message': 'Bildirim okundu olarak işaretlendi'})
            else:
                return JsonResponse({'success': False, 'error': 'Bildirim ID bulunamadı'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Geçersiz JSON verisi'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Sadece POST istekleri kabul edilir'})