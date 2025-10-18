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

from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement
from .services import CourseService, AssignmentService, ReportService
from .forms import CourseForm, CourseGroupForm, AssignmentForm, SubmissionForm, AnnouncementForm


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


class AssignmentController:
    """Assignment business logic controller"""
    
    def __init__(self):
        self.assignment_service = AssignmentService()
    
    def get_assignment_list(self, request, filters=None):
        """Get filtered assignment list"""
        user_type = getattr(request.user, 'userprofile', None)
        if user_type:
            return self.assignment_service.get_user_assignments(
                request.user, user_type.user_type, filters or {}
            )
        return []
    
    def get_assignment_detail(self, request, assignment_id):
        """Get assignment detail with submissions"""
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        return self.assignment_service.get_assignment_with_details(assignment, request.user)
    
    def create_assignment(self, request, form_data):
        """Create new assignment"""
        return self.assignment_service.create_assignment(form_data, request.user)
    
    def submit_assignment(self, request, assignment_id, submission_data):
        """Submit assignment"""
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        return self.assignment_service.submit_assignment(assignment, request.user, submission_data)


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
    
    def generate_assignment_report(self, request, assignment_id, format_type='pdf'):
        """Generate assignment report in specified format"""
        assignment = get_object_or_404(Assignment, pk=assignment_id)
        return self.report_service.generate_assignment_report(assignment, format_type)