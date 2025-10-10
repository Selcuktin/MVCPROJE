"""
Middleware for automatic activity logging
"""
from django.utils.deprecation import MiddlewareMixin
from .models import ActivityLog


class ActivityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log certain user activities
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Log view access for authenticated users"""
        
        # Skip logging for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        # Only log for authenticated users
        if not request.user.is_authenticated:
            return None
        
        # Store request for later use in process_response
        request._log_view = True
        return None
    
    def process_response(self, request, response):
        """Log successful requests"""
        
        # Only log if we marked this request for logging
        if not getattr(request, '_log_view', False):
            return response
        
        # Only log successful responses (2xx status codes)
        if not (200 <= response.status_code < 300):
            return response
        
        # Determine action and model from path
        path_parts = request.path.strip('/').split('/')
        
        # Skip logging for some paths
        skip_paths = ['favicon.ico', 'media', 'static']
        if any(skip in request.path for skip in skip_paths):
            return response
        
        # Determine model name from URL
        model_name = 'General'
        action = 'view'
        
        if len(path_parts) > 0:
            # Map common URL patterns to model names
            model_map = {
                'courses': 'Course',
                'students': 'Student',
                'teachers': 'Teacher',
                'notes': 'Note',
                'enrollments': 'Enrollment',
                'assignments': 'Assignment',
                'announcements': 'Announcement',
                'submissions': 'Submission',
            }
            
            for key, value in model_map.items():
                if key in path_parts:
                    model_name = value
                    break
            
            # Determine action from URL patterns
            if 'create' in path_parts or request.method == 'POST' and 'create' in request.path:
                action = 'create'
            elif 'update' in path_parts or 'edit' in path_parts:
                action = 'update'
            elif 'delete' in path_parts:
                action = 'delete'
            elif 'export' in request.GET:
                action = 'export'
            elif request.method == 'GET':
                action = 'view'
        
        # Create log entry asynchronously (or skip if too frequent)
        try:
            # Check if we've logged this recently (avoid spam)
            from django.utils import timezone
            import datetime
            recent_cutoff = timezone.now() - datetime.timedelta(minutes=1)
            
            recent_log = ActivityLog.objects.filter(
                user=request.user,
                action=action,
                model_name=model_name,
                timestamp__gte=recent_cutoff
            ).exists()
            
            if not recent_log:
                ActivityLog.log_activity(
                    user=request.user,
                    action=action,
                    model_name=model_name,
                    description=f"Accessed {request.path}",
                    request=request
                )
        except Exception as e:
            # Don't break the response if logging fails
            print(f"Logging failed: {e}")
        
        return response


class LoginLogoutMiddleware(MiddlewareMixin):
    """
    Middleware to log user login and logout
    """
    
    def process_response(self, request, response):
        """Log login/logout events"""
        
        # Check for login
        if hasattr(request, 'user') and request.user.is_authenticated:
            if 'login' in request.path and request.method == 'POST' and response.status_code == 302:
                try:
                    ActivityLog.log_activity(
                        user=request.user,
                        action='login',
                        model_name='User',
                        object_id=request.user.id,
                        object_repr=request.user.username,
                        description='User logged in',
                        request=request
                    )
                except Exception:
                    pass
        
        # Check for logout
        if 'logout' in request.path and response.status_code == 302:
            try:
                user = getattr(request, 'user', None)
                if user and user.is_authenticated:
                    ActivityLog.log_activity(
                        user=user,
                        action='logout',
                        model_name='User',
                        object_id=user.id,
                        object_repr=user.username,
                        description='User logged out',
                        request=request
                    )
            except Exception:
                pass
        
        return response

