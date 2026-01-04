"""
Custom template tags for user operations
"""
from django import template
from apps.students.models import Student
from apps.teachers.models import Teacher

register = template.Library()

@register.simple_tag
def get_user_type(user):
    """Get user type safely - checks multiple sources"""
    if not user or not user.is_authenticated:
        return None
    
    # 1. Check if user has userprofile with user_type
    try:
        if hasattr(user, 'userprofile') and user.userprofile and user.userprofile.user_type:
            return user.userprofile.user_type
    except:
        pass
    
    # 2. Check Student model directly (most reliable)
    try:
        Student.objects.get(user=user)
        return 'student'
    except Student.DoesNotExist:
        pass
    except:
        pass
    
    # 3. Check Teacher model directly
    try:
        Teacher.objects.get(user=user)
        return 'teacher'
    except Teacher.DoesNotExist:
        pass
    except:
        pass
    
    # 4. Check if user is admin/staff
    if user.is_staff or user.is_superuser:
        return 'admin'
    
    return None

@register.filter
def has_student_profile(user):
    """Check if user has student profile"""
    if not user or not user.is_authenticated:
        return False
    
    # Check relation first
    if hasattr(user, 'student'):
        return True
    
    # Check model directly
    try:
        Student.objects.get(user=user)
        return True
    except Student.DoesNotExist:
        return False

@register.filter
def has_teacher_profile(user):
    """Check if user has teacher profile"""
    if not user or not user.is_authenticated:
        return False
    
    # Check relation first
    if hasattr(user, 'teacher'):
        return True
    
    # Check model directly
    try:
        Teacher.objects.get(user=user)
        return True
    except Teacher.DoesNotExist:
        return False