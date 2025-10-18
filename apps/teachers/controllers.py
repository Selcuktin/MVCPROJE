"""
Controller Layer: Handles request routing and response context generation.
Bu dosya öğretmen işlemleri için HTTP isteklerini yönlendirir ve context oluşturur.
"""
from django.shortcuts import get_object_or_404
from django.contrib import messages

from .models import Teacher
from .services import TeacherService


class TeacherController:
    """Teacher request handling controller"""
    
    def __init__(self):
        self.teacher_service = TeacherService()
    
    def get_teacher_list_context(self, request):
        """Get context for teacher list view"""
        # Get filters from request
        filters = {
            'search': request.GET.get('search'),
            'department': request.GET.get('department'),
            'status': request.GET.get('status')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        teachers = self.teacher_service.get_filtered_teachers(filters)
        
        return {
            'teachers': teachers,
            'search_query': filters.get('search', ''),
            'department_filter': filters.get('department', ''),
            'status_filter': filters.get('status', '')
        }
    
    def get_teacher_detail_context(self, request, teacher_id):
        """Get context for teacher detail view"""
        data = self.teacher_service.get_teacher_detail(teacher_id)
        return data
    
    def get_teacher_dashboard_context(self, request):
        """Get context for teacher dashboard"""
        data = self.teacher_service.get_teacher_dashboard_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def get_teacher_courses_context(self, request):
        """Get context for teacher courses view"""
        data = self.teacher_service.get_teacher_courses_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def get_teacher_students_context(self, request):
        """Get context for teacher students view"""
        data = self.teacher_service.get_teacher_students_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def get_teacher_assignments_context(self, request):
        """Get context for teacher assignments view"""
        data = self.teacher_service.get_teacher_assignments_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def get_teacher_announcements_context(self, request):
        """Get context for teacher announcements view"""
        data = self.teacher_service.get_teacher_announcements_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def create_teacher_context(self, request, form_data=None):
        """Handle teacher creation"""
        if form_data:
            try:
                teacher = self.teacher_service.create_teacher(form_data)
                messages.success(request, 'Öğretmen başarıyla oluşturuldu.')
                return {'success': True, 'teacher': teacher}
            except Exception as e:
                messages.error(request, f'Öğretmen oluşturulurken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'form_title': 'Yeni Öğretmen Oluştur'}
    
    def update_teacher_context(self, request, teacher_id, form_data=None):
        """Handle teacher update"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        if form_data:
            try:
                updated_teacher = self.teacher_service.update_teacher(teacher_id, form_data)
                messages.success(request, 'Öğretmen bilgileri başarıyla güncellendi.')
                return {'success': True, 'teacher': updated_teacher}
            except Exception as e:
                messages.error(request, f'Öğretmen güncellenirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {
            'teacher': teacher,
            'form_title': 'Öğretmen Bilgilerini Güncelle'
        }
    
    def delete_teacher_context(self, request, teacher_id):
        """Handle teacher deletion"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        
        if request.method == 'POST':
            try:
                self.teacher_service.delete_teacher(teacher_id)
                messages.success(request, 'Öğretmen başarıyla silindi.')
                return {'success': True}
            except Exception as e:
                messages.error(request, f'Öğretmen silinirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'teacher': teacher}
    
    def get_teacher_statistics_context(self, request, teacher_id):
        """Get teacher statistics context"""
        teacher = get_object_or_404(Teacher, pk=teacher_id)
        stats = self.teacher_service.get_teacher_statistics(teacher)
        
        return {
            'teacher': teacher,
            'statistics': stats
        }