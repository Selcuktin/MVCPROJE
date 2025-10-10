from django.contrib import admin
from .models import ActivityLog, ChangeHistory


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'model_name', 'object_repr', 'description']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 
                       'description', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ChangeHistory)
class ChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ['activity_log', 'field_name', 'old_value', 'new_value']
    list_filter = ['field_name']
    search_fields = ['field_name', 'old_value', 'new_value']
    readonly_fields = ['activity_log', 'field_name', 'old_value', 'new_value']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

