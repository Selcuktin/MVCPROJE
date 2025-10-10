"""
Custom middleware for the application
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class UserTypeMiddleware(MiddlewareMixin):
    """Middleware to add user type to request"""
    
    def process_request(self, request):
        if not isinstance(request.user, AnonymousUser) and request.user.is_authenticated:
            try:
                if hasattr(request.user, 'userprofile'):
                    request.user_type = request.user.userprofile.user_type
                else:
                    request.user_type = 'admin' if request.user.is_staff else 'unknown'
            except Exception as e:
                logger.warning(f"Could not determine user type: {e}")
                request.user_type = 'unknown'
        else:
            request.user_type = None

class APILoggingMiddleware(MiddlewareMixin):
    """Middleware to log API requests"""
    
    def process_request(self, request):
        if request.path.startswith('/api/'):
            logger.info(f"API Request: {request.method} {request.path} - User: {request.user}")
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            logger.info(f"API Response: {response.status_code} for {request.path}")
        return response

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""
    
    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        return response