"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya kullanıcı işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

# Rate limiting (optional)
try:
    from ratelimit.decorators import ratelimit
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False

from .models import User, UserProfile
from .controllers import UserController
from .forms import CustomUserCreationForm

class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.get_home_context(self.request))
        return context

# Rate limiting decorator (if available)
if RATELIMIT_AVAILABLE:
    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
    class CustomLoginView(LoginView):
        template_name = 'users/login.html'
        redirect_authenticated_user = True
        
        def get_success_url(self):
            # Superuser/staff için admin paneline yönlendir
            if self.request.user.is_superuser or self.request.user.is_staff:
                return '/admin/'
            controller = UserController()
            return controller.get_login_success_url(self.request.user)
        
        def form_valid(self, form):
            user = form.get_user()
            if user.is_superuser or user.is_staff:
                from django.contrib import messages
                messages.success(self.request, f'Admin olarak giriş yaptınız, Hoş geldiniz {user.get_full_name() or user.username}!')
                return super().form_valid(form)
            controller = UserController()
            controller.handle_login_success(self.request, user)
            return super().form_valid(form)
        
        def form_invalid(self, form):
            # Log failed login attempts
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed login attempt from IP: {self.get_client_ip()}")
            return super().form_invalid(form)
        
        @staticmethod
        def get_client_ip(request=None):
            """Get client IP address"""
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            return "Unknown"
else:
    # Without rate limiting
    class CustomLoginView(LoginView):
        template_name = 'users/login.html'
        redirect_authenticated_user = True
        
        def get_success_url(self):
            # Superuser/staff için admin paneline yönlendir
            if self.request.user.is_superuser or self.request.user.is_staff:
                return '/admin/'  # Admin paneline yönlendir
            
            controller = UserController()
            return controller.get_login_success_url(self.request.user)
        
        def form_valid(self, form):
            user = form.get_user()
            
            # Superuser/staff check
            if user.is_superuser or user.is_staff:
                # Admin için özel işlem
                from django.contrib import messages
                messages.success(self.request, f'Admin olarak giriş yaptınız, Hoş geldiniz {user.get_full_name() or user.username}!')
            else:
                # Normal kullanıcı işlemi
                controller = UserController()
                controller.handle_login_success(self.request, user)
            
            return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = 'home'
    template_name = 'users/logged_out.html'
    
    def dispatch(self, request, *args, **kwargs):
        controller = UserController()
        controller.handle_logout(request)
        response = super().dispatch(request, *args, **kwargs)
        
        # Botpress çerezlerini sunucu tarafından sil
        # Tüm olası Botpress cookie isimlerini dene
        botpress_cookie_patterns = [
            'bp-', 'bp_', 'botpress', 'webchat', 'conversation', 'conv-'
        ]
        
        # Request'teki tüm cookie'leri kontrol et
        for cookie_name in request.COOKIES.keys():
            # Botpress ile ilgili cookie'leri sil
            for pattern in botpress_cookie_patterns:
                if pattern in cookie_name.lower():
                    # Cookie'yi sil - tüm domain ve path kombinasyonları için
                    response.delete_cookie(cookie_name)
                    response.delete_cookie(cookie_name, domain=request.get_host())
                    response.delete_cookie(cookie_name, path='/')
                    response.delete_cookie(cookie_name, path='/webchat')
                    response.delete_cookie(cookie_name, path='/chat')
                    break
        
        # Cache-Control header'ları ekle (tarayıcı cache'ini temizle)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response

class RegisterView(TemplateView):
    template_name = 'users/register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CustomUserCreationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create UserProfile as student
            from .models import UserProfile
            from apps.students.models import Student
            from datetime import date
            
            # Create UserProfile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'user_type': 'student'}
            )
            
            # Create Student profile
            Student.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': user.first_name or user.username,
                    'last_name': user.last_name or '',
                    'email': user.email or f'{user.username}@example.com',
                    'school_number': f'STD{user.id:06d}',  # Auto-generate student number
                    'birth_date': date(2000, 1, 1),  # Default birth date
                    'phone': '0000000000',
                    'gender': 'M',
                    'address': 'Adres bilgisi girilmedi',
                }
            )
            
            from django.contrib import messages
            messages.success(request, 'Kayıt başarılı! Öğrenci hesabınız oluşturuldu. Şimdi giriş yapabilirsiniz.')
            return redirect('users:login')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)


class ControlPanelView(LoginRequiredMixin, TemplateView):
    template_name = 'users/control_panel.html'
    
    def get(self, request, *args, **kwargs):
        # AJAX request for calendar data
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            controller = UserController()
            return controller.get_calendar_data_ajax(request)
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.get_control_panel_context(self.request))
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
        controller = UserController()
        context.update(controller.get_notifications_context(self.request))
        return context


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
def mark_notification_read(request):
    """Mark a notification as read via AJAX"""
    controller = UserController()
    return controller.mark_notification_read_ajax(request)


@login_required
def get_unread_notification_count(request):
    """Get unread notification count via AJAX"""
    from .services import UserService
    service = UserService()
    count = service.get_unread_notifications_count(request.user)
    return JsonResponse({'count': count})


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view"""
    template_name = 'users/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user profile
        try:
            user_profile = user.userprofile
        except:
            user_profile = None
        
        # Get role-specific information
        role_info = {}
        if user_profile:
            if user_profile.user_type == 'student':
                try:
                    from apps.students.models import Student
                    student = Student.objects.get(user=user)
                    role_info = {
                        'student_number': student.student_number,
                        'department': student.department,
                        'status': student.get_status_display(),
                    }
                except:
                    pass
            elif user_profile.user_type == 'teacher':
                try:
                    from apps.teachers.models import Teacher
                    teacher = Teacher.objects.get(user=user)
                    role_info = {
                        'department': teacher.department,
                        'title': teacher.title,
                    }
                except:
                    pass
        
        context['user_profile'] = user_profile
        context['role_info'] = role_info
        
        return context


from django.views.generic import ListView
from django.contrib.admin.views.decorators import staff_member_required
from django.db import models as db_models
from django.contrib.auth.mixins import UserPassesTestMixin


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Modern Kullanıcı Listesi - Admin için"""
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 12
    login_url = 'users:login'
    
    def test_func(self):
        """Sadece staff veya superuser erişebilir"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        queryset = User.objects.select_related('userprofile').all().order_by('-date_joined')
        
        # Search filter
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                db_models.Q(username__icontains=search) |
                db_models.Q(first_name__icontains=search) |
                db_models.Q(last_name__icontains=search) |
                db_models.Q(email__icontains=search)
            )
        
        # User type filter
        user_type = self.request.GET.get('user_type', '')
        if user_type:
            queryset = queryset.filter(userprofile__user_type=user_type)
        
        # Status filter
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['user_type_filter'] = self.request.GET.get('user_type', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        context['student_count'] = UserProfile.objects.filter(user_type='student').count()
        context['teacher_count'] = UserProfile.objects.filter(user_type='teacher').count()
        context['admin_count'] = UserProfile.objects.filter(user_type='admin').count()
        return context
