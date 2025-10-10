"""
Custom decorators for the application
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def student_required(view_func):
    """Decorator to require student user type"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sayfaya sadece öğrenciler erişebilir.')
            raise PermissionDenied
    return _wrapped_view

def teacher_required(view_func):
    """Decorator to require teacher user type"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'teacher':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sayfaya sadece öğretmenler erişebilir.')
            raise PermissionDenied
    return _wrapped_view

def admin_required(view_func):
    """Decorator to require admin user type"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'admin'):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sayfaya sadece yöneticiler erişebilir.')
            raise PermissionDenied
    return _wrapped_view

def teacher_or_admin_required(view_func):
    """Decorator to require teacher or admin user type"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if (request.user.is_staff or 
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.user_type in ['teacher', 'admin'])):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Bu sayfaya sadece öğretmenler ve yöneticiler erişebilir.')
            raise PermissionDenied
    return _wrapped_view