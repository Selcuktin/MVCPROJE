from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['school_number', 'first_name', 'last_name', 'email', 'status', 'registration_date']
    list_filter = ['status', 'gender', 'registration_date']
    search_fields = ['school_number', 'first_name', 'last_name', 'email']
    readonly_fields = ['registration_date']
    
    fieldsets = (
        ('Kişisel Bilgiler', {
            'fields': ('user', 'school_number', 'first_name', 'last_name', 'email', 'phone', 'birth_date', 'gender')
        }),
        ('Adres Bilgileri', {
            'fields': ('address',)
        }),
        ('Sistem Bilgileri', {
            'fields': ('status', 'registration_date')
        }),
    )