"""
Academic Term Service Layer
Business logic for academic term operations
"""
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from .models import AcademicTerm


class AcademicTermService:
    """Service for academic term operations"""
    
    def get_active_term(self):
        """Get the currently active academic term"""
        return AcademicTerm.get_active_term()
    
    def get_current_term(self):
        """Get the term that is currently running by date"""
        return AcademicTerm.get_current_term()
    
    def get_upcoming_terms(self, limit=3):
        """Get upcoming academic terms"""
        today = timezone.now().date()
        return AcademicTerm.objects.filter(
            start_date__gt=today
        ).order_by('start_date')[:limit]
    
    def get_past_terms(self, limit=5):
        """Get past academic terms"""
        today = timezone.now().date()
        return AcademicTerm.objects.filter(
            end_date__lt=today
        ).order_by('-end_date')[:limit]
    
    def get_terms_by_year(self, year):
        """Get all terms for a specific academic year"""
        return AcademicTerm.objects.filter(
            Q(year_start=year) | Q(year_end=year)
        ).order_by('start_date')
    
    def get_term_with_courses(self, term_id):
        """Get term with related course groups"""
        try:
            term = AcademicTerm.objects.prefetch_related(
                Prefetch('course_groups',
                         queryset=CourseGroup.objects.select_related(
                             'course', 'teacher'
                         ).filter(status='active'))
            ).get(id=term_id)
            
            return {
                'success': True,
                'term': term,
                'course_count': term.course_groups.count()
            }
        except AcademicTerm.DoesNotExist:
            return {
                'success': False,
                'error': 'Dönem bulunamadı'
            }
    
    def create_term(self, data):
        """Create new academic term"""
        try:
            term = AcademicTerm.objects.create(**data)
            return {
                'success': True,
                'term': term,
                'message': f'{term.name} dönemi oluşturuldu'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def activate_term(self, term_id):
        """Activate a specific term"""
        try:
            term = AcademicTerm.objects.get(id=term_id)
            term.activate()
            return {
                'success': True,
                'term': term,
                'message': f'{term.name} aktif dönem olarak ayarlandı'
            }
        except AcademicTerm.DoesNotExist:
            return {
                'success': False,
                'error': 'Dönem bulunamadı'
            }
    
    def complete_term(self, term_id):
        """Mark term as completed"""
        try:
            term = AcademicTerm.objects.get(id=term_id)
            term.complete()
            return {
                'success': True,
                'term': term,
                'message': f'{term.name} tamamlandı olarak işaretlendi'
            }
        except AcademicTerm.DoesNotExist:
            return {
                'success': False,
                'error': 'Dönem bulunamadı'
            }
    
    def archive_term(self, term_id):
        """Archive a term"""
        try:
            term = AcademicTerm.objects.get(id=term_id)
            
            # Check if term can be archived
            if term.is_active:
                return {
                    'success': False,
                    'error': 'Aktif dönem arşivlenemez'
                }
            
            term.archive()
            return {
                'success': True,
                'term': term,
                'message': f'{term.name} arşivlendi'
            }
        except AcademicTerm.DoesNotExist:
            return {
                'success': False,
                'error': 'Dönem bulunamadı'
            }
    
    def get_term_statistics(self, term_id):
        """Get statistics for a specific term"""
        try:
            from apps.courses.models import CourseGroup, Enrollment
            
            term = AcademicTerm.objects.get(id=term_id)
            
            # Get course groups for this term
            course_groups = CourseGroup.objects.filter(
                academic_term=term,
                status='active'
            )
            
            # Calculate statistics
            total_courses = course_groups.count()
            total_students = Enrollment.objects.filter(
                group__in=course_groups,
                status='enrolled'
            ).values('student').distinct().count()
            
            total_teachers = course_groups.values('teacher').distinct().count()
            
            return {
                'success': True,
                'term': term,
                'statistics': {
                    'total_courses': total_courses,
                    'total_students': total_students,
                    'total_teachers': total_teachers,
                    'is_active': term.is_active,
                    'is_current': term.is_current,
                    'is_registration_open': term.is_registration_open,
                    'days_remaining': term.days_remaining if term.is_current else 0
                }
            }
        except AcademicTerm.DoesNotExist:
            return {
                'success': False,
                'error': 'Dönem bulunamadı'
            }
    
    def get_registration_status(self):
        """Get current registration status"""
        active_term = self.get_active_term()
        
        if not active_term:
            return {
                'is_open': False,
                'message': 'Aktif dönem yok'
            }
        
        if active_term.is_registration_open:
            days_left = (active_term.registration_end - timezone.now().date()).days
            return {
                'is_open': True,
                'term': active_term,
                'message': f'Kayıt dönemi açık ({days_left} gün kaldı)',
                'days_left': days_left
            }
        else:
            return {
                'is_open': False,
                'term': active_term,
                'message': 'Kayıt dönemi kapalı'
            }


# Import CourseGroup here to avoid circular import
from apps.courses.models import CourseGroup
