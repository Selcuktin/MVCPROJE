"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya kullanıcı işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, CreateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

# Rate limiting (optional)
try:
    from ratelimit.decorators import ratelimit
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False

from .models import User, UserProfile
from .controllers import UserController

class HomeView(TemplateView):
    template_name = 'users/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.get_home_context(self.request))
        return context

# Rate limiting decorator (if available)
if RATELIMIT_AVAILABLE:
    @method_decorator(ratelimit(key='ip', rate='5/h', method='POST', block=True), name='dispatch')
    class CustomLoginView(LoginView):
        template_name = 'users/login.html'
        redirect_authenticated_user = True
        
        def get_success_url(self):
            controller = UserController()
            return controller.get_login_success_url(self.request.user)
        
        def form_valid(self, form):
            controller = UserController()
            controller.handle_login_success(self.request, form.get_user())
            return super().form_valid(form)
        
        def form_invalid(self, form):
            # Log failed login attempts
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed login attempt from IP: {self.get_client_ip()}")
            return super().form_invalid(form)
        
        @staticmethod
        def get_client_ip(request=None):
            """Get client IP address"""
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            return "Unknown"
else:
    # Without rate limiting
    class CustomLoginView(LoginView):
        template_name = 'users/login.html'
        redirect_authenticated_user = True
        
        def get_success_url(self):
            controller = UserController()
            return controller.get_login_success_url(self.request.user)
        
        def form_valid(self, form):
            controller = UserController()
            controller.handle_login_success(self.request, form.get_user())
            return super().form_valid(form)

class CustomLogoutView(LogoutView):
    next_page = 'home'
    
    def dispatch(self, request, *args, **kwargs):
        controller = UserController()
        controller.handle_logout(request)
        return super().dispatch(request, *args, **kwargs)

class RegisterView(TemplateView):
    template_name = 'users/register.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.handle_user_registration(self.request))
        context['form'] = UserCreationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            controller = UserController()
            result = controller.handle_user_registration(request, form.cleaned_data)
            if result.get('success'):
                return redirect('users:login')
        
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return render(request, self.template_name, context)


class NotificationsView(LoginRequiredMixin, TemplateView):
    template_name = 'users/notifications.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = UserController()
        context.update(controller.get_notifications_context(self.request))
        return context


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
def mark_notification_read(request):
    """Mark a notification as read via AJAX"""
    controller = UserController()
    return controller.mark_notification_read_ajax(request)