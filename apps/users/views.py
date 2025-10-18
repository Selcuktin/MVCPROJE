"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya kullanıcı işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse_lazy

from .models import User, UserProfile
from .controllers import UserController

class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.get_home_context(self.request))
        return context

class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        controller = UserController()
        return controller.get_login_success_url(self.request.user)
    
    def form_valid(self, form):
        controller = UserController()
        controller.handle_login_success(self.request, form.get_user())
        return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        controller = UserController()
        controller.handle_logout(request)
        return super().dispatch(request, *args, **kwargs)

class RegisterView(TemplateView):
    template_name = 'users/register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.handle_user_registration(self.request))
        context['form'] = UserCreationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            controller = UserController()
            result = controller.handle_user_registration(request, form.cleaned_data)
            if result.get('success'):
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
@csrf_exempt
def mark_notification_read(request):
    """Mark a notification as read via AJAX"""
    controller = UserController()
    return controller.mark_notification_read_ajax(request)