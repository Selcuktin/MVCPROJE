from django.contrib import admin
from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement, CourseContent

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'department', 'semester', 'capacity', 'is_elective', 'status']
    list_filter = ['department', 'semester', 'is_elective', 'status', 'credits']
    search_fields = ['code', 'name', 'department']

@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ['course', 'teacher', 'semester', 'classroom', 'status']
    list_filter = ['semester', 'status', 'course__department']
    search_fields = ['course__code', 'course__name', 'teacher__first_name', 'teacher__last_name']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'group', 'enrollment_date', 'attendance', 'grade', 'status']
    list_filter = ['status', 'grade', 'enrollment_date', 'group__course__department']
    search_fields = ['student__first_name', 'student__last_name', 'group__course__code']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'create_date', 'due_date', 'max_score', 'status']
    list_filter = ['status', 'create_date', 'due_date', 'group__course__department']
    search_fields = ['title', 'group__course__code']

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'submission_date', 'score', 'status']
    list_filter = ['status', 'submission_date', 'assignment__group__course__department']
    search_fields = ['student__first_name', 'student__last_name', 'assignment__title']

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'teacher', 'create_date', 'expire_date', 'status']
    list_filter = ['status', 'create_date', 'group__course__department']
    search_fields = ['title', 'content', 'group__course__code']

@admin.register(CourseContent)
class CourseContentAdmin(admin.ModelAdmin):
    list_display = ['course', 'week_number', 'title', 'content_type', 'upload_date', 'is_active']
    list_filter = ['content_type', 'is_active', 'week_number', 'course__department']
    search_fields = ['title', 'description', 'course__code', 'course__name']
    ordering = ['course', 'week_number']