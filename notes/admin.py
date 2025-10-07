from django.contrib import admin
from .models import Note

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'teacher', 'exam_type', 'grade', 'score', 'created_at']
    list_filter = ['exam_type', 'grade', 'course', 'created_at']
    search_fields = ['course__name', 'course__code', 'student__username', 'student__first_name', 'student__last_name', 'teacher__username']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['grade']  # Harf notu otomatik hesaplandığı için sadece okunabilir
