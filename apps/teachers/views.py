"""
Teachers app views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import Teacher
from .forms import TeacherForm

class TeacherListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Teacher
    template_name = 'teachers/list.html'
    context_object_name = 'teachers'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_queryset(self):
        queryset = Teacher.objects.all()
        search = self.request.GET.get('search')
        department = self.request.GET.get('department')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(tc_no__icontains=search) |
                Q(email__icontains=search) |
                Q(department__icontains=search)
            )
        
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('department', 'first_name', 'last_name')

class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'teachers/detail.html'
    context_object_name = 'teacher'

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['teacher'] = teacher
            
            # Get teacher's course groups
            from apps.courses.models import CourseGroup
            teacher_course_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            context['teacher_courses'] = teacher_course_groups
            
            # Calculate total students
            total_students = 0
            for group in teacher_course_groups:
                total_students += group.enrollments.filter(status='enrolled').count()
            context['total_students'] = total_students
            
            # Get recent assignments and announcements
            from apps.courses.models import Assignment, Announcement
            context['recent_assignments'] = Assignment.objects.filter(
                group__in=teacher_course_groups
            ).select_related('group__course').order_by('-create_date')[:5]
            
            context['recent_announcements'] = Announcement.objects.filter(
                group__in=teacher_course_groups
            ).select_related('group__course').order_by('-create_date')[:5]
            
            context['course_groups'] = teacher_course_groups
            context['now'] = timezone.now()
            
        except Teacher.DoesNotExist:
            messages.error(self.request, 'Öğretmen profili bulunamadı.')
        
        return context

class TeacherCoursesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/courses.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            from apps.courses.models import CourseGroup
            context['teacher'] = teacher
            context['course_groups'] = CourseGroup.objects.filter(teacher=teacher, status='active').select_related('course').order_by('course__code')
            
        except Teacher.DoesNotExist:
            messages.error(self.request, 'Öğretmen profili bulunamadı.')
        
        return context

class TeacherStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/students.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['teacher'] = teacher
            
            # Get students from teacher's course groups
            from apps.courses.models import CourseGroup, Enrollment
            teacher_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            students = []
            for group in teacher_groups:
                group_students = Enrollment.objects.filter(group=group, status='enrolled').select_related('student')
                for enrollment in group_students:
                    if enrollment.student not in students:
                        students.append(enrollment.student)
            context['students'] = students
            
        except Teacher.DoesNotExist:
            messages.error(self.request, 'Öğretmen profili bulunamadı.')
        
        return context

class TeacherAssignmentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/assignments.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['teacher'] = teacher
            
            # Get assignments from teacher's course groups
            from apps.courses.models import CourseGroup, Assignment
            teacher_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
            assignments = Assignment.objects.filter(group__in=teacher_groups).order_by('-create_date')
            context['assignments'] = assignments
            
        except Teacher.DoesNotExist:
            messages.error(self.request, 'Öğretmen profili bulunamadı.')
        
        return context

class TeacherAnnouncementsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/announcements.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['teacher'] = teacher
            
            # Get announcements from teacher
            from apps.courses.models import Announcement
            announcements = Announcement.objects.filter(teacher=teacher).order_by('-create_date')
            context['announcements'] = announcements
            
        except Teacher.DoesNotExist:
            messages.error(self.request, 'Öğretmen profili bulunamadı.')
        
        return context

class TeacherCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Yeni öğretmen oluşturma"""
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/form.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğretmen başarıyla oluşturuldu.')
        return super().form_valid(form)

class TeacherUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Öğretmen bilgilerini güncelleme"""
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/form.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğretmen bilgileri başarıyla güncellendi.')
        return super().form_valid(form)

class TeacherDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Öğretmen silme"""
    model = Teacher
    template_name = 'teachers/delete.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Öğretmen başarıyla silindi.')
        return super().delete(request, *args, **kwargs)