"""
Content Access Middleware
Permission-gated file downloads and activity tracking
"""
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.courses.models import Enrollment, Assignment
from apps.enrollment.models import EnrollmentMethod, EnrollmentRule


class ContentAccessMiddleware:
    """Middleware for controlling access to course content"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Track activity
        if request.user.is_authenticated and not request.path.startswith('/admin/'):
            self._track_activity(request)
        
        response = self.get_response(request)
        return response
    
    def _track_activity(self, request):
        """Track user activity for analytics"""
        # Simple activity tracking - can be expanded
        if hasattr(request.user, 'userprofile'):
            # Update last activity time
            request.user.userprofile.last_activity = timezone.now()
            request.user.userprofile.save(update_fields=['last_activity'])
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Check content access permissions"""
        # Check if accessing course content
        if 'group_id' in view_kwargs and request.path.startswith('/courses/'):
            group_id = view_kwargs['group_id']
            
            if not self._check_course_access(request.user, group_id):
                return HttpResponseForbidden("Bu içeriğe erişim yetkiniz yok.")
        
        return None
    
    def _check_course_access(self, user, group_id):
        """Check if user has access to course content"""
        if not user.is_authenticated:
            return False
        
        # Admin and staff always have access
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user is enrolled
        if hasattr(user, 'userprofile'):
            if user.userprofile.user_type == 'student':
                try:
                    from apps.students.models import Student
                    student = Student.objects.get(user=user)
                    enrollment = Enrollment.objects.filter(
                        student=student,
                        group_id=group_id,
                        status='enrolled'
                    ).exists()
                    return enrollment
                except:
                    return False
            
            elif user.userprofile.user_type == 'teacher':
                # Teachers can access their own courses
                try:
                    from apps.teachers.models import Teacher
                    from apps.courses.models import CourseGroup
                    teacher = Teacher.objects.get(user=user)
                    group = CourseGroup.objects.filter(
                        id=group_id,
                        teacher=teacher
                    ).exists()
                    return group
                except:
                    return False
        
        return False
