"""
Service Layer: Business logic and data processing operations.
Bu dosya not işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q
from collections import defaultdict

from .models import Note
from apps.courses.models import Course
from apps.users.models import User


class NoteService:
    """Note business logic service"""
    
    def get_student_notes(self, user):
        """Get notes for a specific student"""
        # Sınav türü sıralaması: vize, final, but
        notes = Note.objects.filter(student=user).extra(
            select={'exam_order': "CASE WHEN exam_type='vize' THEN 1 WHEN exam_type='final' THEN 2 WHEN exam_type='but' THEN 3 ELSE 4 END"}
        ).order_by('course__name', 'exam_order')
        
        return notes
    
    def get_all_notes_with_filters(self, filters, user):
        """Get all notes with applied filters for teachers/admins"""
        notes = Note.objects.all().extra(
            select={'exam_order': "CASE WHEN exam_type='vize' THEN 1 WHEN exam_type='final' THEN 2 WHEN exam_type='but' THEN 3 ELSE 4 END"}
        ).order_by('student__first_name', 'course__name', 'exam_order')
        
        # Apply filters
        if filters.get('course'):
            notes = notes.filter(course_id=filters['course'])
        if filters.get('exam_type'):
            notes = notes.filter(exam_type=filters['exam_type'])
        if filters.get('grade'):
            notes = notes.filter(grade=filters['grade'])
        
        return notes
    
    def search_notes(self, notes, search_query):
        """Apply search filter to notes"""
        if search_query:
            notes = notes.filter(
                Q(course__name__icontains=search_query) |
                Q(course__code__icontains=search_query) |
                Q(student__first_name__icontains=search_query) |
                Q(student__last_name__icontains=search_query)
            )
        return notes
    
    def get_structured_notes_data(self, notes):
        """Get structured notes data for teacher view"""
        # Öğrenci bazlı gruplandırma
        student_data = defaultdict(lambda: defaultdict(dict))
        
        for note in notes:
            student_data[note.student][note.course][note.exam_type] = note
        
        # Her öğrenci ve ders için eksik sınav türlerini ekle
        structured_data = []
        for student, courses in student_data.items():
            student_courses = []
            for course, exams in courses.items():
                course_exams = {
                    'course': course,
                    'vize': exams.get('vize'),
                    'final': exams.get('final'),
                    'but': exams.get('but'),
                }
                student_courses.append(course_exams)
            
            structured_data.append({
                'student': student,
                'courses': student_courses
            })
        
        return structured_data
    
    def get_note_detail(self, note_id):
        """Get note detail"""
        note = Note.objects.get(id=note_id)
        return note
    
    def create_note(self, form_data, teacher_user):
        """Create new note"""
        note = Note.objects.create(
            teacher=teacher_user,
            **form_data
        )
        return note
    
    def update_note(self, note_id, form_data):
        """Update existing note"""
        note = Note.objects.get(id=note_id)
        for key, value in form_data.items():
            setattr(note, key, value)
        note.save()
        return note
    
    def delete_note(self, note_id):
        """Delete note"""
        note = Note.objects.get(id=note_id)
        note.delete()
        return True
    
    def get_students_by_course(self, course_id):
        """Get students enrolled in a specific course"""
        try:
            course = Course.objects.get(id=course_id)
            # Bu derse kayıtlı öğrencileri getir
            from apps.students.models import Student
            enrolled_students = Student.objects.filter(
                enrollments__group__course=course,
                enrollments__status='enrolled'  # Sadece aktif kayıtlı öğrenciler
            ).distinct()
            
            students_list = [
                {
                    'id': student.user.id, 
                    'name': f"{student.first_name} {student.last_name}"
                } 
                for student in enrolled_students
            ]
            
            return students_list
        except Course.DoesNotExist:
            return []
    
    def check_note_permission(self, note, user):
        """Check if user has permission to access note"""
        # Öğrenciler sadece kendi notlarını görebilir
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'student':
            return note.student == user
        
        # Öğretmenler ve adminler tüm notları görebilir
        return True
    
    def can_modify_notes(self, user):
        """Check if user can create/edit/delete notes"""
        # Öğrenciler not oluşturamaz/düzenleyemez/silemez
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'student':
            return False
        return True
    
    def get_note_statistics(self, user=None, course=None):
        """Get note statistics"""
        queryset = Note.objects.all()
        
        if user:
            queryset = queryset.filter(student=user)
        
        if course:
            queryset = queryset.filter(course=course)
        
        total_notes = queryset.count()
        
        # Grade distribution
        grade_counts = {
            'AA': queryset.filter(grade='AA').count(),
            'BA': queryset.filter(grade='BA').count(),
            'BB': queryset.filter(grade='BB').count(),
            'CB': queryset.filter(grade='CB').count(),
            'CC': queryset.filter(grade='CC').count(),
            'DC': queryset.filter(grade='DC').count(),
            'DD': queryset.filter(grade='DD').count(),
            'FD': queryset.filter(grade='FD').count(),
            'FF': queryset.filter(grade='FF').count(),
        }
        
        # Exam type distribution
        exam_type_counts = {
            'vize': queryset.filter(exam_type='vize').count(),
            'final': queryset.filter(exam_type='final').count(),
            'but': queryset.filter(exam_type='but').count(),
        }
        
        # Average score
        scores = [note.score for note in queryset if note.score is not None]
        average_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_notes': total_notes,
            'grade_distribution': grade_counts,
            'exam_type_distribution': exam_type_counts,
            'average_score': round(average_score, 2)
        }