"""
Controller Layer: Handles request routing and response context generation.
Bu dosya not işlemleri için HTTP isteklerini yönlendirir ve context oluşturur.
"""
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse

from .models import Note
from .forms import NoteFilterForm
from .services import NoteService


class NoteController:
    """Note request handling controller"""
    
    def __init__(self):
        self.note_service = NoteService()
    
    def get_note_list_context(self, request):
        """Get context for note list view"""
        user = request.user
        
        # Check if user is student
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'student':
            notes = self.note_service.get_student_notes(user)
            filter_form = None
            structured_data = None
        else:
            # Get filters from request
            filters = {
                'course': request.GET.get('course'),
                'exam_type': request.GET.get('exam_type'),
                'grade': request.GET.get('grade')
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v}
            
            notes = self.note_service.get_all_notes_with_filters(filters, user)
            filter_form = NoteFilterForm(request.GET, user=user)
            
            # Get structured data for teacher view
            structured_data = self.note_service.get_structured_notes_data(notes)
        
        # Apply search
        search_query = request.GET.get('search')
        if search_query:
            notes = self.note_service.search_notes(notes, search_query)
        
        return {
            'notes': notes,
            'structured_data': structured_data,
            'filter_form': filter_form,
            'search_query': search_query,
            'is_student': hasattr(user, 'userprofile') and user.userprofile.user_type == 'student'
        }
    
    def get_note_detail_context(self, request, note_id):
        """Get context for note detail view"""
        note = self.note_service.get_note_detail(note_id)
        
        # Check permission
        if not self.note_service.check_note_permission(note, request.user):
            messages.error(request, 'Bu nota erişim yetkiniz yok.')
            return {'error': True, 'redirect': 'notes:list'}
        
        return {
            'note': note,
            'is_student': hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student'
        }
    
    def create_note_context(self, request, form_data=None):
        """Handle note creation"""
        # Check permission
        if not self.note_service.can_modify_notes(request.user):
            messages.error(request, 'Not oluşturma yetkiniz yok.')
            return {'error': True, 'redirect': 'notes:list'}
        
        if form_data:
            try:
                note = self.note_service.create_note(form_data, request.user)
                messages.success(request, 'Not başarıyla oluşturuldu!')
                return {'success': True, 'note': note}
            except Exception as e:
                messages.error(request, f'Not oluşturulurken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        # Get initial data from URL parameters
        initial_data = {}
        if request.GET.get('course'):
            initial_data['course'] = request.GET.get('course')
        if request.GET.get('student'):
            initial_data['student'] = request.GET.get('student')
        if request.GET.get('exam_type'):
            initial_data['exam_type'] = request.GET.get('exam_type')
        
        return {
            'title': 'Yeni Not Oluştur',
            'initial_data': initial_data
        }
    
    def update_note_context(self, request, note_id, form_data=None):
        """Handle note update"""
        # Check permission
        if not self.note_service.can_modify_notes(request.user):
            messages.error(request, 'Not düzenleme yetkiniz yok.')
            return {'error': True, 'redirect': 'notes:list'}
        
        note = get_object_or_404(Note, pk=note_id)
        
        if form_data:
            try:
                updated_note = self.note_service.update_note(note_id, form_data)
                messages.success(request, 'Not başarıyla güncellendi!')
                return {'success': True, 'note': updated_note}
            except Exception as e:
                messages.error(request, f'Not güncellenirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {
            'note': note,
            'title': 'Not Düzenle'
        }
    
    def delete_note_context(self, request, note_id):
        """Handle note deletion"""
        # Check permission
        if not self.note_service.can_modify_notes(request.user):
            messages.error(request, 'Not silme yetkiniz yok.')
            return {'error': True, 'redirect': 'notes:list'}
        
        note = get_object_or_404(Note, pk=note_id)
        
        if request.method == 'POST':
            try:
                self.note_service.delete_note(note_id)
                messages.success(request, 'Not başarıyla silindi!')
                return {'success': True}
            except Exception as e:
                messages.error(request, f'Not silinirken hata oluştu: {str(e)}')
                return {'success': False, 'error': str(e)}
        
        return {'note': note}
    
    def get_students_by_course_ajax(self, request):
        """Handle AJAX request for students by course"""
        course_id = request.GET.get('course_id')
        
        if course_id:
            students_list = self.note_service.get_students_by_course(course_id)
            return JsonResponse({'students': students_list})
        
        return JsonResponse({'students': []})
    
    def get_note_statistics_context(self, request, user=None, course=None):
        """Get note statistics context"""
        stats = self.note_service.get_note_statistics(user, course)
        
        return {
            'statistics': stats,
            'user': user,
            'course': course
        }