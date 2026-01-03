"""
Notes Admin - Basit Not Yönetimi
"""
from django.contrib import admin
from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """Not Yönetimi - Basit"""
    
    list_display = [
        'student_name',
        'course_name',
        'exam_type',
        'score',
        'grade',
    ]
    
    list_filter = ['exam_type', 'grade', 'course']
    
    search_fields = [
        'student__first_name',
        'student__last_name',
        'course__name',
        'course__code',
    ]
    
    def student_name(self, obj):
        """Öğrenci adı"""
        return obj.student.get_full_name()
    student_name.short_description = 'Öğrenci'
    
    def course_name(self, obj):
        """Ders adı"""
        return f"{obj.course.code} - {obj.course.name}"
    course_name.short_description = 'Ders'
