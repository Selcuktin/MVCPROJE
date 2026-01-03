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
    """Teacher/Admin: List all question banks"""
    # Admin veya superuser ise tüm bankaları göster
    if request.user.is_staff or request.user.is_superuser:
        banks = QuestionBank.objects.prefetch_related('questions').select_related('created_by', 'course_group__course')
        context = {
            'banks': banks,
            'teacher': None,
            'is_admin': True
        }
        return render(request, 'quiz/question_bank_list.html', context)
    
    # Öğretmen ise sadece kendi bankalarını göster
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('home')
    
    # SADECE kendi oluşturduğu bankaları göster (shared olanları gösterme)
    banks = QuestionBank.objects.filter(
        created_by=request.user
    ).prefetch_related('questions')
    
    context = {
        'banks': banks,
        'teacher': teacher,
        'is_admin': False
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
    """Teacher/Admin: View/manage questions in a bank"""
    bank = get_object_or_404(QuestionBank, id=bank_id)
    
    # Admin veya superuser her bankaya erişebilir
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Check permission
    if not is_admin and bank.created_by != request.user and not bank.is_shared:
        messages.error(request, 'Bu soru bankasına erişim yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    questions = bank.questions.all().order_by('-created_at')
    
    context = {
        'bank': bank,
        'questions': questions,
        'is_admin': is_admin
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
        explanation = request.POST.get('explanation', '')
        
        if not question_text or not question_type:
            messages.error(request, 'Soru metni ve tipi gerekli')
            return redirect('quiz:question_bank_detail', bank_id=bank_id)
        
        # Find correct answer
        correct_answer = ''
        choices_count = int(request.POST.get('choices_count', 0))
        
        # Get options and find correct one
        option_a = request.POST.get('choice_0', '')
        option_b = request.POST.get('choice_1', '')
        option_c = request.POST.get('choice_2', '')
        option_d = request.POST.get('choice_3', '')
        option_e = request.POST.get('choice_4', '') if choices_count > 4 else ''
        
        # Find which one is correct
        for i in range(choices_count):
            if request.POST.get(f'is_correct_{i}') == 'on':
                correct_answer = chr(65 + i)  # A, B, C, D, E
                break
        
        question = Question.objects.create(
            bank=bank,
            question_text=question_text,
            question_type=question_type,
            points=1,  # Varsayılan puan, sınava eklendiğinde otomatik hesaplanacak
            difficulty='medium',  # Varsayılan zorluk
            explanation=explanation,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            option_e=option_e,
            correct_answer=correct_answer
        )
        
        # Handle image upload
        if 'question_image' in request.FILES:
            question.question_image = request.FILES['question_image']
            question.save()
        
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
    
    # Check permission - SADECE kendi sınavına soru ekleyebilir
    if quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu sınava soru ekleme yetkiniz yok')
        return redirect('teachers:dashboard')
    
    if request.method == 'POST':
        question_ids = request.POST.getlist('questions')
        
        print(f"DEBUG: Received question_ids: {question_ids}")  # Debug log
        
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
        
        # Check if random questions mode - no minimum requirement anymore
        if quiz.use_random_questions:
            # Just check if we have at least as many questions as random_question_count
            if len(question_ids) < quiz.random_question_count:
                messages.warning(request, f'Uyarı: Rastgele soru modu için {quiz.random_question_count} soru gerekiyor, ancak sadece {len(question_ids)} soru seçtiniz. Öğrenciler daha az soru görebilir.')
        
        order = quiz.questions.filter(assigned_to_student__isnull=True).count() + 1
        added_count = 0
        skipped_count = 0
        
        # Otomatik puan hesaplama: 100 puan / toplam soru sayısı
        total_questions_after = order - 1 + len(question_ids)
        points_per_question = round(100.0 / total_questions_after, 2) if total_questions_after > 0 else 1.0
        
        for question_id in question_ids:
            try:
                question = Question.objects.get(id=question_id)
                # Check if already exists
                if QuizQuestion.objects.filter(quiz=quiz, question=question, assigned_to_student__isnull=True).exists():
                    skipped_count += 1
                    print(f"DEBUG: Question {question_id} already exists, skipping")
                    continue
                
                # Create new quiz question with auto-calculated points
                QuizQuestion.objects.create(
                    quiz=quiz,
                    question=question,
                    order=order,
                    points=points_per_question,  # Otomatik hesaplanan puan
                    assigned_to_student=None
                )
                order += 1
                added_count += 1
                print(f"DEBUG: Added question {question_id} with {points_per_question} points")
            except Question.DoesNotExist:
                print(f"DEBUG: Question {question_id} not found")
                continue
            except Exception as e:
                print(f"DEBUG: Error adding question {question_id}: {str(e)}")
                continue
        
        # Tüm soruların puanlarını yeniden hesapla (eşit dağıt)
        all_questions = quiz.questions.filter(assigned_to_student__isnull=True).order_by('order')
        total_count = all_questions.count()
        if total_count > 0:
            points_per_question = round(100.0 / total_count, 2)
            for qq in all_questions:
                qq.points = points_per_question
                qq.save()
        
        print(f"DEBUG: Added {added_count} questions, skipped {skipped_count}, {total_count} total questions, {points_per_question} points each")
        
        if added_count > 0:
            if quiz.use_random_questions:
                messages.success(request, f'✓ {added_count} soru havuza eklendi! Her öğrenci sınava başladığında rastgele {quiz.random_question_count} soru alacak.')
            else:
                messages.success(request, f'✓ {added_count} soru başarıyla sınava eklendi!')
            
            if skipped_count > 0:
                messages.info(request, f'{skipped_count} soru zaten sınava eklenmiş olduğu için atlandı.')
        else:
            if skipped_count > 0:
                messages.warning(request, 'Seçilen tüm sorular zaten sınava eklenmiş.')
            else:
                messages.error(request, 'Hiçbir soru eklenemedi. Lütfen tekrar deneyin.')
        
        return redirect('quiz:quiz_detail', quiz_id=quiz.id)
    
    # Get available question banks - SADECE kendi bankaları
    banks = QuestionBank.objects.filter(
        created_by=request.user
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
    """Teacher: View quiz details and manage - SADECE kendi sınavı"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permission - SADECE kendi sınavını görebilir
    if quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu sınava erişim yetkiniz yok')
        return redirect('teachers:dashboard')
    
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
    
    # Get questions - if random mode, only get questions assigned to this student
    if attempt.quiz.use_random_questions:
        questions = QuizQuestion.objects.filter(
            quiz=attempt.quiz,
            assigned_to_student=request.user
        ).select_related('question').order_by('order')
        
        # If no questions assigned yet, assign them from the pool
        if not questions.exists():
            import random
            pool = list(attempt.quiz.questions.filter(assigned_to_student__isnull=True))
            if pool:
                count = min(len(pool), attempt.quiz.random_question_count)
                selected = random.sample(pool, count)
                for i, pq in enumerate(selected):
                    QuizQuestion.objects.create(
                        quiz=attempt.quiz,
                        question=pq.question,
                        order=i + 1,
                        points=pq.points,
                        assigned_to_student=request.user
                    )
                # Refresh questions
                questions = QuizQuestion.objects.filter(
                    quiz=attempt.quiz,
                    assigned_to_student=request.user
                ).select_related('question').order_by('order')
    else:
        questions = attempt.quiz.questions.filter(assigned_to_student__isnull=True).select_related('question').order_by('order')

    if request.method == 'POST':
        # Save answers
        for key, value in request.POST.items():
            if key.startswith('question_'):
                quiz_question_id = key.replace('question_', '')
                quiz_question = questions.filter(id=quiz_question_id).first()
                if not quiz_question:
                    continue
                
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
        # Calculate percentage based on actual questions
        actual_total = sum(q.points for q in questions)
        attempt.percentage = (total_score / actual_total * 100) if actual_total > 0 else 0
        attempt.save()
        
        messages.success(request, 'Quiz teslim edildi!')
        return redirect('quiz:quiz_attempt_review', attempt_id=attempt.id)
    
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
        
        # En yüksek puanlı denemeyi bul
        best_attempt = quiz.get_student_best_score(request.user)
        
        quiz_data.append({
            'quiz': quiz,
            'attempts': quiz_attempts,
            'can_take': len(quiz_attempts) < quiz.max_attempts,
            'best_attempt': best_attempt,
            'attempts_used': len(quiz_attempts),
            'max_attempts': quiz.max_attempts
        })
    
    context = {
        'quiz_data': quiz_data
    }
    return render(request, 'quiz/quiz_list_student_simple.html', context)


@login_required
def quiz_list(request):
    """Teacher/Admin: List all quizzes"""
    # Admin veya superuser ise tüm sınavları göster
    if request.user.is_staff or request.user.is_superuser:
        quizzes = Quiz.objects.select_related('course_group__course', 'course_group__teacher').order_by('-created_at')
        context = {
            'quizzes': quizzes,
            'teacher': None,
            'is_admin': True
        }
        return render(request, 'quiz/quiz_list.html', context)
    
    # Öğretmen ise sadece kendi sınavlarını göster
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Öğretmen profili bulunamadı')
        return redirect('home')
    
    # SADECE bu öğretmenin derslerindeki sınavlar
    quizzes = Quiz.objects.filter(
        course_group__teacher=teacher
    ).select_related('course_group__course').order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
        'teacher': teacher,
        'is_admin': False
    }
    return render(request, 'quiz/quiz_list.html', context)


@login_required
@require_POST
def quiz_delete(request, quiz_id):
    """Teacher/Admin: Delete a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Admin veya superuser her sınavı silebilir
    is_admin = request.user.is_staff or request.user.is_superuser
    
    # Check permission
    if not is_admin and quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu sınavı silme yetkiniz yok')
        return redirect('quiz:quiz_list')
    
    quiz_title = quiz.title
    quiz.delete()
    messages.success(request, f'{quiz_title} sınavı başarıyla silindi')
    return redirect('quiz:quiz_list')


@login_required
def question_preview(request, question_id):
    """Teacher: Preview a question (AJAX) - SADECE kendi sorusu"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check permission - SADECE kendi sorusunu görebilir
    if question.bank.created_by != request.user:
        return JsonResponse({'success': False, 'error': 'Bu soruya erişim yetkiniz yok'})
    
    data = {
        'success': True,
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'question_type': question.question_type,
            'type_display': question.get_question_type_display(),
            'points': float(question.points),
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d,
            'option_e': question.option_e,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
        }
    }
    
    return JsonResponse(data)


@login_required
def question_edit(request, question_id):
    """Teacher: Edit a question"""
    question = get_object_or_404(Question, id=question_id)
    
    # Check permission
    if question.bank.created_by != request.user:
        messages.error(request, 'Bu soruyu düzenleme yetkiniz yok')
        return redirect('quiz:question_bank_list')
    
    if request.method == 'POST':
        question.question_text = request.POST.get('question_text')
        question.question_type = request.POST.get('question_type')
        question.correct_answer = request.POST.get('correct_answer', '')
        question.explanation = request.POST.get('explanation', '')
        
        # Update options for multiple choice
        if question.question_type == 'multiple_choice':
            question.option_a = request.POST.get('option_a', '')
            question.option_b = request.POST.get('option_b', '')
            question.option_c = request.POST.get('option_c', '')
            question.option_d = request.POST.get('option_d', '')
            question.option_e = request.POST.get('option_e', '')
        
        # Handle image removal
        if request.POST.get('remove_image') == 'true':
            if question.question_image:
                question.question_image.delete(save=False)
                question.question_image = None
        
        # Handle new image upload
        if 'question_image' in request.FILES:
            # Delete old image if exists
            if question.question_image:
                question.question_image.delete(save=False)
            question.question_image = request.FILES['question_image']
        
        question.save()
        messages.success(request, 'Soru başarıyla güncellendi!')
        return redirect('quiz:question_bank_detail', bank_id=question.bank.id)
    
    context = {
        'question': question,
        'bank': question.bank
    }
    return render(request, 'quiz/question_edit.html', context)


@login_required
@require_POST
def question_delete(request, question_id):
    """Teacher: Delete a question"""
    question = get_object_or_404(Question, id=question_id)
    bank_id = question.bank.id
    
    # Check permission
    if question.bank.created_by != request.user:
        messages.error(request, 'Bu soruyu silme yetkiniz yok')
        return redirect('quiz:question_bank_detail', bank_id=bank_id)
    
    question.delete()
    messages.success(request, 'Soru başarıyla silindi!')
    return redirect('quiz:question_bank_detail', bank_id=bank_id)


@login_required
def quiz_edit(request, quiz_id):
    """Teacher: Edit a quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Check permission
    if quiz.course_group.teacher.user != request.user:
        messages.error(request, 'Bu sınavı düzenleme yetkiniz yok')
        return redirect('quiz:quiz_list')
    
    if request.method == 'POST':
        quiz.title = request.POST.get('title')
        quiz.description = request.POST.get('description', '')
        quiz.start_time = request.POST.get('start_time')
        quiz.end_time = request.POST.get('end_time')
        quiz.duration_minutes = int(request.POST.get('duration_minutes', 60))
        quiz.max_attempts = int(request.POST.get('max_attempts', 1))
        quiz.shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        quiz.shuffle_options = request.POST.get('shuffle_options') == 'on'
        quiz.show_results_immediately = request.POST.get('show_results_immediately') == 'on'
        quiz.auto_submit = request.POST.get('auto_submit') == 'on'
        
        quiz.save()
        messages.success(request, 'Sınav başarıyla güncellendi!')
        return redirect('quiz:quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'course_group': quiz.course_group
    }
    return render(request, 'quiz/quiz_edit.html', context)
