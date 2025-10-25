from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import View
import logging

logger = logging.getLogger(__name__)

def handle_exception(request, exception, template_name='errors/error.html'):
    """
    Özel exception handler
    """
    logger.error(f"Exception: {str(exception)}", exc_info=True)
    context = {
        'error_message': str(exception),
        'error_code': 500
    }
    return render(request, template_name, context, status=500)

def handle_404(request, exception):
    """404 sayfa bulunamadı hatası"""
    context = {
        'error_message': 'Sayfa bulunamadı',
        'error_code': 404
    }
    return render(request, 'errors/404.html', context, status=404)

def handle_403(request, exception):
    """403 erişim reddedildi hatası"""
    context = {
        'error_message': 'Bu sayfaya erişim izniniz yok',
        'error_code': 403
    }
    return render(request, 'errors/403.html', context, status=403)

def handle_500(request):
    """500 sunucu hatası"""
    context = {
        'error_message': 'Sunucu hatası oluştu',
        'error_code': 500
    }
    return render(request, 'errors/500.html', context, status=500)


@method_decorator(staff_member_required, name='dispatch')
class ActivityLogListView(LoginRequiredMixin, ListView):
    """View for displaying all activity logs (admin only)"""
    template_name = 'utils/activity_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        # For now, return empty queryset since we don't have activity log model
        # This can be implemented later when activity logging is added
        return []


class MyActivityLogView(LoginRequiredMixin, ListView):
    """View for displaying user's own activity logs"""
    template_name = 'utils/my_activity_log.html'
    context_object_name = 'logs'
    paginate_by = 20
    
    def get_queryset(self):
        # For now, return empty queryset since we don't have activity log model
        # This can be implemented later when activity logging is added
        return []