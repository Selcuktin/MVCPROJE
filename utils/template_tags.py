"""
Custom template tags
"""
from django import template
from apps.students.models import Student
from apps.teachers.models import Teacher

register = template.Library()

@register.simple_tag
def get_user_type(user):
    """Get user type safely"""
    if not user.is_authenticated:
        return None
    
    # Check if user has userprofile
    if hasattr(user, 'userprofile'):
        return user.userprofile.user_type
    
    # Check if user is student
    try:
        Student.objects.get(user=user)
        return 'student'
    except Student.DoesNotExist:
        pass
    
    # Check if user is teacher
    try:
        Teacher.objects.get(user=user)
        return 'teacher'
    except Teacher.DoesNotExist:
        pass
    
    # Check if user is admin
    if user.is_staff or user.is_superuser:
        return 'admin'
    
    return None

@register.filter
def has_student_profile(user):
    """Check if user has student profile"""
    if not user.is_authenticated:
        return False
    try:
        Student.objects.get(user=user)
        return True
    except Student.DoesNotExist:
        return False

@register.filter
def has_teacher_profile(user):
    """Check if user has teacher profile"""
    if not user.is_authenticated:
        return False
    try:
        Teacher.objects.get(user=user)
        return True
    except Teacher.DoesNotExist:
        return False