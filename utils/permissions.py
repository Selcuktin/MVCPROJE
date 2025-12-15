"""
Permission utilities
"""
from django.core.exceptions import PermissionDenied

class UserTypePermissionMixin:
    """Mixin for checking user types in class-based views"""
    required_user_types = []
    
    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            raise PermissionDenied("Bu sayfaya erişim yetkiniz yok.")
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self):
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        if user.is_staff:
            return True
        
        if hasattr(user, 'userprofile'):
            return user.userprofile.user_type in self.required_user_types
        
        return False

class StudentPermissionMixin(UserTypePermissionMixin):
    required_user_types = ['student']

class TeacherPermissionMixin(UserTypePermissionMixin):
    required_user_types = ['teacher']

class AdminPermissionMixin(UserTypePermissionMixin):
    required_user_types = ['admin']

class TeacherOrAdminPermissionMixin(UserTypePermissionMixin):
    required_user_types = ['teacher', 'admin']

def check_course_access(user, course_group):
    """Check if user has access to course group"""
    if user.is_staff:
        return True
    
    if hasattr(user, 'userprofile') and user.userprofile:
        user_type = user.userprofile.user_type
        
        if user_type == 'teacher':
            from apps.teachers.models import Teacher
            try:
                teacher = Teacher.objects.get(user=user)
                return course_group.teacher == teacher
            except Teacher.DoesNotExist:
                return False
        
        elif user_type == 'student':
            from apps.students.models import Student
            from apps.courses.models import Enrollment
            try:
                student = Student.objects.get(user=user)
                return Enrollment.objects.filter(
                    student=student, 
                    group=course_group
                ).exists()
            except Student.DoesNotExist:
                return False
    
    return False

def check_assignment_access(user, assignment):
    """Check if user has access to assignment"""
    return check_course_access(user, assignment.group)

def check_grade_edit_permission(user, enrollment):
    """Check if user can edit grades for enrollment"""
    if user.is_staff:
        return True
    
    if hasattr(user, 'userprofile') and user.userprofile and user.userprofile.user_type == 'teacher':
        from apps.teachers.models import Teacher
        try:
            teacher = Teacher.objects.get(user=user)
            return enrollment.group.teacher == teacher
        except Teacher.DoesNotExist:
            return False
    
    return False