from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Note
from .forms import NoteForm, NoteFilterForm
from courses.models import Course
from django.contrib.auth.models import User

@login_required
def note_list(request):
    # Öğrenciler sadece kendi notlarını görebilir
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
        # Sınav türü sıralaması: vize, final, but
        notes = Note.objects.filter(student=request.user).extra(
            select={'exam_order': "CASE WHEN exam_type='vize' THEN 1 WHEN exam_type='final' THEN 2 WHEN exam_type='but' THEN 3 ELSE 4 END"}
        ).order_by('course__name', 'exam_order')
        filter_form = None
    else:
        # Öğretmenler ve adminler tüm notları görebilir
        notes = Note.objects.all().extra(
            select={'exam_order': "CASE WHEN exam_type='vize' THEN 1 WHEN exam_type='final' THEN 2 WHEN exam_type='but' THEN 3 ELSE 4 END"}
        ).order_by('student__first_name', 'course__name', 'exam_order')
        
        # Filtreleme formu - sadece öğretmen/admin için
        filter_form = NoteFilterForm(request.GET, user=request.user)
        
        # Filtreleri uygula
        course_filter = request.GET.get('course')
        exam_type_filter = request.GET.get('exam_type')
        grade_filter = request.GET.get('grade')
        
        if course_filter:
            notes = notes.filter(course_id=course_filter)
        if exam_type_filter:
            notes = notes.filter(exam_type=exam_type_filter)
        if grade_filter:
            notes = notes.filter(grade=grade_filter)
    
    # Arama - hem öğrenci hem öğretmen için
    search_query = request.GET.get('search')
    if search_query:
        notes = notes.filter(
            Q(course__name__icontains=search_query) |
            Q(course__code__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )
    
    # Öğretmen görünümü için eksik notları hesapla
    structured_data = None
    if not (hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student'):
        from collections import defaultdict
        from courses.models import Course
        
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
    
    context = {
        'notes': notes,
        'structured_data': structured_data,
        'filter_form': filter_form,
        'search_query': search_query,
        'is_student': hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student',
    }
    return render(request, 'notes/list.html', context)

@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk)
    
    # Öğrenciler sadece kendi notlarını görebilir
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
        if note.student != request.user:
            messages.error(request, 'Bu nota erişim yetkiniz yok.')
            return redirect('notes:list')
    
    context = {
        'note': note,
        'is_student': hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student',
    }
    return render(request, 'notes/detail.html', context)

@login_required
def note_create(request):
    # Öğrenciler not oluşturamaz
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
        messages.error(request, 'Not oluşturma yetkiniz yok.')
        return redirect('notes:list')
    
    if request.method == 'POST':
        form = NoteForm(request.POST, user=request.user)
        if form.is_valid():
            note = form.save(commit=False)
            note.teacher = request.user
            note.save()
            messages.success(request, 'Not başarıyla oluşturuldu!')
            return redirect('notes:list')
    else:
        # URL parametrelerinden ön değerleri al
        initial_data = {}
        if request.GET.get('course'):
            initial_data['course'] = request.GET.get('course')
        if request.GET.get('student'):
            initial_data['student'] = request.GET.get('student')
        if request.GET.get('exam_type'):
            initial_data['exam_type'] = request.GET.get('exam_type')
            
        form = NoteForm(user=request.user, initial=initial_data)
    
    return render(request, 'notes/form.html', {'form': form, 'title': 'Yeni Not Oluştur'})

@login_required
def note_edit(request, pk):
    # Öğrenciler not düzenleyemez
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
        messages.error(request, 'Not düzenleme yetkiniz yok.')
        return redirect('notes:list')
    
    note = get_object_or_404(Note, pk=pk)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Not başarıyla güncellendi!')
            return redirect('notes:detail', pk=note.pk)
    else:
        form = NoteForm(instance=note, user=request.user)
    
    return render(request, 'notes/form.html', {'form': form, 'title': 'Not Düzenle', 'note': note})

@login_required
def note_delete(request, pk):
    # Öğrenciler not silemez
    if hasattr(request.user, 'userprofile') and request.user.userprofile.user_type == 'student':
        messages.error(request, 'Not silme yetkiniz yok.')
        return redirect('notes:list')
    
    note = get_object_or_404(Note, pk=pk)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Not başarıyla silindi!')
        return redirect('notes:list')
    
    return render(request, 'notes/delete.html', {'note': note})

@login_required
def get_students_by_course(request):
    """AJAX view to get students enrolled in a specific course"""
    course_id = request.GET.get('course_id')
    
    if course_id:
        try:
            course = Course.objects.get(id=course_id)
            # Bu derse kayıtlı öğrencileri getir
            from students.models import Student
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
            
            return JsonResponse({'students': students_list})
        except Course.DoesNotExist:
            pass
    
    return JsonResponse({'students': []})
