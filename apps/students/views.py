"""
Students app views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import HttpResponse
from django.utils import timezone

from .models import Student
from .forms import StudentForm
from apps.courses.models import Course, Enrollment

class StudentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_queryset(self):
        queryset = Student.objects.all()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(school_number__icontains=search) |
                Q(email__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('first_name', 'last_name')

class StudentDetailView(LoginRequiredMixin, DetailView):
    model = Student
    template_name = 'students/detail.html'
    context_object_name = 'student'

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user=self.request.user)
            context['student'] = student
            
            # Get enrollments
            from apps.courses.models import Enrollment, Assignment, Announcement
            from django.utils import timezone
            
            enrollments = Enrollment.objects.filter(student=student, status='enrolled')
            context['enrollments'] = enrollments
            
            # Get enrolled groups
            enrolled_groups = [enrollment.group for enrollment in enrollments]
            
            # Get recent assignments
            recent_assignments = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).order_by('-create_date')[:5]
            context['recent_assignments'] = recent_assignments
            
            # Get recent announcements
            recent_announcements = Announcement.objects.filter(
                group__in=enrolled_groups,
                status='active'
            ).order_by('-create_date')[:5]
            context['recent_announcements'] = recent_announcements
            
            # Get pending submissions count
            from apps.courses.models import Submission
            pending_submissions = Assignment.objects.filter(
                group__in=enrolled_groups,
                status='active',
                due_date__gte=timezone.now()
            ).exclude(
                submissions__student=student
            ).count()
            context['pending_submissions'] = pending_submissions
            context['now'] = timezone.now()
            
        except Student.DoesNotExist:
            messages.error(self.request, 'Öğrenci profili bulunamadı.')
        
        return context

class StudentCoursesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/courses.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            student = Student.objects.get(user=self.request.user)
            context['student'] = student
            
            # Get enrolled course groups
            from apps.courses.models import CourseGroup
            enrollments = Enrollment.objects.filter(student=student, status='enrolled')
            context['enrollments'] = enrollments
            
            # Get available course groups (not enrolled)
            enrolled_group_ids = enrollments.values_list('group_id', flat=True)
            available_groups = CourseGroup.objects.filter(status='active').exclude(id__in=enrolled_group_ids)
            context['available_groups'] = available_groups
            
        except Student.DoesNotExist:
            messages.error(self.request, 'Öğrenci profili bulunamadı.')
        
        return context

class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğrenci başarıyla oluşturuldu.')
        return super().form_valid(form)

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğrenci bilgileri başarıyla güncellendi.')
        return super().form_valid(form)

class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = 'students/delete.html'
    success_url = reverse_lazy('students:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Öğrenci başarıyla silindi.')
        return super().delete(request, *args, **kwargs)