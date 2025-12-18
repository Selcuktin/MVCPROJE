"""
Gradebook Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import GradeCategory, GradeItem, Grade
from .services import GradebookService
from apps.courses.models import CourseGroup, Enrollment
from apps.students.models import Student
from apps.teachers.models import Teacher
from decimal import Decimal


@login_required
def gradebook_view(request, group_id):
    """Teacher view for course gradebook"""
    course_group = get_object_or_404(CourseGroup, id=group_id)
    
    # Check if user is teacher of this course
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'teacher':
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok')
        return redirect('users:dashboard')

    # Must be the assigned teacher
    if not getattr(course_group, 'teacher_id', None) or course_group.teacher.user_id != request.user.id:
        messages.error(request, 'Bu dersin notlandırma sayfasına erişim yetkiniz yok')
        return redirect('teachers:dashboard')
    
    service = GradebookService()

    # Auto-create standard categories/items so admin panel is not required
    vize_cat, _ = GradeCategory.objects.get_or_create(
        course_group=course_group,
        name='Vize',
        defaults={'category_type': 'exam', 'weight': Decimal('40'), 'description': 'Vize (%40)', 'is_active': True},
    )
    final_cat, _ = GradeCategory.objects.get_or_create(
        course_group=course_group,
        name='Final',
        defaults={'category_type': 'exam', 'weight': Decimal('60'), 'description': 'Final (%60)', 'is_active': True},
    )
    # Bütünleme, Finalin yerine geçtiği için ağırlığı toplamda ekstra yük getirmemeli.
    # Bu yüzden burada ağırlığı 0 olarak tanımlıyoruz; hesaplama servisi zaten finali
    # bütünleme ile değiştirerek yüzdelendirmeyi yapıyor.
    but_cat, _ = GradeCategory.objects.get_or_create(
        course_group=course_group,
        name='Bütünleme',
        defaults={
            'category_type': 'exam',
            'weight': Decimal('0'),
            'description': 'Bütünleme (Final yerine geçer)',
            'is_active': True,
        },
    )

    vize_item, _ = GradeItem.objects.get_or_create(
        category=vize_cat,
        name='Vize Sınavı',
        defaults={'max_score': Decimal('100'), 'weight_in_category': Decimal('100'), 'status': 'published'},
    )
    final_item, _ = GradeItem.objects.get_or_create(
        category=final_cat,
        name='Final Sınavı',
        defaults={'max_score': Decimal('100'), 'weight_in_category': Decimal('100'), 'status': 'published'},
    )
    but_item, _ = GradeItem.objects.get_or_create(
        category=but_cat,
        name='Bütünleme Sınavı',
        defaults={'max_score': Decimal('100'), 'weight_in_category': Decimal('100'), 'status': 'published'},
    )
    
    # Get categories and items
    categories = GradeCategory.objects.filter(
        course_group=course_group,
        is_active=True
    ).prefetch_related('items')
    
    # Get enrollments
    enrollments = Enrollment.objects.filter(
        group=course_group,
        status='enrolled'
    ).select_related('student').order_by('student__first_name', 'student__last_name')

    enrollment_ids = list(enrollments.values_list('id', flat=True))
    student_ids = list(enrollments.values_list('student_id', flat=True))

    # Existing scores for fast rendering
    existing_grades = Grade.objects.filter(
        student_id__in=student_ids,
        item_id__in=[vize_item.id, final_item.id, but_item.id],
    ).values('student_id', 'item_id', 'score')
    existing_map = {(g['student_id'], g['item_id']): g['score'] for g in existing_grades}
    
    # Build gradebook data
    gradebook_data = []
    for enrollment in enrollments:
        result = service.calculate_student_course_grade(
            enrollment.student,
            course_group
        )
        
        gradebook_data.append({
            'enrollment': enrollment,
            'student': enrollment.student,
            'total_score': result['total'],
            'letter_grade': result['letter_grade'],
            'breakdown': result['breakdown'],
            'vize_score': existing_map.get((enrollment.student_id, vize_item.id)),
            'final_score': existing_map.get((enrollment.student_id, final_item.id)),
            'but_score': existing_map.get((enrollment.student_id, but_item.id)),
        })
    
    # Statistics
    stats = service.get_course_grade_statistics(course_group)
    
    context = {
        'course_group': course_group,
        'categories': categories,
        'gradebook_data': gradebook_data,
        'stats': stats,
        'vize_item_id': vize_item.id,
        'final_item_id': final_item.id,
        'but_item_id': but_item.id,
    }
    
    return render(request, 'gradebook/gradebook.html', context)


@login_required
def teacher_default_gradebook(request):
    """
    Teacher: shortcut from sidebar to a gradebook page.
    Shows course selection if teacher has multiple courses, otherwise redirects to the only course.
    """
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('users:dashboard')

    course_groups = CourseGroup.objects.filter(
        teacher=teacher,
        status='active'
    ).select_related('course').order_by('course__code')

    if not course_groups.exists():
        messages.error(request, 'Aktif ders bulunamadı, önce bir ders oluşturun veya atanmasını isteyin.')
        return redirect('teachers:dashboard')
    
    # If only one course, redirect directly
    if course_groups.count() == 1:
        return redirect('gradebook:course_gradebook', group_id=course_groups.first().id)
    
    # Multiple courses - show selection page
    return render(request, 'gradebook/select_course.html', {
        'course_groups': course_groups,
        'teacher': teacher
    })

@login_required
@require_POST
def quick_grade_entry_view(request, group_id):
    """Teacher: quick grade entry for Vize/Final/Bütünleme with live recalculation"""
    try:
        course_group = get_object_or_404(CourseGroup, id=group_id)

        if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'teacher':
            return JsonResponse({'success': False, 'message': 'Yetki yok'}, status=403)

        if not getattr(course_group, 'teacher_id', None) or course_group.teacher.user_id != request.user.id:
            return JsonResponse({'success': False, 'message': 'Yetki yok'}, status=403)

        student_id = request.POST.get('student_id')
        kind = (request.POST.get('kind') or '').strip().lower()
        score_raw = (request.POST.get('score') or '').strip()

        if kind not in {'vize', 'final', 'but'}:
            return JsonResponse({'success': False, 'message': 'Geçersiz not türü'}, status=400)

        student = get_object_or_404(Student, id=student_id)
        enrollment = Enrollment.objects.filter(group=course_group, student=student, status='enrolled').first()
        if not enrollment:
            return JsonResponse({'success': False, 'message': 'Öğrenci bu grupta kayıtlı değil'}, status=400)

        # Find item id from POST (template already has these), fallback to name-based search
        item_id = request.POST.get('item_id')
        if not item_id:
            name_map = {'vize': 'Vize Sınavı', 'final': 'Final Sınavı', 'but': 'Bütünleme Sınavı'}
            item = GradeItem.objects.filter(category__course_group=course_group, name=name_map[kind]).first()
        else:
            try:
                item = GradeItem.objects.get(id=item_id)
            except GradeItem.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Not kategorisi bulunamadı'}, status=400)
        
        if not item:
            return JsonResponse({'success': False, 'message': 'Not kategorisi bulunamadı'}, status=400)

        score_val = None
        if score_raw != '':
            try:
                score_val = Decimal(str(score_raw))
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'message': 'Puan sayısal olmalı'}, status=400)

            if score_val < 0 or score_val > item.max_score:
                return JsonResponse({'success': False, 'message': f'Puan 0-{item.max_score} aralığında olmalı'}, status=400)

        Grade.objects.update_or_create(
            student=student,
            item=item,
            defaults={'score': score_val, 'enrollment': enrollment},
        )

        service = GradebookService()
        result = service.calculate_student_course_grade(student, course_group)
        if result.get('letter_grade'):
            service.update_enrollment_grades(enrollment)

        return JsonResponse({
            'success': True,
            'total': result.get('total'),
            'letter_grade': result.get('letter_grade'),
        })
    
    except Exception as e:
        import traceback
        import sys
        error_details = traceback.format_exc()
        print("="*80)
        print(f"ERROR in quick_grade_entry_view:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Full traceback:")
        print(error_details)
        print("="*80)
        sys.stdout.flush()
        return JsonResponse({
            'success': False,
            'message': f'Sunucu hatası: {str(e)}',
            'traceback': error_details if True else None  # Debug mode
        }, status=500)


@login_required
def student_grades_view(request):
    """Student view of their own grades"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci profili bulunamadı')
        return redirect('users:dashboard')
    
    service = GradebookService()
    
    # Get current enrollments
    enrollments = Enrollment.objects.filter(
        student=student,
        status='enrolled'
    ).select_related('group__course', 'group__academic_term').order_by('-group__academic_term__start_date')
    
    course_grades = []
    for enrollment in enrollments:
        result = service.calculate_student_course_grade(
            student,
            enrollment.group
        )
        
        course_grades.append({
            'enrollment': enrollment,
            'result': result
        })
    
    context = {
        'student': student,
        'course_grades': course_grades
    }
    
    return render(request, 'gradebook/student_grades.html', context)


@login_required
def student_transcript_view(request):
    """Student transcript"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Öğrenci profili bulunamadı')
        return redirect('users:dashboard')
    
    service = GradebookService()
    transcript_data = service.get_student_transcript(student)
    
    context = {
        'student': student,
        'transcript': transcript_data['transcript'],
        'total_credits': transcript_data['total_credits'],
        'gpa': transcript_data['gpa'],
        'total_courses': transcript_data['total_courses']
    }
    
    return render(request, 'gradebook/transcript.html', context)


@login_required
@require_POST
def grade_entry_view(request, item_id):
    """AJAX grade entry"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'teacher':
        return JsonResponse({'success': False, 'message': 'Yetki yok'}, status=403)
    
    item = get_object_or_404(GradeItem, id=item_id)
    student_id = request.POST.get('student_id')
    score = request.POST.get('score')
    feedback = request.POST.get('feedback', '')
    
    try:
        student = Student.objects.get(id=student_id)
        
        grade, created = Grade.objects.update_or_create(
            student=student,
            item=item,
            defaults={
                'score': float(score) if score else None,
                'feedback': feedback
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Not kaydedildi',
            'percentage': grade.percentage
        })
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Öğrenci bulunamadı'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def update_enrollment_grade_view(request, enrollment_id):
    """Update enrollment final grade based on gradebook"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.user_type != 'teacher':
        return JsonResponse({'success': False, 'message': 'Yetki yok'}, status=403)
    
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    
    service = GradebookService()
    result = service.update_enrollment_grades(enrollment)
    
    return JsonResponse({
        'success': True,
        'message': 'Not güncellendi',
        'letter_grade': result['letter_grade'],
        'total': result['total']
    })
