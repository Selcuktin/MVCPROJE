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
from django.db.models import Count, Q
import json
import logging

logger = logging.getLogger(__name__)

from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement, ExampleQuestion, Quiz, QuizQuestion, QuizChoice
from .forms import CourseForm, CourseGroupForm, AssignmentForm, SubmissionForm, AnnouncementForm, EnrollmentForm, GradeForm, ExampleQuestionForm, QuizFromFileForm
from .controllers import CourseController, AssignmentController, ReportController, TeacherCourseAssignmentController
from apps.students.models import Student
from apps.teachers.models import Teacher

# Course Views
class CourseListView(LoginRequiredMixin, TemplateView):
    template_name = 'courses/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filters from request
        filters = {
            'search': self.request.GET.get('search'),
            'department': self.request.GET.get('department'),
            'semester': self.request.GET.get('semester')
        }
        
        # Kullanıcı tipini belirle
        user_type = None
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile:
            user_type = self.request.user.userprofile.user_type
        
        # Öğretmen ise SADECE kendi derslerini göster
        if user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                # Öğretmenin ders gruplarından dersleri al
                course_ids = CourseGroup.objects.filter(
                    teacher=teacher,
                    status='active'
                ).values_list('course_id', flat=True).distinct()
                
                courses = Course.objects.filter(id__in=course_ids)
                
                # Apply filters
                if filters.get('search'):
                    courses = courses.filter(
                        Q(name__icontains=filters['search']) |
                        Q(code__icontains=filters['search'])
                    )
                if filters.get('department'):
                    courses = courses.filter(department__icontains=filters['department'])
                if filters.get('semester'):
                    courses = courses.filter(semester=filters['semester'])
                
                context['courses'] = courses.order_by('code')
            except Teacher.DoesNotExist:
                context['courses'] = Course.objects.none()
        else:
            # Admin, staff veya öğrenci için tüm aktif dersler
            controller = CourseController()
            courses = controller.get_course_list(self.request, filters)
            context['courses'] = courses
        
        return context

# Quiz Views
class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'courses/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        qs = Quiz.objects.select_related('course', 'created_by')
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            teacher = Teacher.objects.get(user=self.request.user)
            qs = qs.filter(created_by=teacher)
        elif hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            # öğrenciye kayıtlı olduğu dersler
            student = Student.objects.get(user=self.request.user)
            qs = qs.filter(course__groups__enrollments__student=student, is_published=True).distinct()
        return qs.order_by('-created_at')


class QuizCreateFromFileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'courses/quiz_from_file.html'

    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'

    def get(self, request):
        form = QuizFromFileForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = QuizFromFileForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.cleaned_data['course']
            title = form.cleaned_data['title']
            quiz_type = form.cleaned_data['quiz_type']
            duration = form.cleaned_data['duration_minutes']
            f = request.FILES['file']
            from .services import parse_quiz_from_text, parse_quiz_from_docx, parse_quiz_from_pdf, create_quiz_from_items
            name = (f.name or '').lower()
            if name.endswith('.txt'):
                text = f.read().decode('utf-8', errors='ignore')
                items = parse_quiz_from_text(text)
            elif name.endswith('.docx'):
                items = parse_quiz_from_docx(f)
            elif name.endswith('.pdf'):
                items = parse_quiz_from_pdf(f)
            else:
                messages.error(request, 'Desteklenmeyen dosya türü.')
                return render(request, self.template_name, {'form': form})
            teacher = Teacher.objects.get(user=request.user)
            quiz = create_quiz_from_items(course, teacher, title, quiz_type, items, duration_minutes=duration)
            messages.success(request, f"Quiz oluşturuldu: {quiz.title} ({len(items)} soru)")
            return redirect('courses:quiz_list')
        return render(request, self.template_name, {'form': form})


class QuizDetailView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'courses/quiz_detail.html'
    context_object_name = 'quiz'

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
        return self.request.user.is_staff or (hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin'])
    
    def form_valid(self, form):
        messages.success(self.request, 'Ders başarıyla oluşturuldu.')
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Course
    form_class = CourseForm
    template_name = 'courses/form.html'
    success_url = reverse_lazy('courses:list')
    
    def test_func(self):
        return self.request.user.is_staff or (hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin'])
    
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
        # Öğretmen ise SADECE kendi ders gruplarını göster
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=self.request.user)
                return CourseGroup.objects.filter(
                    teacher=teacher,
                    status='active'
                ).select_related('course', 'teacher')
            except Teacher.DoesNotExist:
                return CourseGroup.objects.none()
        else:
            # Admin veya öğrenci için tüm gruplar
            return CourseGroup.objects.select_related('course', 'teacher').filter(status='active')

class CourseGroupDetailView(LoginRequiredMixin, DetailView):
    model = CourseGroup
    template_name = 'courses/group_detail.html'
    context_object_name = 'group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
        # Optimize with Prefetch to avoid N+1 queries
        from apps.notes.models import Note
        from django.db.models import Prefetch
        
        notes_prefetch = Prefetch(
            'student__user__student_notes',
            queryset=Note.objects.filter(course=group.course).select_related('course'),
            to_attr='course_notes_list'
        )
        
        enrollments = group.enrollments.select_related(
            'student', 
            'student__user'
        ).prefetch_related(notes_prefetch)
        
        # Process enrollment data
        enrollment_data = []
        for enrollment in enrollments:
            # Get notes from prefetched data
            notes = getattr(enrollment.student.user, 'course_notes_list', [])
            
            # Group notes by exam type
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
    
    def get_queryset(self):
        return Enrollment.objects.select_related('student', 'group__course', 'group__teacher')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Tüm aktif öğrenciler
        students = Student.objects.filter(status='active').order_by('first_name', 'last_name')
        
        # Tüm aktif ders grupları
        all_groups = CourseGroup.objects.filter(status='active').select_related('course', 'teacher').order_by('course__code')
        
        # Her öğrenci için ders kayıt durumlarını hazırla
        students_with_courses = []
        
        for student in students:
            # Bu öğrencinin kayıtlı olduğu grupları al
            enrolled_groups = Enrollment.objects.filter(
                student=student,
                status='enrolled'
            ).values_list('group_id', flat=True)
            
            # Enrollment ID'lerini de al
            enrollment_map = {}
            for enrollment in Enrollment.objects.filter(student=student, status='enrolled'):
                enrollment_map[enrollment.group_id] = enrollment.id
            
            # Her grup için kayıt durumunu belirle
            courses = []
            for group in all_groups:
                is_enrolled = group.id in enrolled_groups
                courses.append({
                    'group': group,
                    'is_enrolled': is_enrolled,
                    'enrollment_id': enrollment_map.get(group.id)
                })
            
            students_with_courses.append({
                'student': student,
                'courses': courses,
                'enrolled_count': len(enrolled_groups)
            })
        
        context['students_with_courses'] = students_with_courses
        
        # Stats
        context['student_count'] = students.count()
        context['course_count'] = all_groups.count()
        context['total_enrollments'] = Enrollment.objects.count()
        context['enrolled_count'] = Enrollment.objects.filter(status='enrolled').count()
        
        # Current filters
        context['search_query'] = self.request.GET.get('search', '')
        context['course_filter'] = self.request.GET.get('course', '')
        context['status_filter'] = self.request.GET.get('status', '')
        
        return context


@login_required
def enrollment_add(request):
    """Add new enrollment"""
    if request.method == 'POST':
        student_id = request.POST.get('student')
        group_id = request.POST.get('group')
        status = request.POST.get('status', 'enrolled')
        
        try:
            student = Student.objects.get(id=student_id)
            group = CourseGroup.objects.get(id=group_id)
            
            # Check if already enrolled
            if Enrollment.objects.filter(student=student, group=group).exists():
                messages.error(request, 'Bu öğrenci zaten bu derse kayıtlı.')
            else:
                Enrollment.objects.create(
                    student=student,
                    group=group,
                    status=status
                )
                messages.success(request, f'{student.first_name} {student.last_name} başarıyla {group.course.name} dersine kaydedildi.')
        except Exception as e:
            messages.error(request, f'Kayıt eklenirken hata oluştu: {str(e)}')
    
    return redirect('courses:enrollment_list')


@login_required
def enrollment_update(request):
    """Update enrollment status"""
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        status = request.POST.get('status')
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            enrollment.status = status
            enrollment.save()
            messages.success(request, 'Kayıt durumu güncellendi.')
        except Enrollment.DoesNotExist:
            messages.error(request, 'Kayıt bulunamadı.')
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    return redirect('courses:enrollment_list')


@login_required
def enrollment_delete(request):
    """Delete enrollment"""
    if request.method == 'POST':
        enrollment_id = request.POST.get('enrollment_id')
        
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
            student_name = f'{enrollment.student.first_name} {enrollment.student.last_name}'
            enrollment.delete()
            messages.success(request, f'{student_name} ders kaydı silindi.')
        except Enrollment.DoesNotExist:
            messages.error(request, 'Kayıt bulunamadı.')
        except Exception as e:
            messages.error(request, f'Silme hatası: {str(e)}')
    
    return redirect('courses:enrollment_list')


# Assignment Views
class AssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = 'courses/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 20
    
    def get_queryset(self):
        state = (self.request.GET.get('state') or '').lower()
        now = timezone.now()
        qs_base = Assignment.objects.select_related('group__course', 'group__teacher').prefetch_related('submissions', 'group__enrollments')

        # Optional filter: specific course group (for teacher flow)
        group_id = self.request.GET.get('group')
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            student = Student.objects.get(user=self.request.user)
            # Öğrenci SADECE kayıtlı olduğu gruplardaki ödevleri görebilir
            qs_base = qs_base.filter(group__enrollments__student=student)
        elif hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            teacher = Teacher.objects.get(user=self.request.user)
            # Öğretmen SADECE kendi derslerindeki ödevleri görebilir
            qs_base = qs_base.filter(group__teacher=teacher)

        # Apply group filter only after teacher/student scoping
        if group_id:
            qs_base = qs_base.filter(group_id=group_id)

        if state == 'approaching':
            # teslim tarihi yakında olanlar: 7 gün içinde ve gelecekte
            qs = qs_base.filter(due_date__gte=now, due_date__lte=now + timezone.timedelta(days=7)).order_by('due_date')
        elif state == 'active':
            qs = qs_base.filter(due_date__gte=now).order_by('due_date')
        elif state == 'expired':
            qs = qs_base.filter(due_date__lt=now).order_by('-due_date')
        elif state == 'urgent':
            qs = qs_base.filter(due_date__gte=now, due_date__lte=now + timezone.timedelta(hours=24)).order_by('due_date')
        else:
            # varsayılan: aktifler due_date ASC, ardından expired due_date DESC
            from django.db.models import Case, When, IntegerField
            qs = qs_base.annotate(
                exp=Case(
                    When(due_date__lt=now, then=1),
                    default=0,
                    output_field=IntegerField()
                )
            ).order_by('exp', 'due_date').order_by('exp', 'due_date')
            # ikinci order_by yazımı bazı sürümlerde stabilite için bırakıldı
        return qs
    
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
            # Öğrenci SADECE kayıtlı olduğu gruplardaki duyuruları görebilir
            return Announcement.objects.filter(
                group__enrollments__student=student,
                status='active'
            ).select_related('group__course', 'teacher').order_by('-create_date')
        elif hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            teacher = Teacher.objects.get(user=self.request.user)
            # Öğretmen SADECE kendi derslerindeki duyuruları görebilir
            return Announcement.objects.filter(
                teacher=teacher,
                status='active'
            ).select_related('group__course', 'teacher').order_by('-create_date')
        else:
            # Admin tüm duyuruları görebilir
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

# Example Questions Views
class ExampleQuestionListView(LoginRequiredMixin, ListView):
    model = ExampleQuestion
    template_name = 'courses/question_list.html'
    context_object_name = 'questions'
    paginate_by = 20

    def get_queryset(self):
        qs = ExampleQuestion.objects.select_related('course', 'created_by')
        # Öğrenciler: kayıtlı oldukları derslerin public soruları
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
                course_ids = Enrollment.objects.filter(student=student, status='enrolled').values_list('group__course_id', flat=True)
                return qs.filter(course_id__in=course_ids, visibility='public')
            except Student.DoesNotExist:
                return qs.none()
        # Öğretmenler: kendi derslerindeki tüm sorular
        if hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher':
            teacher = Teacher.objects.get(user=self.request.user)
            course_ids = CourseGroup.objects.filter(teacher=teacher).values_list('course_id', flat=True)
            return qs.filter(course_id__in=course_ids)
        # Admin/staff: tümü
        return qs

class ExampleQuestionDetailView(LoginRequiredMixin, DetailView):
    model = ExampleQuestion
    template_name = 'courses/question_detail.html'
    context_object_name = 'question'

class ExampleQuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = ExampleQuestion
    form_class = ExampleQuestionForm
    template_name = 'courses/question_form.html'

    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        teacher = Teacher.objects.get(user=self.request.user)
        obj = form.save(commit=False)
        obj.created_by = teacher
        # Eğer ekli dosya varsa ve çoklu soru içeriyorsa, text/docx'ten ayrıştır ve toplu oluştur
        attachment = self.request.FILES.get('attachment')
        created_many = 0
        if attachment and not obj.content:
            from .services import parse_questions_from_text, parse_questions_from_docx
            filename = attachment.name.lower()
            if filename.endswith('.txt'):
                try:
                    text = attachment.read().decode('utf-8', errors='ignore')
                    items = parse_questions_from_text(text)
                except Exception:
                    items = []
            elif filename.endswith('.docx'):
                items = parse_questions_from_docx(attachment)
            else:
                items = []
            if items:
                bulk = []
                for it in items:
                    bulk.append(ExampleQuestion(
                        course=obj.course,
                        created_by=teacher,
                        title=it['title'],
                        content=it['content'],
                        question_type=it['type'],
                        visibility=obj.visibility
                    ))
                ExampleQuestion.objects.bulk_create(bulk)
                created_many = len(bulk)
        if created_many:
            messages.success(self.request, f'{created_many} soru dosyadan içe aktarıldı.')
        else:
            obj.save()
            messages.success(self.request, 'Örnek soru eklendi.')
        return redirect('courses:question_list')

class ExampleQuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ExampleQuestion
    form_class = ExampleQuestionForm
    template_name = 'courses/question_form.html'

    def test_func(self):
        obj = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                obj.created_by.user == self.request.user) or self.request.user.is_staff

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Örnek soru güncellendi.')
        return redirect('courses:question_list')

class ExampleQuestionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ExampleQuestion
    template_name = 'courses/question_delete.html'
    success_url = reverse_lazy('courses:question_list')

    def test_func(self):
        obj = self.get_object()
        return (hasattr(self.request.user, 'userprofile') and 
                self.request.user.userprofile.user_type == 'teacher' and
                obj.created_by.user == self.request.user) or self.request.user.is_staff

@login_required
@csrf_exempt
def ai_solve_question(request, pk):
    """Basit AI çözüm stub: ileride Gemini/OpenAI ile değiştirilecek."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)
    question = get_object_or_404(ExampleQuestion, pk=pk)
    try:
        from .services import solve_question_with_ai
        solution = solve_question_with_ai(question)
        return JsonResponse({'success': True, 'solution': solution})
    except Exception as e:
        logger.error(f"AI solve error: {e}")
        return JsonResponse({'success': False, 'error': 'Çözüm üretilemedi'}, status=500)

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
@csrf_exempt
def grade_submission_ajax(request):
    """AJAX endpoint for grading assignment submissions"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'})
    
    # Check if user is teacher
    if not (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'teacher'):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    try:
        submission_id = request.POST.get('submission_id')
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        if not submission_id or not score:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid score format'})
        
        # Get submission
        submission = get_object_or_404(Submission, id=submission_id)
        assignment = submission.assignment
        
        # Check if teacher owns this assignment
        teacher = Teacher.objects.get(user=request.user)
        if assignment.group.teacher != teacher:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Validate score
        if score_val < 0 or score_val > float(assignment.max_score):
            return JsonResponse({'success': False, 'error': f'Score must be between 0 and {assignment.max_score}'})
        
        # Update submission
        submission.score = score_val
        submission.feedback = feedback
        submission.status = 'graded'
        submission.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Grade updated successfully',
            'score': str(submission.score),
            'max_score': str(assignment.max_score)
        })
        
    except Submission.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Submission not found'})
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Teacher profile not found'})
    except Exception as e:
        logger.error(f"Grade submission error: {e}")
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
            request.user.userprofile and
            request.user.userprofile.user_type in ['admin', 'teacher']):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        return redirect('courses:detail', pk=course_pk)
    
    course = get_object_or_404(Course, pk=course_pk)
    
    try:
        student = Student.objects.get(id=student_id)
        
        # If user is teacher, only allow removing from their own groups
        if (hasattr(request.user, 'userprofile') and 
            request.user.userprofile and 
            request.user.userprofile.user_type == 'teacher'):
            try:
                teacher = Teacher.objects.get(user=request.user)
                enrollment = Enrollment.objects.filter(
                    student=student,
                    group__course=course,
                    group__teacher=teacher,
                    status='enrolled'
                ).first()
                
                if not enrollment:
                    messages.error(request, 'Bu öğrenci sizin dersinizde kayıtlı değil.')
                    return redirect('courses:detail', pk=course_pk)
            except Teacher.DoesNotExist:
                messages.error(request, 'Öğretmen profili bulunamadı.')
                return redirect('courses:detail', pk=course_pk)
        else:
            # Admin can remove from any group
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


# Teacher-Course Assignment Views (Simplified)
class TeacherCourseAssignmentView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Öğretmen-Ders Atama Paneli - Basitleştirilmiş"""
    template_name = 'courses/teacher_course_assignment.html'
    
    def test_func(self):
        return self.request.user.is_staff or (
            hasattr(self.request.user, 'userprofile') and 
            self.request.user.userprofile.user_type in ['admin', 'staff']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Tüm dersler
        courses = Course.objects.all().order_by('code')
        
        # Her ders için mevcut grupları ve öğretmenleri getir
        courses_with_groups = []
        for course in courses:
            groups = CourseGroup.objects.filter(course=course, status='active').select_related('teacher')
            courses_with_groups.append({
                'course': course,
                'groups': groups,
                'has_teacher': groups.filter(teacher__isnull=False).exists()
            })
        
        context['courses_with_groups'] = courses_with_groups
        context['teachers'] = Teacher.objects.filter(status='active').order_by('first_name', 'last_name')
        context['students'] = Student.objects.filter(status='active').order_by('first_name', 'last_name')
        
        # Mevcut atamalar (ders grupları)
        context['current_assignments'] = CourseGroup.objects.filter(
            status='active'
        ).select_related('course', 'teacher').prefetch_related('enrollments__student').order_by('course__code')
        
        return context


@login_required
def assign_teacher_to_course(request):
    """Derse öğretmen ata - Basit versiyon"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            teacher_id = data.get('teacher_id')
            semester = data.get('semester', '2024-2025 Güz')
            
            if not course_id or not teacher_id:
                return JsonResponse({'success': False, 'error': 'Ders ve öğretmen seçilmelidir'})
            
            course = Course.objects.get(id=course_id)
            teacher = Teacher.objects.get(id=teacher_id)
            
            # Mevcut grup var mı kontrol et
            existing_group = CourseGroup.objects.filter(course=course, teacher=teacher, status='active').first()
            if existing_group:
                return JsonResponse({'success': False, 'error': 'Bu öğretmen zaten bu derse atanmış'})
            
            # Yeni grup oluştur
            group = CourseGroup.objects.create(
                course=course,
                teacher=teacher,
                name=f"{course.code}-{teacher.first_name[:1]}{teacher.last_name[:1]}",
                semester=semester,
                status='active'
            )
            
            return JsonResponse({
                'success': True, 
                'message': f'{teacher.full_name} öğretmeni {course.code} dersine atandı',
                'group_id': group.id
            })
            
        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ders bulunamadı'})
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Öğretmen bulunamadı'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'})


@login_required
def remove_teacher_from_course(request):
    """Dersten öğretmen çıkar"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            
            if not group_id:
                return JsonResponse({'success': False, 'error': 'Grup ID gerekli'})
            
            group = CourseGroup.objects.get(id=group_id)
            course_code = group.course.code
            teacher_name = group.teacher.full_name if group.teacher else 'Bilinmeyen'
            
            # Grubu pasif yap (silmek yerine)
            group.status = 'inactive'
            group.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{teacher_name} öğretmeni {course_code} dersinden çıkarıldı'
            })
            
        except CourseGroup.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ders grubu bulunamadı'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'})


@login_required
def update_course_group(request):
    """Ders grubunu güncelle"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            
            if not group_id:
                return JsonResponse({'success': False, 'error': 'Grup ID gerekli'})
            
            group = CourseGroup.objects.get(id=group_id)
            
            # Güncellenebilir alanlar
            if 'semester' in data:
                group.semester = data['semester']
            if 'classroom' in data:
                group.classroom = data['classroom']
            if 'schedule' in data:
                group.schedule = data['schedule']
            if 'teacher_id' in data:
                teacher = Teacher.objects.get(id=data['teacher_id'])
                group.teacher = teacher
            
            group.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'{group.course.code} ders grubu güncellendi'
            })
            
        except CourseGroup.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Ders grubu bulunamadı'})
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Öğretmen bulunamadı'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'})


@login_required
def bulk_assign_view(request):
    """Toplu ders atama"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_ids = data.get('course_ids', [])
            teacher_ids = data.get('teacher_ids', [])
            semester = data.get('semester', '')
            classroom = data.get('classroom', '')
            schedule = data.get('schedule', '')
            
            if not course_ids or not teacher_ids:
                return JsonResponse({'success': False, 'error': 'Ders ve öğretmen seçilmelidir'})
            
            controller = TeacherCourseAssignmentController()
            service = controller.assignment_service
            
            results = service.bulk_assign(
                course_ids, teacher_ids, semester, classroom, schedule, request.user
            )
            
            success_count = sum(1 for r in results if r.get('success'))
            
            return JsonResponse({
                'success': True,
                'message': f'{success_count} atama başarıyla yapıldı',
                'results': [
                    {
                        'course': r['course_group'].course.code,
                        'teacher': r['course_group'].teacher.full_name,
                        'compatibility': r.get('compatibility', {}).get('score', 0),
                        'conflicts': len(r.get('conflicts', []))
                    }
                    for r in results if r.get('success')
                ]
            })
        except Exception as e:
            logger.error(f"Toplu atama hatası: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'}, status=400)


@login_required
def bulk_remove_view(request):
    """Toplu ders çıkarma"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_group_ids = data.get('course_group_ids', [])
            
            if not course_group_ids:
                return JsonResponse({'success': False, 'error': 'Atama seçilmelidir'})
            
            controller = TeacherCourseAssignmentController()
            service = controller.assignment_service
            
            results = service.bulk_remove(course_group_ids, request.user)
            success_count = sum(1 for r in results if r.get('success'))
            
            return JsonResponse({
                'success': True,
                'message': f'{success_count} atama başarıyla kaldırıldı'
            })
        except Exception as e:
            logger.error(f"Toplu çıkarma hatası: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'}, status=400)


@login_required
def check_compatibility_view(request):
    """Uyumluluk kontrolü"""
    if request.method == 'GET':
        teacher_id = request.GET.get('teacher_id')
        course_id = request.GET.get('course_id')
        
        if not teacher_id or not course_id:
            return JsonResponse({'success': False, 'error': 'Öğretmen ve ders seçilmelidir'})
        
        controller = TeacherCourseAssignmentController()
        compatibility = controller.check_compatibility(request, teacher_id, course_id)
        
        return JsonResponse({
            'success': True,
            'compatibility': compatibility
        })
    
    return JsonResponse({'success': False, 'error': 'GET isteği gerekli'}, status=400)


@login_required
def check_conflicts_view(request):
    """Çakışma kontrolü"""
    if request.method == 'GET':
        teacher_id = request.GET.get('teacher_id')
        course_id = request.GET.get('course_id')
        semester = request.GET.get('semester', '')
        schedule = request.GET.get('schedule', '')
        
        if not teacher_id or not course_id:
            return JsonResponse({'success': False, 'error': 'Öğretmen ve ders seçilmelidir'})
        
        controller = TeacherCourseAssignmentController()
        conflicts = controller.check_conflicts(request, teacher_id, course_id, semester, schedule)
        
        return JsonResponse({
            'success': True,
            'conflicts': [
                {
                    'group': c['group'].course.code,
                    'conflict_type': c['conflict_type'],
                    'message': c['message']
                }
                for c in conflicts
            ],
            'has_conflicts': len(conflicts) > 0
        })
    
    return JsonResponse({'success': False, 'error': 'GET isteği gerekli'}, status=400)


@login_required
def teacher_availability_view(request, teacher_id):
    """Öğretmen uygunluk durumu"""
    controller = TeacherCourseAssignmentController()
    availability = controller.get_teacher_availability(request, teacher_id)
    
    return JsonResponse({
        'success': True,
        'availability': availability
    })


@login_required
@csrf_exempt
def bulk_enroll_students_view(request):
    """Toplu öğrenci ekleme/yönetimi"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    # GET isteği - mevcut kayıtlı öğrencileri döndür
    if request.method == 'GET':
        group_id = request.GET.get('group_id')
        if not group_id:
            return JsonResponse({'success': False, 'error': 'Grup ID gerekli'})
        
        try:
            group = CourseGroup.objects.get(pk=group_id)
            enrollments = Enrollment.objects.filter(
                group=group, status='enrolled'
            ).select_related('student')
            
            enrolled_students = []
            enrolled_student_details = []
            
            for enrollment in enrollments:
                enrolled_students.append(enrollment.student_id)
                enrolled_student_details.append({
                    'id': enrollment.student.id,
                    'name': enrollment.student.full_name,
                    'school_number': enrollment.student.school_number
                })
            
            return JsonResponse({
                'success': True, 
                'enrolled_students': enrolled_students,
                'enrolled_student_details': enrolled_student_details
            })
        except CourseGroup.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Grup bulunamadı'})
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            student_ids = data.get('student_ids', [])
            
            if not group_id:
                return JsonResponse({'success': False, 'error': 'Grup seçilmelidir'})
            
            # Grup kontrolü
            group = get_object_or_404(CourseGroup, pk=group_id)
            
            # Mevcut kayıtları al
            current_enrollments = set(Enrollment.objects.filter(
                group=group, status='enrolled'
            ).values_list('student_id', flat=True))
            
            new_student_ids = set(student_ids)
            
            # Çıkarılacak öğrenciler (mevcut ama yeni listede yok)
            to_remove = current_enrollments - new_student_ids
            # Eklenecek öğrenciler (yeni listede var ama mevcut değil)
            to_add = new_student_ids - current_enrollments
            
            # Öğrencileri çıkar
            removed_count = 0
            for student_id in to_remove:
                Enrollment.objects.filter(group=group, student_id=student_id).delete()
                removed_count += 1
            
            # Öğrencileri ekle
            added_count = 0
            for student_id in to_add:
                try:
                    student = Student.objects.get(pk=student_id)
                    Enrollment.objects.create(
                        student=student,
                        group=group,
                        status='enrolled'
                    )
                    added_count += 1
                except Student.DoesNotExist:
                    pass
            
            return JsonResponse({
                'success': True,
                'message': f'{added_count} öğrenci eklendi, {removed_count} öğrenci çıkarıldı',
                'added': added_count,
                'removed': removed_count
            })
            
        except Exception as e:
            logger.error(f"Toplu öğrenci ekleme hatası: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'}, status=400)


@login_required
@csrf_exempt
def bulk_unenroll_students_view(request):
    """Toplu öğrenci çıkarma"""
    if not (request.user.is_staff or 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.user_type in ['admin', 'teacher', 'staff']):
        return JsonResponse({'success': False, 'error': 'Yetkiniz yok'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            enrollment_ids = data.get('enrollment_ids', [])
            
            logger.info(f"bulk_unenroll_students_view called with data: {data}")
            logger.info(f"enrollment_ids: {enrollment_ids}")
            
            if not enrollment_ids or len(enrollment_ids) == 0:
                logger.warning("No enrollment_ids provided")
                return JsonResponse({'success': False, 'error': 'En az bir öğrenci seçilmelidir'})
            
            # Enrollment'ları bul ve sil
            removed_count = 0
            errors = []
            
            for enrollment_id in enrollment_ids:
                try:
                    enrollment = Enrollment.objects.get(pk=enrollment_id)
                    
                    # Yetki kontrolü - öğretmen ise sadece kendi gruplarından çıkarabilir
                    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'teacher':
                        try:
                            teacher = Teacher.objects.get(user=request.user)
                            if enrollment.group.teacher != teacher:
                                errors.append(f'Enrollment {enrollment_id}: Bu gruptan öğrenci çıkarma yetkiniz yok')
                                continue
                        except Teacher.DoesNotExist:
                            errors.append(f'Enrollment {enrollment_id}: Öğretmen bilgisi bulunamadı')
                            continue
                    
                    enrollment.delete()
                    removed_count += 1
                    
                except Enrollment.DoesNotExist:
                    errors.append(f'Enrollment {enrollment_id}: Kayıt bulunamadı')
                except Exception as e:
                    errors.append(f'Enrollment {enrollment_id}: {str(e)}')
            
            response_data = {
                'success': True,
                'count': removed_count,
                'removed': removed_count
            }
            
            if errors:
                response_data['errors'] = errors
            
            if removed_count == 0:
                response_data['success'] = False
                response_data['error'] = 'Hiçbir öğrenci çıkarılamadı'
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Toplu öğrenci çıkarma hatası: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'POST isteği gerekli'}, status=400)


# ---- Feedback & Plagiarism endpoints ----
@login_required
@csrf_exempt
def generate_feedback_view(request, pk):
    """Öğretmenin bir teslim için hızlı geri bildirim metni üretmesi."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)
    if not (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'teacher'):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    try:
        submission = get_object_or_404(Submission, pk=pk)
        from .services import generate_feedback
        feedback_text = generate_feedback(submission.student, submission.assignment)
        submission.feedback = feedback_text
        submission.save(update_fields=['feedback'])
        return JsonResponse({'success': True, 'feedback': feedback_text})
    except Exception as e:
        logger.error(f"feedback error: {e}")
        return JsonResponse({'success': False, 'error': 'Geri bildirim oluşturulamadı'}, status=500)


@login_required
@csrf_exempt
def plagiarism_check_view(request, pk):
    """Teslim metnini diğer teslimlere karşı basit benzerlik ile kontrol eder."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)
    if not (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type in ['teacher', 'admin']):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    try:
        submission = get_object_or_404(Submission, pk=pk)
        from .services import extract_text_from_upload
        text = extract_text_from_upload(submission.file_url)
        others = submission.assignment.submissions.exclude(pk=submission.pk)
        corpus = []
        for s in others:
            try:
                if s.file_url:
                    corpus.append(extract_text_from_upload(s.file_url))
            except Exception:
                continue
        from .services import check_plagiarism
        result = check_plagiarism(text, corpus)
        try:
            from .models import PlagiarismReport
            report = PlagiarismReport.objects.create(
                submission=submission,
                method='ngram_jaccard',
                max_similarity=result.get('max_similarity') or 0.0,
                details=result
            )
            result['report_id'] = report.id
        except Exception:
            pass
        return JsonResponse({'success': True, 'result': result})
    except Exception as e:
        logger.error(f"plagiarism error: {e}")
        return JsonResponse({'success': False, 'error': 'İntihal kontrolü yapılamadı'}, status=500)