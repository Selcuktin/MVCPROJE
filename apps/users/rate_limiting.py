"""
Rate Limiting Middleware
Protect against brute force and DDoS attacks
"""
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone
from functools import wraps


class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return self.get_response(request)
        
        # Check rate limit
        if not self._check_rate_limit(request):
            return HttpResponseForbidden(
                "Rate limit exceeded. Please try again later."
            )
        
        response = self.get_response(request)
        return response
    
    def _check_rate_limit(self, request):
        """Check if request is within rate limit"""
        # Get client IP
        ip = self._get_client_ip(request)
        
        # Different limits for different endpoints
        if request.path.startswith('/api/'):
            limit = 100  # 100 requests
            window = 60  # per minute
        elif request.path.startswith('/login/'):
            limit = 5  # 5 attempts
            window = 300  # per 5 minutes
        else:
            limit = 200  # 200 requests
            window = 60  # per minute
        
        # Cache key
        cache_key = f'ratelimit:{ip}:{request.path}'
        
        # Get current count
        count = cache.get(cache_key, 0)
        
        if count >= limit:
            return False
        
        # Increment counter
        cache.set(cache_key, count + 1, window)
        return True
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def rate_limit(limit=10, window=60):
    """
    Decorator for rate limiting views
    Usage: @rate_limit(limit=5, window=300)  # 5 requests per 5 minutes
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Get client IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            # Cache key
            cache_key = f'ratelimit:{func.__name__}:{ip}'
            
            # Get current count
            count = cache.get(cache_key, 0)
            
            if count >= limit:
                return HttpResponseForbidden(
                    f"Rate limit exceeded. Maximum {limit} requests per {window} seconds."
                )
            
            # Increment counter
            cache.set(cache_key, count + 1, window)
            
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# Login rate limiting
def check_login_attempts(username, ip_address):
    """Check if login attempts exceeded"""
    cache_key_user = f'login_attempts:user:{username}'
    cache_key_ip = f'login_attempts:ip:{ip_address}'
    
    user_attempts = cache.get(cache_key_user, 0)
    ip_attempts = cache.get(cache_key_ip, 0)
    
    # Block after 5 failed attempts
    if user_attempts >= 5 or ip_attempts >= 10:
        return False, 'Too many failed login attempts. Please try again in 15 minutes.'
    
    return True, ''


def record_failed_login(username, ip_address):
    """Record failed login attempt"""
    cache_key_user = f'login_attempts:user:{username}'
    cache_key_ip = f'login_attempts:ip:{ip_address}'
    
    # Increment counters (15 minute window)
    user_attempts = cache.get(cache_key_user, 0)
    ip_attempts = cache.get(cache_key_ip, 0)
    
    cache.set(cache_key_user, user_attempts + 1, 900)  # 15 minutes
    cache.set(cache_key_ip, ip_attempts + 1, 900)


def clear_login_attempts(username, ip_address):
    """Clear login attempts on successful login"""
    cache_key_user = f'login_attempts:user:{username}'
    cache_key_ip = f'login_attempts:ip:{ip_address}'
    
    cache.delete(cache_key_user)
    cache.delete(cache_key_ip)
