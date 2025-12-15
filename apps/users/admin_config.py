"""
Admin Panel Özelleştirme
Django admin panelini tek yönetim merkezi olarak yapılandırır
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.conf import settings

class CustomAdminSite(AdminSite):
    site_header = "Uzaktan Eğitim Sistemi - Yönetim Paneli"
    site_title = "Yönetim Paneli"
    index_title = "Sistem Yönetimi"
    
    def each_context(self, request):
        context = super().each_context(request)
        
        # Hızlı istatistikler ekle
        from apps.students.models import Student
        from apps.teachers.models import Teacher
        from apps.courses.models import Course, CourseGroup
        from apps.enrollment.models import Enrollment
        
        try:
            context.update({
                'total_students': Student.objects.count(),
                'total_teachers': Teacher.objects.count(),
                'total_courses': Course.objects.count(),
                'active_enrollments': Enrollment.objects.filter(status='enrolled').count(),
            })
        except:
            pass
        
        return context

# Özel admin site'ı kullan
admin_site = CustomAdminSite(name='custom_admin')
