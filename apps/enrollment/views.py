"""
Enrollment Views
Student course enrollment interface
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services import EnrollmentService
from apps.courses.models import CourseGroup, Enrollment
from apps.students.models import Student
from apps.academic.models import AcademicTerm


@login_required
def available_courses_view(request):
    """Display available courses for enrollment"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci profili bulunamadı')
        return redirect('users:dashboard')
    
    service = EnrollmentService()
    
    # Get active term
    active_term = AcademicTerm.get_active_term()
    
    if not active_term:
        messages.warning(request, 'Aktif dönem bulunamadı')
        available_courses = []
    else:
        # Get available courses
        available_courses = service.get_available_courses_for_student(student, active_term)
    
    # Get current enrollments
    current_enrollments = service.get_student_enrollments(student, active_term)
    
    context = {
        'student': student,
        'active_term': active_term,
        'available_courses': available_courses,
        'current_enrollments': current_enrollments,
        'registration_open': active_term.is_registration_open if active_term else False
    }
    
    return render(request, 'enrollment/available_courses.html', context)


@login_required
@require_POST
def enroll_course_view(request, group_id):
    """Enroll student in a course"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Öğrenci profili bulunamadı'
        }, status=403)
    
    course_group = get_object_or_404(CourseGroup, id=group_id)
    enrollment_key = request.POST.get('enrollment_key', None)
    
    service = EnrollmentService()
    result = service.enroll_student(student, course_group, enrollment_key)
    
    if result['success']:
        messages.success(request, f"{course_group.course.name} dersine kayıt oldunuz")
    else:
        messages.error(request, result['message'])
    
    return JsonResponse(result)


@login_required
@require_POST
def drop_enrollment_view(request, enrollment_id):
    """Drop an enrollment"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Öğrenci profili bulunamadı'
        }, status=403)
    
    service = EnrollmentService()
    result = service.drop_enrollment(enrollment_id, student)
    
    if result['success']:
        messages.success(request, 'Ders başarıyla bırakıldı')
    else:
        messages.error(request, result['message'])
    
    return JsonResponse(result)


@login_required
def check_enrollment_eligibility(request, group_id):
    """Check if student can enroll (AJAX)"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return JsonResponse({
            'can_enroll': False,
            'messages': ['Öğrenci profili bulunamadı']
        })
    
    course_group = get_object_or_404(CourseGroup, id=group_id)
    enrollment_key = request.GET.get('key', None)
    
    service = EnrollmentService()
    result = service.can_student_enroll(student, course_group, enrollment_key)
    
    return JsonResponse(result)


@login_required
def my_enrollments_view(request):
    """Display student's enrollments"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci profili bulunamadı')
        return redirect('users:dashboard')
    
    service = EnrollmentService()
    
    # Get enrollments by term
    terms = AcademicTerm.objects.filter(
        course_groups__enrollments__student=student
    ).distinct().order_by('-start_date')
    
    enrollments_by_term = []
    for term in terms:
        enrollments = service.get_student_enrollments(student, term)
        enrollments_by_term.append({
            'term': term,
            'enrollments': enrollments
        })
    
    context = {
        'student': student,
        'enrollments_by_term': enrollments_by_term
    }
    
    return render(request, 'enrollment/my_enrollments.html', context)
