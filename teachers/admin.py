from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['tc_no', 'title', 'first_name', 'last_name', 'department', 'status', 'hire_date']
    list_filter = ['status', 'gender', 'department', 'hire_date']
    search_fields = ['tc_no', 'first_name', 'last_name', 'email', 'department']
    
    fieldsets = (
        ('Kişisel Bilgiler', {
            'fields': ('user', 'tc_no', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'gender')
        }),
        ('Akademik Bilgiler', {
            'fields': ('title', 'department', 'hire_date')
        }),
        ('Sistem Bilgileri', {
            'fields': ('status',)
        }),
    )