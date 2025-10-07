from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Count
from .models import Teacher
from courses.models import CourseGroup, Assignment, Announcement
from .forms import TeacherForm

class TeacherListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Teacher
    template_name = 'teachers/list.html'
    context_object_name = 'teachers'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['teacher', 'admin']
    
    def get_queryset(self):
        queryset = Teacher.objects.all()
        search = self.request.GET.get('search')
        department = self.request.GET.get('department')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(tc_no__icontains=search) |
                Q(email__icontains=search) |
                Q(department__icontains=search)
            )
        
        if department:
            queryset = queryset.filter(department__icontains=department)
            
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('department', 'first_name', 'last_name')

class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = Teacher
    template_name = 'teachers/detail.html'
    context_object_name = 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        context['course_groups'] = teacher.course_groups.select_related('course')
        context['assignments'] = Assignment.objects.filter(group__teacher=teacher).count()
        context['announcements'] = teacher.announcements.count()
        return context

class TeacherCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/form.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin']
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğretmen başarıyla oluşturuldu.')
        return super().form_valid(form)

class TeacherUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Teacher
    form_class = TeacherForm
    template_name = 'teachers/form.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin']
    
    def form_valid(self, form):
        messages.success(self.request, 'Öğretmen bilgileri başarıyla güncellendi.')
        return super().form_valid(form)

class TeacherDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Teacher
    template_name = 'teachers/delete.html'
    success_url = reverse_lazy('teachers:list')
    
    def test_func(self):
        return self.request.user.is_staff or hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type in ['admin']
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Öğretmen başarıyla silindi.')
        return super().delete(request, *args, **kwargs)

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def handle_no_permission(self):
        messages.error(self.request, 'Öğretmen paneline sadece öğretmenler erişebilir.')
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['teacher'] = teacher
            context['course_groups'] = teacher.course_groups.select_related('course')
            context['total_students'] = sum([group.enrollments.count() for group in teacher.course_groups.all()])
            context['recent_assignments'] = Assignment.objects.filter(
                group__teacher=teacher
            ).order_by('-create_date')[:5]
            context['recent_announcements'] = Announcement.objects.filter(
                teacher=teacher
            ).select_related('group__course').order_by('-create_date')[:5]
            context['pending_submissions'] = Assignment.objects.filter(
                group__teacher=teacher,
                status='active'
            ).annotate(
                submission_count=Count('submissions')
            )
        except Teacher.DoesNotExist:
            context['teacher'] = None
        return context

class TeacherCoursesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/courses.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            context['course_groups'] = teacher.course_groups.select_related('course').prefetch_related('enrollments__student')
        except Teacher.DoesNotExist:
            context['course_groups'] = []
        return context

class TeacherAssignmentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/assignments.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            
            # Öğretmenin tüm ödevleri
            assignments = Assignment.objects.filter(
                group__teacher=teacher
            ).select_related('group__course').annotate(
                submission_count=Count('submissions')
            ).order_by('-create_date')
            
            # Filtreleme
            course_filter = self.request.GET.get('course')
            status_filter = self.request.GET.get('status')
            search_filter = self.request.GET.get('search')
            
            if course_filter:
                assignments = assignments.filter(group_id=course_filter)
            
            if status_filter:
                assignments = assignments.filter(status=status_filter)
                
            if search_filter:
                assignments = assignments.filter(title__icontains=search_filter)
            
            context['assignments'] = assignments
            context['course_groups'] = teacher.course_groups.select_related('course')
            
            # İstatistikler
            all_assignments = Assignment.objects.filter(group__teacher=teacher)
            context['active_assignments'] = all_assignments.filter(status='active').count()
            context['completed_assignments'] = all_assignments.filter(status='inactive').count()
            context['expired_assignments'] = all_assignments.filter(status='expired').count()
            
        except Teacher.DoesNotExist:
            context['assignments'] = []
            context['course_groups'] = []
            context['active_assignments'] = 0
            context['completed_assignments'] = 0
            context['expired_assignments'] = 0
            
        return context

class TeacherStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teachers/students.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'userprofile') and self.request.user.userprofile.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            teacher = Teacher.objects.get(user=self.request.user)
            
            # Get all students enrolled in teacher's courses
            from courses.models import Enrollment
            from students.models import Student
            from collections import defaultdict
            
            # Öğretmenin ders grupları
            course_groups = teacher.course_groups.all()
            context['my_course_groups'] = course_groups
            context['my_courses'] = course_groups.count()
            
            # Öğretmenin derslerine kayıtlı öğrenciler
            enrollments = Enrollment.objects.filter(
                group__teacher=teacher,
                status='enrolled'
            ).select_related('student', 'group__course').order_by('student__first_name')
            
            # Öğrenci bazında verileri grupla
            student_data = defaultdict(lambda: {
                'student': None,
                'enrollments': [],
                'completed_assignments': 0,
                'pending_assignments': 0,
                'average_grade': None
            })
            
            for enrollment in enrollments:
                student = enrollment.student
                student_data[student.id]['student'] = student
                student_data[student.id]['enrollments'].append(enrollment)
            
            # Filtreleme
            search = self.request.GET.get('search')
            course_filter = self.request.GET.get('course')
            status_filter = self.request.GET.get('status')
            
            filtered_students = []
            for student_id, data in student_data.items():
                student = data['student']
                
                # Arama filtresi
                if search:
                    if not (search.lower() in student.first_name.lower() or 
                           search.lower() in student.last_name.lower() or
                           search in student.school_number):
                        continue
                
                # Ders filtresi
                if course_filter:
                    if not any(e.group.id == int(course_filter) for e in data['enrollments']):
                        continue
                
                # Durum filtresi
                if status_filter:
                    if student.status != status_filter:
                        continue
                
                filtered_students.append(data)
            
            context['students'] = filtered_students
            context['total_students'] = len(filtered_students)
            
            # İstatistikler
            from courses.models import Assignment
            context['active_assignments'] = Assignment.objects.filter(
                group__teacher=teacher,
                status='active'
            ).count()
            
            # Sınıf ortalaması hesapla (basit)
            from notes.models import Note
            notes = Note.objects.filter(
                course__groups__teacher=teacher
            )
            if notes.exists():
                total_score = sum(note.score for note in notes)
                context['class_average'] = total_score / notes.count()
            else:
                context['class_average'] = 0
                
        except Teacher.DoesNotExist:
            context['students'] = []
            context['total_students'] = 0
            context['my_courses'] = 0
            context['active_assignments'] = 0
            context['class_average'] = 0
            context['my_course_groups'] = []
            
        return context