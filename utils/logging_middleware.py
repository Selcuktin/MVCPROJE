"""
Middleware for automatic activity logging
"""
from django.utils.deprecation import MiddlewareMixin
from .models import ActivityLog


def get_user_role(user):
    """Kullanıcının rolünü belirle"""
    if user.is_superuser:
        return 'Admin'
    elif hasattr(user, 'teacher'):
        return 'Öğretmen'
    elif hasattr(user, 'student'):
        return 'Öğrenci'
    return 'Kullanıcı'


def get_detailed_description(request, action, model_name, path_parts):
    """Detaylı ve okunabilir açıklama oluştur"""
    user_role = get_user_role(request.user)
    user_name = request.user.get_full_name() or request.user.username
    
    # Model isimlerini Türkçeleştir
    model_names_tr = {
        'Course': 'ders',
        'Student': 'öğrenci',
        'Teacher': 'öğretmen',
        'Note': 'not',
        'Enrollment': 'kayıt',
        'Assignment': 'ödev',
        'Announcement': 'duyuru',
        'Submission': 'teslim',
        'Quiz': 'sınav',
        'Question': 'soru',
        'QuestionBank': 'soru bankası',
        'General': 'sayfa',
        'User': 'kullanıcı',
    }
    
    model_tr = model_names_tr.get(model_name, model_name.lower())
    
    # İşlem türüne göre açıklama
    action_descriptions = {
        'create': f'{user_role} {user_name} yeni {model_tr} oluşturdu',
        'update': f'{user_role} {user_name} {model_tr} güncelledi',
        'delete': f'{user_role} {user_name} {model_tr} sildi',
        'view': f'{user_role} {user_name} {model_tr} görüntüledi',
        'export': f'{user_role} {user_name} {model_tr} dışa aktardı',
        'enroll': f'{user_role} {user_name} öğrenci kaydı yaptı',
        'submit': f'{user_role} {user_name} ödev teslim etti',
        'grade': f'{user_role} {user_name} not girişi yaptı',
    }
    
    # Özel URL pattern'leri için daha detaylı açıklamalar
    path = request.path.lower()
    
    if 'assignment' in path:
        if 'create' in path or (request.method == 'POST' and action == 'create'):
            return f'{user_role} {user_name} yeni ödev ekledi'
        elif 'submit' in path:
            return f'{user_role} {user_name} ödev teslim etti'
        elif 'grade' in path or 'feedback' in path:
            return f'{user_role} {user_name} ödev notlandırdı'
        elif action == 'view':
            return f'{user_role} {user_name} ödev detaylarını görüntüledi'
    
    if 'quiz' in path:
        if 'create' in path or (request.method == 'POST' and action == 'create'):
            return f'{user_role} {user_name} yeni sınav oluşturdu'
        elif 'question' in path:
            if 'create' in path:
                return f'{user_role} {user_name} sınava soru ekledi'
            return f'{user_role} {user_name} soru bankasını görüntüledi'
        elif 'result' in path or 'attempt' in path:
            return f'{user_role} {user_name} sınav sonuçlarını görüntüledi'
        elif action == 'view':
            return f'{user_role} {user_name} sınav detaylarını görüntüledi'
    
    if 'announcement' in path:
        if 'create' in path or (request.method == 'POST' and action == 'create'):
            return f'{user_role} {user_name} yeni duyuru yayınladı'
        elif action == 'view':
            return f'{user_role} {user_name} duyuruları görüntüledi'
    
    if 'student' in path:
        if 'create' in path or 'add' in path:
            return f'{user_role} {user_name} yeni öğrenci ekledi'
        elif 'enroll' in path:
            return f'{user_role} {user_name} öğrenci kaydı yaptı'
        elif action == 'view':
            return f'{user_role} {user_name} öğrenci bilgilerini görüntüledi'
    
    if 'teacher' in path:
        if 'assignment' in path:
            return f'{user_role} {user_name} öğretmen-ders ataması yaptı'
        elif action == 'view':
            return f'{user_role} {user_name} öğretmen bilgilerini görüntüledi'
    
    if 'course' in path:
        if 'create' in path or (request.method == 'POST' and action == 'create'):
            return f'{user_role} {user_name} yeni ders oluşturdu'
        elif 'content' in path:
            return f'{user_role} {user_name} ders içeriği düzenledi'
        elif action == 'view':
            return f'{user_role} {user_name} ders detaylarını görüntüledi'
    
    if 'note' in path or 'grade' in path:
        if request.method == 'POST':
            return f'{user_role} {user_name} not girişi yaptı'
        return f'{user_role} {user_name} notları görüntüledi'
    
    if 'profile' in path:
        return f'{user_role} {user_name} profilini görüntüledi'
    
    if 'dashboard' in path:
        return f'{user_role} {user_name} panele giriş yaptı'
    
    if 'message' in path or 'chat' in path:
        if request.method == 'POST':
            return f'{user_role} {user_name} mesaj gönderdi'
        return f'{user_role} {user_name} mesajları görüntüledi'
    
    # Varsayılan açıklama
    return action_descriptions.get(action, f'{user_role} {user_name} {model_tr} işlemi yaptı')


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
        
        # Only log successful responses (2xx status codes) and redirects (3xx for POST)
        if not (200 <= response.status_code < 400):
            return response
        
        # Determine action and model from path
        path_parts = request.path.strip('/').split('/')
        
        # Skip logging for some paths
        skip_paths = ['favicon.ico', 'media', 'static', 'ajax', 'api']
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
                'quiz': 'Quiz',
                'question': 'Question',
                'question-banks': 'QuestionBank',
            }
            
            for key, value in model_map.items():
                if key in path_parts:
                    model_name = value
                    break
            
            # Determine action from URL patterns and HTTP method
            if request.method == 'POST':
                if 'create' in path_parts or 'add' in path_parts:
                    action = 'create'
                elif 'delete' in path_parts:
                    action = 'delete'
                elif 'submit' in path_parts:
                    action = 'submit'
                elif 'grade' in path_parts or 'feedback' in path_parts:
                    action = 'grade'
                elif 'enroll' in path_parts:
                    action = 'enroll'
                else:
                    action = 'update'
            elif 'update' in path_parts or 'edit' in path_parts:
                action = 'update'
            elif 'delete' in path_parts:
                action = 'delete'
            elif 'export' in request.GET or 'export' in path_parts:
                action = 'export'
            elif request.method == 'GET':
                action = 'view'
        
        # Create log entry (skip if too frequent)
        try:
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
                # Detaylı açıklama oluştur
                description = get_detailed_description(request, action, model_name, path_parts)
                
                ActivityLog.log_activity(
                    user=request.user,
                    action=action,
                    model_name=model_name,
                    description=description,
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

