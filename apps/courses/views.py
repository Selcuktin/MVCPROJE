"""
View Layer: Renders templates and handles HTTP responses.
Bu dosya ders işlemleri için template render işlemlerini yapar.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import json
import logging

logger = logging.getLogger(__name__)

from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement
from .forms import CourseForm, CourseGroupForm, AssignmentForm, SubmissionForm, AnnouncementForm, EnrollmentForm, GradeForm
from .controllers import CourseController, AssignmentController, ReportController
from apps.students.models import Student
from apps.teachers.models import Teacher

# Course Views
class CourseListView(LoginRequiredMixin, TemplateView):
    template_name = 'courses/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        controller = CourseController()
        
        # Get filters from request
        filters = {
            'search': self.request.GET.get('search'),
            'department': self.request.GET.get('department'),
            'semester': self.request.GET.get('semester')
        }
        
        courses = controller.get_course_list(self.request, filters)
        context['courses'] = courses
        return context

class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            course = self.get_object()
            
            # Derse kayıtlı öğrencileri getir (tüm gruplardan)
            enrollments = Enrollment.objects.filter(
                group__course=course,
                status='enrolled'
            ).select_related('student', 'group').order_by('student__first_name')
            
            context['enrollments'] = enrollments
            context['enrolled_count'] = enrollments.count()
            
            # Kayıtlı olmayan öğrencileri getir
            enrolled_student_ids = enrollments.values_list('student_id', flat=True)
            available_students = Student.objects.filter(
                status='active'
            ).exclude(id__in=enrolled_student_ids).order_by('first_name')
            context['available_students'] = available_students
            
            # Dersin öğretmenini getir (ilk gruptan)
            first_group = course.groups.filter(status='active').first()
            if first_group:
                context['teacher'] = first_group.teacher
            
            # Ders içeriklerini getir
            from .models import CourseContent
            contents = CourseContent.objects.filter(
                course=course,
                is_active=True
            ).order_by('week_number', 'upload_date')
            context['contents'] = contents
            
            return context
        except Exception as e:
            logger.error(f"Ders detayı yüklenirken hata: {str(e)}", exc_info=True)
            messages.error(self.request, "Ders bilgileri yüklenirken bir hata oluştu")
            return super().get_context_data(**kwargs)

class CourseCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/form.html'
    success_url = reverse_lazy('courses:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def form_valid(self, form):
        messages.success(self.request, 'Ders başarıyla oluşturuldu.')
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/form.html'
    success_url = reverse_lazy('courses:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def form_valid(self, form):
        messages.success(self.request, 'Ders başarıyla güncellendi.')
        return super().form_valid(form)

class CourseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Course
    template_name = 'courses/delete.html'
    success_url = reverse_lazy('courses:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin']

# Course Group Views
class CourseGroupListView(LoginRequiredMixin, ListView):
    model = CourseGroup
    template_name = 'courses/group_list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def get_queryset(self):
        return CourseGroup.objects.select_related('course', 'teacher').filter(status='active')

class CourseGroupDetailView(LoginRequiredMixin, DetailView):
    model = CourseGroup
    template_name = 'courses/group_detail.html'
    context_object_name = 'group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Enrollments ile birlikte notları da getir
        enrollments = group.enrollments.select_related('student')
        
        # Her enrollment için notları getir
        from apps.notes.models import Note
        enrollment_data = []
        for enrollment in enrollments:
            notes = Note.objects.filter(
                student=enrollment.student.user,  # Student nesnesinden User nesnesine geçiş
                course=group.course
            )
            
            # Notları sınav türüne göre grupla
            note_dict = {}
            for note in notes:
                note_dict[note.exam_type] = note
            
            enrollment_data.append({
                'enrollment': enrollment,
                'notes': note_dict
            })
        
        context['enrollment_data'] = enrollment_data
        context['enrollments'] = enrollments  # Geriye uyumluluk için
        context['assignments'] = group.assignments.filter(status='active')
        context['announcements'] = group.announcements.filter(status='active').order_by('-create_date')
        return context

class CourseGroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CourseGroup
    form_class = CourseGroupForm
    template_name = 'courses/group_form.html'
    success_url = reverse_lazy('courses:group_list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def form_valid(self, form):
        messages.success(self.request, 'Ders grubu başarıyla oluşturuldu.')
        return super().form_valid(form)

class CourseGroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CourseGroup
    form_class = CourseGroupForm
    template_name = 'courses/group_form.html'
    success_url = reverse_lazy('courses:group_list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def form_valid(self, form):
        messages.success(self.request, 'Ders grubu başarıyla güncellendi.')
        return super().form_valid(form)

# Enrollment Views
class EnrollmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Enrollment
    form_class = EnrollmentForm
    template_name = 'courses/enroll.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(CourseGroup, pk=self.kwargs['group_id'])
        return context
    
    def form_valid(self, form):
        group = get_object_or_404(CourseGroup, pk=self.kwargs['group_id'])
        student = Student.objects.get(user=self.request.user)
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=student, group=group).exists():
            messages.error(self.request, 'Bu derse zaten kayıtlısınız.')
            return redirect('courses:detail', pk=group.course.pk)
        
        # Check capacity
        if group.enrollments.count() >= group.course.capacity:
            messages.error(self.request, 'Bu ders grubu dolu.')
            return redirect('courses:detail', pk=group.course.pk)
        
        enrollment = form.save(commit=False)
        enrollment.student = student
        enrollment.group = group
        enrollment.save()
        
        messages.success(self.request, f'{group.course.name} dersine başarıyla kayıt oldunuz.')
        return redirect('courses:detail', pk=group.course.pk)

class EnrollmentListView(LoginRequiredMixin, ListView):
    model = Enrollment
    template_name = 'courses/enrollment_list.html'
    context_object_name = 'enrollments'
    paginate_by = 20
    
    def get_queryset(self):
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            student = Student.objects.get(user=self.request.user)
            return student.enrollments.select_related('group__course', 'group__teacher')
        else:
            return Enrollment.objects.select_related('student', 'group__course', 'group__teacher')

# Assignment Views
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'courses/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_queryset(self):
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            student = Student.objects.get(user=self.request.user)
            return Assignment.objects.filter(
                group__enrollments__student=student,
                status='active'
            ).select_related('group__course').prefetch_related('submissions', 'group__enrollments')
        elif hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            teacher = Teacher.objects.get(user=self.request.user)
            return Assignment.objects.filter(
                group__teacher=teacher
            ).select_related('group__course').prefetch_related('submissions', 'group__enrollments')
        else:
            return Assignment.objects.select_related('group__course', 'group__teacher').prefetch_related('submissions', 'group__enrollments')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Assignments are already prefetched with submissions and enrollments
        # The template will use the property methods directly
        return context

class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    template_name = 'courses/assignment_detail.html'
    context_object_name = 'assignment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
                context['submission'] = Submission.objects.filter(
                    assignment=assignment, student=student
                ).first()
                context['can_submit'] = timezone.now() <= assignment.due_date
            except Student.DoesNotExist:
                pass
        
        context['submissions'] = assignment.submissions.select_related('student')
        return context

class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'courses/assignment_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Ödev başarıyla oluşturuldu.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:assignment_list')

class AssignmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'courses/assignment_form.html'
    
    def test_func(self):
        assignment = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                assignment.group.teacher.user == self.request.user) or self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Ödev başarıyla güncellendi.')
        # Formu kaydet ve success_url'e yönlendir
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('courses:assignment_list')
    
    def form_invalid(self, form):
        # Detaylı hata mesajları için form hatalarını logla
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    error_messages.append(f"Genel hata: {error}")
                else:
                    field_label = form.fields.get(field, {}).get('label', field)
                    error_messages.append(f"{field_label}: {error}")
        
        if error_messages:
            messages.error(self.request, f"Ödev güncellenirken hatalar oluştu: {'; '.join(error_messages)}")
        else:
            messages.error(self.request, 'Ödev güncellenirken hata oluştu. Lütfen formu kontrol edin.')
        
        return super().form_invalid(form)

class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Assignment
    template_name = 'courses/assignment_delete.html'
    success_url = reverse_lazy('teachers:assignments')
    
    def test_func(self):
        assignment = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                assignment.group.teacher.user == self.request.user) or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Ödev başarıyla silindi.')
        return super().delete(request, *args, **kwargs)

# Submission Views
class SubmissionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Submission
    form_class = SubmissionForm
    template_name = 'courses/submission_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assignment'] = get_object_or_404(Assignment, pk=self.kwargs['pk'])
        return context
    
    def form_valid(self, form):
        assignment = get_object_or_404(Assignment, pk=self.kwargs['pk'])
        student = Student.objects.get(user=self.request.user)
        
        # Check if already submitted
        if Submission.objects.filter(assignment=assignment, student=student).exists():
            messages.error(self.request, 'Bu ödevi zaten teslim ettiniz.')
            return redirect('courses:assignment_detail', pk=assignment.pk)
        
        # Check deadline
        if timezone.now() > assignment.due_date:
            messages.error(self.request, 'Ödev teslim süresi dolmuş.')
            return redirect('courses:assignment_detail', pk=assignment.pk)
        
        submission = form.save(commit=False)
        submission.assignment = assignment
        submission.student = student
        submission.save()
        
        messages.success(self.request, 'Ödev başarıyla teslim edildi.')
        return redirect('courses:assignment_list')

# Announcement Views
class AnnouncementListView(LoginRequiredMixin, ListView):
    model = Announcement
    template_name = 'courses/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 20
    
    def get_queryset(self):
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            student = Student.objects.get(user=self.request.user)
            return Announcement.objects.filter(
                group__enrollments__student=student,
                status='active'
            ).select_related('group__course', 'teacher').order_by('-create_date')
        else:
            return Announcement.objects.filter(status='active').select_related('group__course', 'teacher').order_by('-create_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_student'] = hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
        
        # Get course groups for filtering (for teachers)
        if not context['is_student']:
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                from apps.courses.models import CourseGroup
                context['my_course_groups'] = CourseGroup.objects.filter(teacher=teacher, status='active')
            except Teacher.DoesNotExist:
                context['my_course_groups'] = []
        
        return context

class AnnouncementDetailView(LoginRequiredMixin, DetailView):
    model = Announcement
    template_name = 'courses/announcement_detail.html'
    context_object_name = 'announcement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_student'] = hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student'
        return context

class AnnouncementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'courses/announcement_form.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        teacher = Teacher.objects.get(user=self.request.user)
        announcement = form.save(commit=False)
        announcement.teacher = teacher
        announcement.save()
        
        messages.success(self.request, 'Duyuru başarıyla oluşturuldu.')
        return redirect('courses:announcement_list')

class AnnouncementUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'courses/announcement_form.html'
    
    def test_func(self):
        announcement = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                announcement.teacher.user == self.request.user) or self.request.user.is_staff
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Duyuru başarıyla güncellendi.')
        return redirect('courses:announcement_list')

class AnnouncementDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Announcement
    template_name = 'courses/announcement_delete.html'
    success_url = reverse_lazy('courses:announcement_list')
    
    def test_func(self):
        announcement = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                announcement.teacher.user == self.request.user) or self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Duyuru başarıyla silindi.')
        return super().delete(request, *args, **kwargs)

# Grade Management Views
class GradeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Enrollment
    form_class = GradeForm
    template_name = 'courses/grade_form.html'
    
    def test_func(self):
        enrollment = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                enrollment.group.teacher.user == self.request.user)
    
    def get_success_url(self):
        return reverse_lazy('courses:group_detail', kwargs={'pk': self.object.group.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f'{self.object.student.full_name} için notlar başarıyla güncellendi.')
        return super().form_valid(form)

# Report Views
# MVC Pattern - Views using Controllers
class StudentReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'courses/student_report.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # MVC: Controller kullanarak business logic'i çalıştır
        course_controller = CourseController()
        context['enrollments'] = Enrollment.objects.select_related('student', 'group__course').order_by('student__first_name')
        return context


# MVC Pattern - Export Functions using Controllers
@login_required
def export_student_report(request, format):
    """Export student report in specified format - MVC Pattern"""
    # Permission check
    if not (request.user.is_staff or hasattr(request.user, 'userprofile') and request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz bulunmuyor.')
        return redirect('courses:student_report')
    
    # MVC: Controller kullanarak rapor oluştur
    report_controller = ReportController()
    
    try:
        if format in ['pdf', 'excel', 'csv']:
            return report_controller.generate_student_report(request, format)
        else:
            messages.error(request, 'Geçersiz format türü.')
            return redirect('courses:student_report')
    except Exception as e:
        messages.error(request, f'Rapor oluşturulurken hata oluştu: {str(e)}')
        return redirect('courses:student_report')


@login_required
def export_course_report(request, course_id, format):
    """Export course report in specified format - MVC Pattern"""
    # Permission check
    if not (request.user.is_staff or hasattr(request.user, 'userprofile') and request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz bulunmuyor.')
        return redirect('courses:list')
    
    # MVC: Controller kullanarak rapor oluştur
    report_controller = ReportController()
    
    try:
        if format in ['pdf', 'excel', 'csv']:
            return report_controller.generate_course_report(request, course_id, format)
        else:
            messages.error(request, 'Geçersiz format türü.')
            return redirect('courses:detail', pk=course_id)
    except Exception as e:
        messages.error(request, f'Rapor oluşturulurken hata oluştu: {str(e)}')
        return redirect('courses:detail', pk=course_id)


@login_required
def export_assignment_report(request, assignment_id, format):
    """Export assignment report in specified format - MVC Pattern"""
    # Permission check
    if not (request.user.is_staff or hasattr(request.user, 'userprofile') and request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz bulunmuyor.')
        return redirect('courses:assignment_list')
    
    # MVC: Controller kullanarak rapor oluştur
    report_controller = ReportController()
    
    try:
        if format in ['pdf', 'excel', 'csv']:
            return report_controller.generate_assignment_report(request, assignment_id, format)
        else:
            messages.error(request, 'Geçersiz format türü.')
            return redirect('courses:assignment_detail', pk=assignment_id)
    except Exception as e:
        messages.error(request, f'Rapor oluşturulurken hata oluştu: {str(e)}')
        return redirect('courses:assignment_detail', pk=assignment_id)

class CourseReportView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'courses/course_report.html'
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin', 'teacher']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.annotate(
            enrollment_count=Count('groups__enrollments')
        ).order_by('code')
        return context

# AJAX Views
@login_required
@csrf_exempt
def update_grade_ajax(request):
    """AJAX endpoint for inline grade updates"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    # Check if user is teacher
    if not (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'teacher'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        data = json.loads(request.body)
        enrollment_id = data.get('enrollment_id')
        grade_type = data.get('grade_type')
        score = data.get('score')
        
        # Validate input
        if not all([enrollment_id, grade_type, score is not None]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        try:
            score = float(score)
            if score < 0 or score > 100:
                return JsonResponse({'success': False, 'error': 'Score must be between 0 and 100'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid score format'})
        
        # Get enrollment
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Enrollment not found'})
        
        # Check if teacher owns this course
        teacher = Teacher.objects.get(user=request.user)
        if enrollment.group.teacher != teacher:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Update or create note
        from apps.notes.models import Note
        
        # First update the enrollment model
        if grade_type == 'vize':
            enrollment.midterm_grade = score
        elif grade_type == 'final':
            enrollment.final_grade = score
        elif grade_type == 'but':
            enrollment.makeup_grade = score
        else:
            return JsonResponse({'success': False, 'error': 'Invalid grade type'})
        
        enrollment.save()  # This will auto-calculate letter grade
        
        # Also update/create the Note model for consistency
        note, created = Note.objects.update_or_create(
            student=enrollment.student.user,
            course=enrollment.group.course,
            exam_type=grade_type,
            defaults={
                'score': int(score),
                'teacher': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'letter_grade': enrollment.grade,
            'message': 'Grade updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Teacher profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def add_student_to_course(request, course_pk):
    """Derse öğrenci ekle"""
    if request.method != 'POST':
        return redirect('courses:detail', pk=course_pk)
    
    # Yetki kontrolü
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:detail', pk=course_pk)
    
    course = get_object_or_404(Course, pk=course_pk)
    student_id = request.POST.get('student_id')
    
    if not student_id:
        messages.error(request, 'Lütfen bir öğrenci seçin.')
        return redirect('courses:detail', pk=course_pk)
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Dersin aktif bir grubu var mı kontrol et
        group = course.groups.filter(status='active').first()
        
        if not group:
            messages.error(request, 'Bu ders için aktif bir grup bulunamadı. Önce grup oluşturun.')
            return redirect('courses:detail', pk=course_pk)
        
        # Öğrenci zaten kayıtlı mı kontrol et
        existing = Enrollment.objects.filter(
            student=student,
            group__course=course,
            status='enrolled'
        ).exists()
        
        if existing:
            messages.warning(request, f'{student.full_name} zaten bu derse kayıtlı.')
            return redirect('courses:detail', pk=course_pk)
        
        # Kapasite kontrolü
        enrolled_count = Enrollment.objects.filter(
            group__course=course,
            status='enrolled'
        ).count()
        
        if enrolled_count >= course.capacity:
            messages.error(request, 'Ders kapasitesi dolu.')
            return redirect('courses:detail', pk=course_pk)
        
        # Öğrenciyi ekle
        Enrollment.objects.create(
            student=student,
            group=group,
            status='enrolled'
        )
        
        messages.success(request, f'{student.full_name} derse başarıyla eklendi.')
        
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci bulunamadı.')
    except Exception as e:
        messages.error(request, f'Bir hata oluştu: {str(e)}')
    
    return redirect('courses:detail', pk=course_pk)

@login_required
def remove_student_from_course(request, course_pk, student_id):
    """Dersten öğrenci çıkar"""
    if request.method != 'POST':
        return redirect('courses:detail', pk=course_pk)
    
    # Yetki kontrolü
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:detail', pk=course_pk)
    
    course = get_object_or_404(Course, pk=course_pk)
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Öğrencinin kaydını bul ve sil
        enrollment = Enrollment.objects.filter(
            student=student,
            group__course=course,
            status='enrolled'
        ).first()
        
        if not enrollment:
            messages.warning(request, f'{student.full_name} bu derse kayıtlı değil.')
            return redirect('courses:detail', pk=course_pk)
        
        enrollment.delete()
        messages.success(request, f'{student.full_name} dersten başarıyla çıkarıldı.')
        
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci bulunamadı.')
    except Exception as e:
        messages.error(request, f'Bir hata oluştu: {str(e)}')
    
    return redirect('courses:detail', pk=course_pk)

# Course Content Views
@login_required
def course_content_create(request, course_pk):
    """Derse içerik ekle"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:detail', pk=course_pk)
    
    course = get_object_or_404(Course, pk=course_pk)
    
    if request.method == 'POST':
        from .forms import CourseContentForm
        from .models import CourseContent
        form = CourseContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.course = course
            content.save()
            messages.success(request, 'İçerik başarıyla eklendi.')
            return redirect('courses:detail', pk=course_pk)
    else:
        from .forms import CourseContentForm
        form = CourseContentForm()
    
    return render(request, 'courses/content_form.html', {
        'form': form,
        'course': course,
        'title': 'İçerik Ekle'
    })

@login_required
def course_content_update(request, pk):
    """İçeriği güncelle"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:list')
    
    from .models import CourseContent
    content = get_object_or_404(CourseContent, pk=pk)
    
    if request.method == 'POST':
        from .forms import CourseContentForm
        form = CourseContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, 'İçerik başarıyla güncellendi.')
            return redirect('courses:detail', pk=content.course.pk)
    else:
        from .forms import CourseContentForm
        form = CourseContentForm(instance=content)
    
    return render(request, 'courses/content_form.html', {
        'form': form,
        'course': content.course,
        'title': 'İçerik Düzenle',
        'content': content
    })

@login_required
def course_content_delete(request, pk):
    """İçeriği sil"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:list')
    
    from .models import CourseContent
    content = get_object_or_404(CourseContent, pk=pk)
    course_pk = content.course.pk
    
    if request.method == 'POST':
        content.delete()
        messages.success(request, 'İçerik başarıyla silindi.')
        return redirect('courses:detail', pk=course_pk)
    
    return render(request, 'courses/content_delete.html', {
        'content': content,
        'course': content.course
    })