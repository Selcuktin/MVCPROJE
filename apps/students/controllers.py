"""
Controller Layer: Handles request routing and response context generation.
Bu dosya öğrenci işlemleri için HTTP isteklerini yönlendirir ve context oluşturur.
"""
from django.shortcuts import get_object_or_404
from django.contrib import messages

from .models import Student
from .services import StudentService


class StudentController:
    """Student request handling controller"""
    
    def __init__(self):
        self.student_service = StudentService()
    
    def get_student_list_context(self, request):
        """Get context for student list view"""
        # Get filters from request
        filters = {
            'search': request.GET.get('search'),
            'status': request.GET.get('status')
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        students = self.student_service.get_filtered_students(filters)
        
        return {
            'students': students,
            'search_query': filters.get('search', ''),
            'status_filter': filters.get('status', '')
        }
    
    def get_student_detail_context(self, request, student_id):
        """Get context for student detail view"""
        data = self.student_service.get_student_detail(student_id)
        return data
    
    def get_student_dashboard_context(self, request):
        """Get context for student dashboard"""
        data = self.student_service.get_student_dashboard_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def get_student_courses_context(self, request):
        """Get context for student courses view"""
        data = self.student_service.get_student_courses_data(request.user)
        
        if 'error' in data:
            messages.error(request, data['error'])
            return {'error': True}
        
        return data
    
    def create_student_context(self, request, form_data=None):
        """Handle student creation"""
        if form_data:
            try:
                student = self.student_service.create_student(form_data)
                messages.success(request, 'Öğrenci başarıyla oluşturuldu.')
                return {'success': True, 'student': student}
            except Exception as e:
                messages.error(request, f'Öğrenci oluşturulurken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'form_title': 'Yeni Öğrenci Oluştur'}
    
    def update_student_context(self, request, student_id, form_data=None):
        """Handle student update"""
        student = get_object_or_404(Student, pk=student_id)
        
        if form_data:
            try:
                updated_student = self.student_service.update_student(student_id, form_data)
                messages.success(request, 'Öğrenci bilgileri başarıyla güncellendi.')
                return {'success': True, 'student': updated_student}
            except Exception as e:
                messages.error(request, f'Öğrenci güncellenirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {
            'student': student,
            'form_title': 'Öğrenci Bilgilerini Güncelle'
        }
    
    def delete_student_context(self, request, student_id):
        """Handle student deletion"""
        student = get_object_or_404(Student, pk=student_id)
        
        if request.method == 'POST':
            try:
                self.student_service.delete_student(student_id)
                messages.success(request, 'Öğrenci başarıyla silindi.')
                return {'success': True}
            except Exception as e:
                messages.error(request, f'Öğrenci silinirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'student': student}
    
    def get_student_statistics_context(self, request, student_id):
        """Get student statistics context"""
        student = get_object_or_404(Student, pk=student_id)
        stats = self.student_service.get_student_statistics(student)
        
        return {
            'student': student,
            'statistics': stats
        }