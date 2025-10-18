"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya öğrenci işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy

from .models import Student
from .forms import StudentForm
from .controllers import StudentController

class StudentListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/list.html'
    
    def test_func(self):
        # Sadece öğretmen ve admin'ler öğrenci listesini görebilir
        return (self.request.user.is_staff or 
                (hasattr(self.request.user, 'userprofile') and 
                 self.request.user.userprofile.user_type in ['teacher', 'admin']))
    
    def handle_no_permission(self):
        # Öğrenci ise kendi dashboard'una yönlendir
        if (hasattr(self.request.user, 'userprofile') and 
            self.request.user.userprofile.user_type == 'student'):
            return redirect('students:dashboard')
        return super().handle_no_permission()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.get_student_list_context(self.request))
        return context

class StudentDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'students/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.get_student_detail_context(self.request, self.kwargs['pk']))
        return context

class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.get_student_dashboard_context(self.request))
        return context

class StudentCoursesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/courses.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.get_student_courses_context(self.request))
        return context

class StudentCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/form.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.create_student_context(self.request))
        context['form'] = StudentForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = StudentForm(request.POST)
        if form.is_valid():
            controller = StudentController()
            result = controller.create_student_context(request, form.cleaned_data)
            if result.get('success'):
                return redirect('students:list')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/form.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.update_student_context(self.request, self.kwargs['pk']))
        if 'student' in context:
            context['form'] = StudentForm(instance=context['student'])
        return context
    
    def post(self, request, *args, **kwargs):
        student_id = self.kwargs['pk']
        form = StudentForm(request.POST)
        if form.is_valid():
            controller = StudentController()
            result = controller.update_student_context(request, student_id, form.cleaned_data)
            if result.get('success'):
                return redirect('students:list')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)

class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'students/delete.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = StudentController()
        context.update(controller.delete_student_context(self.request, self.kwargs['pk']))
        return context
    
    def post(self, request, *args, **kwargs):
        controller = StudentController()
        result = controller.delete_student_context(request, self.kwargs['pk'])
        if result.get('success'):
            return redirect('students:list')
        return render(request, self.template_name, self.get_context_data(**kwargs))