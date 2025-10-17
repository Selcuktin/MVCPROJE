from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


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