"""
Users app views
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib.auth.forms import UserCreationForm
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