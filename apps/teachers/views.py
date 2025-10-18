"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya öğretmen işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy

from .models import Teacher
from .forms import TeacherForm
from .controllers import TeacherController

class TeacherListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/list.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_list_context(self.request))
        return context

class TeacherDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'teachers/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_detail_context(self.request, self.kwargs['pk']))
        return context

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_dashboard_context(self.request))
        return context

class TeacherCoursesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/courses.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_courses_context(self.request))
        return context

class TeacherStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/students.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_students_context(self.request))
        return context

class TeacherAssignmentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/assignments.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_assignments_context(self.request))
        return context

class TeacherAnnouncementsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/announcements.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.get_teacher_announcements_context(self.request))
        return context

class TeacherCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/form.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.create_teacher_context(self.request))
        context['form'] = TeacherForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = TeacherForm(request.POST)
        if form.is_valid():
            controller = TeacherController()
            result = controller.create_teacher_context(request, form.cleaned_data)
            if result.get('success'):
                return redirect('teachers:list')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)

class TeacherUpdateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/form.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.update_teacher_context(self.request, self.kwargs['pk']))
        if 'teacher' in context:
            context['form'] = TeacherForm(instance=context['teacher'])
        return context
    
    def post(self, request, *args, **kwargs):
        teacher_id = self.kwargs['pk']
        form = TeacherForm(request.POST)
        if form.is_valid():
            controller = TeacherController()
            result = controller.update_teacher_context(request, teacher_id, form.cleaned_data)
            if result.get('success'):
                return redirect('teachers:list')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)

class TeacherDeleteView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/delete.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = TeacherController()
        context.update(controller.delete_teacher_context(self.request, self.kwargs['pk']))
        return context
    
    def post(self, request, *args, **kwargs):
        controller = TeacherController()
        result = controller.delete_teacher_context(request, self.kwargs['pk'])
        if result.get('success'):
            return redirect('teachers:list')
        return render(request, self.template_name, self.get_context_data(**kwargs))