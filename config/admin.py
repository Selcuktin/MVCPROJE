"""
Basitleştirilmiş Admin Panel
Sadece temel işlemler: Öğrenciler, Öğretmenler, Dersler, Kayıtlar, Sınavlar
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

# Özel Admin Site
class SimpleAdminSite(admin.AdminSite):
    site_header = "Öğretmen Paneli"
    site_title = "Yönetim Paneli"
    index_title = "Yönetim"
    
    def index(self, request, extra_context=None):
        """Dashboard'u devre dışı bırak, direkt ilk modele yönlendir"""
        from django.shortcuts import redirect
        # Öğrenciler listesine yönlendir
        return redirect('admin:students_student_changelist')

# Özel admin site'ı kullan
simple_admin_site = SimpleAdminSite(name='simple_admin')

# Sadece Group modelini kaydet (gerekirse)
simple_admin_site.register(Group, GroupAdmin)
