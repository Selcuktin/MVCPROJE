"""
Views for activity logs
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ActivityLog, ChangeHistory


@staff_member_required
def activity_log_list(request):
    """Display activity logs (admin only)"""
    
    # Get filter parameters
    user_filter = request.GET.get('user', '')
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    logs = ActivityLog.objects.select_related('user').all()
    
    # Apply filters
    if user_filter:
        logs = logs.filter(user__username__icontains=user_filter)
    
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if model_filter:
        logs = logs.filter(model_name__icontains=model_filter)
    
    if search_query:
        logs = logs.filter(
            Q(object_repr__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    actions = ActivityLog.ACTION_CHOICES
    models = ActivityLog.objects.values_list('model_name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'models': models,
        'user_filter': user_filter,
        'action_filter': action_filter,
        'model_filter': model_filter,
        'search_query': search_query,
    }
    
    return render(request, 'utils/activity_log_list.html', context)


@login_required
def my_activity_log(request):
    """Display current user's activity logs"""
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    model_filter = request.GET.get('model', '')
    
    # Base queryset - only current user's logs
    logs = ActivityLog.objects.filter(user=request.user)
    
    # Apply filters
    if action_filter:
        logs = logs.filter(action=action_filter)
    
    if model_filter:
        logs = logs.filter(model_name__icontains=model_filter)
    
    # Pagination
    paginator = Paginator(logs, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filters
    actions = ActivityLog.ACTION_CHOICES
    models = ActivityLog.objects.filter(user=request.user).values_list('model_name', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'actions': actions,
        'models': models,
        'action_filter': action_filter,
        'model_filter': model_filter,
    }
    
    return render(request, 'utils/my_activity_log.html', context)


@staff_member_required
def activity_log_detail(request, pk):
    """Display detailed activity log with change history"""
    from django.shortcuts import get_object_or_404
    
    log = get_object_or_404(ActivityLog, pk=pk)
    changes = log.changes.all()
    
    context = {
        'log': log,
        'changes': changes,
    }
    
    return render(request, 'utils/activity_log_detail.html', context)

