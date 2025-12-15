"""
Quiz Views - Teacher and Student Interfaces
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Avg

from .models import QuestionBank, Question, Quiz, QuizQuestion, QuizAttempt, QuizAnswer
from apps.courses.models import CourseGroup, Enrollment
from apps.teachers.models import Teacher


@login_required
def question_bank_list(request):
    """Teacher: List all question banks"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('users:dashboard')
    
    banks = QuestionBank.objects.filter(
        Q(created_by=request.user) | Q(is_shared=True)
    ).prefetch_related('questions')
    
    context = {
        'banks': banks,
        'teacher': teacher
    }
    return render(request, 'quiz/question_bank_list.html', context)


@login_required
@require_POST
def question_bank_create(request):
    """Teacher: Create a new question bank"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Öğretmen profili bulunamadı'})
    
    name = request.POST.get('name')
    description = request.POST.get('description', '')
    is_shared = request.POST.get('is_shared') == 'true'
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Banka adı gerekli'})
    
    bank = QuestionBank.objects.create(
        name=name,
        description=description,
        created_by=request.user,
        is_shared=is_shared
    )
    
    messages.success(request, f'{name} soru bankası başarıyla oluşturuldu!')
    return JsonResponse({'success': True, 'bank_id': bank.id})


@login_required
def question_bank_detail(request, bank_id):
    """Teacher: View/manage questions in a bank"""
    bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permission
    if bank.created_by != request.user and not bank.is_shared:
        messages.error(request, 'Bu soru bankasına erişim yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    questions = bank.questions.all().order_by('-created_at')
    
    context = {
        'bank': bank,
        'questions': questions
    }
    return render(request, 'quiz/question_bank_detail.html', context)


@login_required
@require_POST
def question_bank_delete(request, bank_id):
    """Teacher: Delete a question bank"""
    bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permission - only creator can delete
    if bank.created_by != request.user:
        messages.error(request, 'Bu soru bankasını silme yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    bank_name = bank.name
    bank.delete()
    messages.success(request, f'{bank_name} soru bankası başarıyla silindi')
    return redirect('quiz:question_bank_list')


@login_required
def question_create(request, bank_id):
    """Teacher: Create a question in a bank"""
    bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permission
    if bank.created_by != request.user and not bank.is_shared:
        messages.error(request, 'Bu soru bankasına soru ekleme yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type')
        points = request.POST.get('points', 1)
        
        if not question_text or not question_type:
            messages.error(request, 'Soru metni ve tipi gerekli')
            return redirect('quiz:question_bank_detail', bank_id=bank_id)
        
        question = Question.objects.create(
            bank=bank,
            question_text=question_text,
            question_type=question_type,
            points=points,
            created_by=request.user
        )
        
        # Handle answer choices for multiple_choice and true_false
        if question_type in ['multiple_choice', 'true_false']:
            choices_count = int(request.POST.get('choices_count', 0))
            for i in range(choices_count):
                choice_text = request.POST.get(f'choice_{i}')
                is_correct = request.POST.get(f'is_correct_{i}') == 'on'
                
                if choice_text:
                    from apps.quiz.models import AnswerChoice
                    AnswerChoice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=is_correct
                    )
        
        messages.success(request, 'Soru başarıyla eklendi!')
        return redirect('quiz:question_bank_detail', bank_id=bank_id)
    
    context = {
        'bank': bank
    }
    return render(request, 'quiz/question_create.html', context)


@login_required
@require_POST
def question_bulk_upload(request, bank_id):
    """Teacher: Bulk upload questions from text or file"""
    bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Check permission
    if bank.created_by != request.user and not bank.is_shared:
        messages.error(request, 'Bu soru bankasına soru ekleme yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    questions_text = request.POST.get('questions', '')
    uploaded_file = request.FILES.get('file')
    
    if uploaded_file:
        try:
            questions_text = uploaded_file.read().decode('utf-8')
        except Exception as e:
            messages.error(request, f'Dosya okunamadı: {str(e)}')
            return redirect('quiz:question_bank_detail', bank_id=bank_id)
    
    if not questions_text.strip():
        messages.error(request, 'Lütfen soruları girin veya dosya yükleyin')
        return redirect('quiz:question_bank_detail', bank_id=bank_id)
    
    lines = [line.strip() for line in questions_text.split('\n') if line.strip()]
    created_count = 0
    error_count = 0
    
    for line in lines:
        try:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 3:
                error_count += 1
                continue
            
            question_text = parts[0]
            question_type = parts[1].lower()
            correct_answer = parts[2] if len(parts) > 2 else ''
            points = float(parts[3]) if len(parts) > 3 and parts[3] else 1.0
            
            question = Question.objects.create(
                bank=bank,
                question_text=question_text,
                question_type=question_type,
                correct_answer=correct_answer,
                points=points
            )
            
            # Parse options for multiple choice
            if question_type == 'multiple_choice' and len(parts) > 4:
                option_map = {'A': 'option_a', 'B': 'option_b', 'C': 'option_c', 'D': 'option_d', 'E': 'option_e'}
                for part in parts[4:]:
                    if ')' in part:
                        option_letter = part.split(')')[0].strip()
                        option_text = part.split(')', 1)[1].strip()
                        if option_letter in option_map:
                            setattr(question, option_map[option_letter], option_text)
                question.save()
            
            created_count += 1
        except Exception as e:
            error_count += 1
            continue
    
    if created_count > 0:
        messages.success(request, f'{created_count} soru başarıyla eklendi!')
    if error_count > 0:
        messages.warning(request, f'{error_count} soru eklenirken hata oluştu.')
    
    return redirect('quiz:question_bank_detail', bank_id=bank_id)


@login_required
def quiz_create(request, group_id):
    """Teacher: Create a quiz"""
    course_group = get_object_or_404(CourseGroup, id=group_id)
    
    # Check if user is the teacher
    try:
        teacher = Teacher.objects.get(user=request.user)
        if course_group.teacher != teacher:
            messages.error(request, 'Bu derse sınav oluşturma yetkiniz yok')
            return redirect('courses:group_detail', pk=group_id)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('courses:group_detail', pk=group_id)
    
    if request.method == 'POST':
        # Create quiz
        use_random = request.POST.get('use_random_questions') == 'on'
        quiz = Quiz.objects.create(
            course_group=course_group,
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            start_time=request.POST.get('start_time'),
            end_time=request.POST.get('end_time'),
            duration_minutes=int(request.POST.get('duration_minutes', 60)),
            max_attempts=int(request.POST.get('max_attempts', 1)),
            passing_score=float(request.POST.get('passing_score', 60)),
            shuffle_questions=request.POST.get('shuffle_questions') == 'on',
            shuffle_options=request.POST.get('shuffle_options') == 'on',
            show_results_immediately=request.POST.get('show_results_immediately') == 'on',
            auto_submit=request.POST.get('auto_submit') == 'on',
            use_random_questions=use_random,
            random_question_count=int(request.POST.get('random_question_count', 40)) if use_random else 0,
            random_question_pool_size=int(request.POST.get('random_question_pool_size', 250)) if use_random else 0
        )
        
        messages.success(request, f'{quiz.title} oluşturuldu. Şimdi soru ekleyebilirsiniz.')
        return redirect('quiz:quiz_add_questions', quiz_id=quiz.id)
    
    # Get question banks for this teacher
    banks = QuestionBank.objects.filter(
        Q(created_by=request.user) | Q(is_shared=True)
    )
    
    context = {
        'course_group': course_group,
        'banks': banks
    }
    return render(request, 'quiz/quiz_create.html', context)


@login_required
def quiz_create_default(request):
    """
    Teacher: shortcut from sidebar to quiz creation.
    Finds the first active course group for this teacher and redirects to its quiz_create page.
    """
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('users:dashboard')

    course_group = CourseGroup.objects.filter(
        teacher=teacher,
        status='active'
    ).order_by('course__code', 'semester', 'name').first()

    if not course_group:
        messages.error(request, 'Aktif ders bulunamadı, önce bir ders oluşturun veya atanmasını isteyin.')
        return redirect('teachers:dashboard')

    return redirect('quiz:quiz_create', group_id=course_group.id)


@login_required
def quiz_add_questions(request, quiz_id):
    """Teacher: Add questions to quiz from question bank"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permission
    if quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu sınava soru ekleme yetkiniz yok')
        return redirect('courses:dashboard')
    
    if request.method == 'POST':
        question_ids = request.POST.getlist('questions')
        
        if not question_ids:
            messages.error(request, 'Lütfen en az bir soru seçin!')
            banks = QuestionBank.objects.filter(
                Q(created_by=request.user) | Q(is_shared=True)
            ).prefetch_related('questions')
            added_question_ids = quiz.questions.filter(assigned_to_student__isnull=True).values_list('question_id', flat=True)
            context = {
                'quiz': quiz,
                'banks': banks,
                'added_question_ids': list(added_question_ids)
            }
            return render(request, 'quiz/quiz_add_questions.html', context)
        
        # Check if random questions mode
        if quiz.use_random_questions:
            # For random mode, we need at least pool_size questions
            if len(question_ids) < quiz.random_question_pool_size:
                messages.error(request, f'Rastgele soru modu için en az {quiz.random_question_pool_size} soru seçmelisiniz!')
                banks = QuestionBank.objects.filter(
                    Q(created_by=request.user) | Q(is_shared=True)
                ).prefetch_related('questions')
                added_question_ids = quiz.questions.filter(assigned_to_student__isnull=True).values_list('question_id', flat=True)
                context = {
                    'quiz': quiz,
                    'banks': banks,
                    'added_question_ids': list(added_question_ids)
                }
                return render(request, 'quiz/quiz_add_questions.html', context)
        
        order = 1
        added_count = 0
        
        for question_id in question_ids:
            try:
                question = Question.objects.get(id=question_id)
                # For random mode, don't assign to specific student yet (will be done when student starts)
                # For normal mode, assigned_to_student is None
                if not QuizQuestion.objects.filter(quiz=quiz, question=question, assigned_to_student__isnull=True).exists():
                    QuizQuestion.objects.create(
                        quiz=quiz,
                        question=question,
                        order=order,
                        points=float(request.POST.get(f'points_{question_id}', question.points)),
                        assigned_to_student=None  # Will be assigned when student starts if random mode
                    )
                    order += 1
                    added_count += 1
            except Question.DoesNotExist:
                continue
        
        if added_count > 0:
            if quiz.use_random_questions:
                messages.success(request, f'{added_count} soru havuzu oluşturuldu! Her öğrenci sınava başladığında rastgele {quiz.random_question_count} soru alacak.')
            else:
                messages.success(request, f'{added_count} soru başarıyla eklendi!')
        else:
            messages.warning(request, 'Seçilen sorular zaten sınava eklenmiş.')
        
        return redirect('quiz:quiz_detail', quiz_id=quiz.id)
    
    # Get available question banks
    banks = QuestionBank.objects.filter(
        Q(created_by=request.user) | Q(is_shared=True)
    ).prefetch_related('questions')
    
    # Already added questions (only unassigned ones)
    added_question_ids = quiz.questions.filter(assigned_to_student__isnull=True).values_list('question_id', flat=True)
    
    context = {
        'quiz': quiz,
        'banks': banks,
        'added_question_ids': list(added_question_ids)
    }
    return render(request, 'quiz/quiz_add_questions.html', context)


@login_required
def quiz_detail(request, quiz_id):
    """Teacher: View quiz details and manage"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permission
    if quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu quiz\'e erişim yetkiniz yok')
        return redirect('courses:dashboard')
    
    # Get all questions (including pool questions for random mode)
    questions = quiz.questions.filter(assigned_to_student__isnull=True).select_related('question__bank')
    attempts = quiz.attempts.all().select_related('student').order_by('-started_at')
    
    # Statistics
    stats = {
        'total_questions': questions.count(),
        'total_points': quiz.total_points,
        'total_attempts': attempts.count(),
        'completed_attempts': attempts.filter(status__in=['submitted', 'auto_submitted']).count(),
        'average_score': attempts.filter(
            status__in=['submitted', 'auto_submitted'],
            score__isnull=False
        ).aggregate(avg=Avg('score'))['avg'] or 0
    }
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'attempts': attempts,
        'stats': stats
    }
    return render(request, 'quiz/quiz_detail_teacher.html', context)


@login_required
def quiz_take(request, quiz_id):
    """Student: Take a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check if student is enrolled
    try:
        enrollment = Enrollment.objects.get(
            student__user=request.user,
            group=quiz.course_group,
            status='enrolled'
        )
    except Enrollment.DoesNotExist:
        messages.error(request, 'Bu derse kayıtlı değilsiniz')
        return redirect('courses:dashboard')
    
    # Check if quiz is available
    if not quiz.is_available:
        messages.warning(request, 'Bu quiz şu anda aktif değil')
        return redirect('courses:group_detail', group_id=quiz.course_group.id)
    
    # Check attempts
    attempts_count = QuizAttempt.objects.filter(
        quiz=quiz,
        student=request.user
    ).count()
    
    if attempts_count >= quiz.max_attempts:
        messages.warning(request, f'Maksimum deneme hakkınızı ({quiz.max_attempts}) kullandınız')
        return redirect('quiz:quiz_results', quiz_id=quiz.id)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        quiz=quiz,
        student=request.user,
        attempt_number=attempts_count + 1,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return redirect('quiz:quiz_attempt', attempt_id=attempt.id)


@login_required
def quiz_attempt(request, attempt_id):
    """Student: Take quiz (active attempt)"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    # Check permission
    if attempt.student != request.user:
        messages.error(request, 'Bu denemeye erişim yetkiniz yok')
        return redirect('courses:dashboard')
    
    # Check if already completed
    if attempt.status != 'in_progress':
        return redirect('quiz:quiz_attempt_review', attempt_id=attempt.id)
    
    # Check if expired and auto-submit
    if attempt.auto_submit_if_expired():
        messages.warning(request, 'Süre dolduğu için quiz otomatik teslim edildi')
        return redirect('quiz:quiz_attempt_review', attempt_id=attempt.id)
    
    if request.method == 'POST':
        # Save answers
        for key, value in request.POST.items():
            if key.startswith('question_'):
                quiz_question_id = key.replace('question_', '')
                quiz_question = QuizQuestion.objects.get(id=quiz_question_id)
                
                answer, created = QuizAnswer.objects.get_or_create(
                    attempt=attempt,
                    quiz_question=quiz_question
                )
                
                if quiz_question.question.question_type in ['multiple_choice', 'true_false']:
                    answer.selected_option = value
                else:
                    answer.answer_text = value
                
                answer.save()
                answer.check_answer()  # Auto-grade if possible
        
        # Submit quiz
        attempt.status = 'submitted'
        attempt.submitted_at = timezone.now()
        
        # Calculate score
        total_score = 0
        for answer in attempt.answers.all():
            if answer.points_earned:
                total_score += answer.points_earned
        
        attempt.score = total_score
        # Calculate percentage based on actual questions answered
        actual_total = sum(q.points for q in questions)
        attempt.percentage = (total_score / actual_total * 100) if actual_total > 0 else 0
        attempt.save()
        
        messages.success(request, 'Quiz teslim edildi!')
        return redirect('quiz:quiz_attempt_review', attempt_id=attempt.id)
    
    # Get questions - if random mode, only get questions assigned to this student
    if attempt.quiz.use_random_questions:
        questions = QuizQuestion.objects.filter(
            quiz=attempt.quiz,
            assigned_to_student=request.user
        ).select_related('question').order_by('order')
    else:
        questions = attempt.quiz.questions.filter(assigned_to_student__isnull=True).select_related('question').order_by('order')
    
    # Get existing answers
    existing_answers = {
        answer.quiz_question_id: answer 
        for answer in attempt.answers.all()
    }
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'questions': questions,
        'existing_answers': existing_answers,
        'remaining_time': attempt.remaining_time_seconds
    }
    return render(request, 'quiz/quiz_attempt.html', context)


@login_required
def quiz_attempt_review(request, attempt_id):
    """Student: Review quiz attempt results"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    
    # Check permission - student field is User, not Student model
    if attempt.student != request.user:
        messages.error(request, 'Bu denemeye erişim yetkiniz yok')
        return redirect('quiz:quiz_list_student')
    
    # Get all quiz questions ordered
    # Get questions - if random mode, only get questions assigned to this student
    if attempt.quiz.use_random_questions:
        quiz_questions = QuizQuestion.objects.filter(
            quiz=attempt.quiz,
            assigned_to_student=request.user
        ).select_related('question').order_by('order')
    else:
        quiz_questions = attempt.quiz.questions.filter(assigned_to_student__isnull=True).select_related('question').order_by('order')
    
    # Get answers as a dict for easy lookup
    answers_dict = {
        answer.quiz_question_id: answer 
        for answer in attempt.answers.all().select_related('quiz_question__question')
    }
    
    # Create list of questions with their answers
    questions_with_answers = []
    for quiz_question in quiz_questions:
        questions_with_answers.append({
            'quiz_question': quiz_question,
            'question': quiz_question.question,
            'answer': answers_dict.get(quiz_question.id)
        })
    
    context = {
        'attempt': attempt,
        'questions_with_answers': questions_with_answers,
        'quiz': attempt.quiz
    }
    return render(request, 'quiz/quiz_attempt_review.html', context)


@login_required
def quiz_list_student(request):
    """Student: List available quizzes"""
    # Get enrolled courses
    enrollments = Enrollment.objects.filter(
        student__user=request.user,
        status='enrolled'
    ).select_related('group')
    
    course_groups = [e.group for e in enrollments]
    
    # Get quizzes
    quizzes = Quiz.objects.filter(
        course_group__in=course_groups,
        is_active=True
    ).select_related('course_group').order_by('-start_time')
    
    # Get attempts - simplified for template
    my_attempts = QuizAttempt.objects.filter(
        student=request.user
    ).select_related('quiz')
    
    # Create quiz data with attempts
    quiz_data = []
    for quiz in quizzes:
        quiz_attempts = [a for a in my_attempts if a.quiz_id == quiz.id]
        quiz_data.append({
            'quiz': quiz,
            'attempts': quiz_attempts,
            'can_take': len(quiz_attempts) < quiz.max_attempts
        })
    
    context = {
        'quiz_data': quiz_data
    }
    return render(request, 'quiz/quiz_list_student_simple.html', context)


@login_required
def quiz_list(request):
    """Teacher: List all quizzes"""
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('users:dashboard')
    
    quizzes = Quiz.objects.filter(
        course_group__teacher=teacher
    ).select_related('course_group').order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
        'teacher': teacher
    }
    return render(request, 'quiz/quiz_list.html', context)
