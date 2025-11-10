"""
Course Controllers - MVC Pattern Implementation
Bu dosya Controller katmanını temsil eder ve business logic'i içerir.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .models import Course, CourseGroup, Enrollment
from .services import CourseService, ReportService, TeacherCourseAssignmentService
from .forms import CourseForm, CourseGroupForm


class CourseController:
    """Course business logic controller"""
    
    def __init__(self):
        self.course_service = CourseService()
    
    def get_course_list(self, request, filters=None):
        """Get filtered course list"""
        return self.course_service.get_filtered_courses(filters or {})
    
    def get_course_detail(self, request, course_id):
        """Get course detail with related data"""
        course = get_object_or_404(Course, pk=course_id)
        return self.course_service.get_course_with_details(course)
    
    def create_course(self, request, form_data):
        """Create new course"""
        return self.course_service.create_course(form_data)
    
    def update_course(self, request, course_id, form_data):
        """Update existing course"""
        course = get_object_or_404(Course, pk=course_id)
        return self.course_service.update_course(course, form_data)
    
    def delete_course(self, request, course_id):
        """Delete course"""
        course = get_object_or_404(Course, pk=course_id)
        return self.course_service.delete_course(course)


class ReportController:
    """Report generation controller"""
    
    def __init__(self):
        self.report_service = ReportService()
    
    def generate_student_report(self, request, format_type='pdf'):
        """Generate student report in specified format"""
        return self.report_service.generate_student_report(format_type)
    
    def generate_course_report(self, request, course_id, format_type='pdf'):
        """Generate course report in specified format"""
        course = get_object_or_404(Course, pk=course_id)
        return self.report_service.generate_course_report(course, format_type)


class TeacherCourseAssignmentController:
    """Teacher-Course Assignment controller"""
    
    def __init__(self):
        self.assignment_service = TeacherCourseAssignmentService()
    
    def get_assignment_panel_data(self, request, filters=None):
        """Get data for assignment panel"""
        current_assignments = self.assignment_service.get_current_assignments(filters)
        assignment_history = self.assignment_service.get_assignment_history(filters, limit=20)
        
        # Get all teachers and courses for filters
        from apps.teachers.models import Teacher
        teachers = Teacher.objects.filter(status='active').order_by('first_name', 'last_name')
        courses = Course.objects.filter(status='active').order_by('code')
        
        return {
            'current_assignments': current_assignments,
            'assignment_history': assignment_history,
            'teachers': teachers,
            'courses': courses,
            'filters': filters or {}
        }
    
    def check_compatibility(self, request, teacher_id, course_id):
        """Check compatibility between teacher and course"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        course = get_object_or_404(Course, pk=course_id)
        return self.assignment_service.check_compatibility(teacher, course)
    
    def check_conflicts(self, request, teacher_id, course_id, semester, schedule):
        """Check schedule conflicts"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        course = get_object_or_404(Course, pk=course_id)
        return self.assignment_service.check_schedule_conflicts(teacher, course, semester, schedule)
    
    def get_teacher_availability(self, request, teacher_id):
        """Get teacher availability status"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        return self.assignment_service.get_teacher_availability(teacher)