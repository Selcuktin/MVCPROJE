"""Forum and Messaging Views"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import DirectMessage, MessageThread
from apps.users.models import User


@login_required
def inbox(request):
    """View inbox messages"""
    received = DirectMessage.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('-created_at')
    
    sent = DirectMessage.objects.filter(
        sender=request.user
    ).select_related('recipient').order_by('-created_at')
    
    unread_count = received.filter(is_read=False).count()
    
    context = {
        # show full history (newest first) - not limited to 1 week / 20 items
        'received_messages': received,
        'sent_messages': sent,
        'unread_count': unread_count
    }
    return render(request, 'forum/inbox.html', context)


@login_required
def message_compose(request):
    """Compose new message"""
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id') or request.POST.get('recipient')
        subject = request.POST.get('subject') or ''
        message_text = request.POST.get('message') or request.POST.get('body') or ''
        
        try:
            if not recipient_id:
                raise User.DoesNotExist()

            recipient = User.objects.get(id=recipient_id)
            DirectMessage.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject.strip() or '(Konu yok)',
                message=message_text.strip()
            )
            messages.success(request, 'Mesaj gönderildi')
            return redirect('forum:inbox')
        except User.DoesNotExist:
            messages.error(request, 'Alıcı bulunamadı')
    
    # Get possible recipients (teachers and students in same courses)
    from apps.courses.models import Enrollment, CourseGroup
    from apps.teachers.models import Teacher
    
    recipients = []
    seen_ids = set()
    
    # If student, get their teachers
    try:
        from apps.students.models import Student
        student = Student.objects.get(user=request.user)
        enrollments = Enrollment.objects.filter(
            student=student,
            status='enrolled'
        ).select_related('group__teacher')
        
        for enrollment in enrollments:
            if enrollment.group.teacher and enrollment.group.teacher.user:
                u = enrollment.group.teacher.user
                if u.id not in seen_ids:
                    seen_ids.add(u.id)
                    recipients.append({
                        'user': u,
                        'name': f"{enrollment.group.teacher.first_name} {enrollment.group.teacher.last_name}",
                        'role': 'Öğretmen'
                    })
    except:
        pass
    
    # If teacher, get their students
    try:
        teacher = Teacher.objects.get(user=request.user)
        course_groups = CourseGroup.objects.filter(teacher=teacher)
        enrollments = Enrollment.objects.filter(
            group__in=course_groups,
            status='enrolled'
        ).select_related('student')
        
        for enrollment in enrollments:
            u = enrollment.student.user
            if u.id not in seen_ids:
                seen_ids.add(u.id)
                recipients.append({
                    'user': u,
                    'name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                    'role': 'Öğrenci'
                })
    except:
        pass
    
    context = {
        'recipients': recipients
    }
    return render(request, 'forum/message_compose.html', context)


@login_required
def message_detail(request, message_id):
    """View message detail"""
    message = get_object_or_404(DirectMessage, id=message_id)
    
    # Check permission
    if message.recipient != request.user and message.sender != request.user:
        messages.error(request, 'Bu mesaja erişim yetkiniz yok')
        return redirect('forum:inbox')
    
    # Mark as read if recipient
    if message.recipient == request.user:
        message.mark_as_read()
    
    # Get conversation thread
    thread = DirectMessage.objects.filter(
        Q(sender=message.sender, recipient=message.recipient) |
        Q(sender=message.recipient, recipient=message.sender)
    ).order_by('created_at')
    
    context = {
        'message': message,
        'thread': thread
    }
    return render(request, 'forum/message_detail.html', context)


# ========================================
# API ENDPOINTS FOR FLOATING CHAT
# ========================================

@login_required
@require_http_methods(["GET"])
def api_inbox(request):
    """
    API: Floating chat için gelen kutusu özeti.
    Kullanıcıyla yapılan her konuşma için son mesajı ve son 50 mesajlık geçmişi döner.
    """
    qs = DirectMessage.objects.filter(
        Q(sender=request.user) | Q(recipient=request.user)
    ).select_related('sender', 'recipient').order_by('created_at')  # kronolojik sıralama

    threads_map = {}
    for msg in qs:
        other = msg.recipient if msg.sender_id == request.user.id else msg.sender
        if other_id := getattr(other, 'id', None):
            # Kullanıcının gerçek ismini al (Student veya Teacher modelinden)
            other_name = other.username
            try:
                from apps.students.models import Student
                student = Student.objects.get(user=other)
                other_name = f"{student.first_name} {student.last_name}".strip()
            except:
                try:
                    from apps.teachers.models import Teacher
                    teacher = Teacher.objects.get(user=other)
                    other_name = f"{teacher.first_name} {teacher.last_name}".strip()
                except:
                    # Fallback: User modelindeki isim
                    other_name = f"{other.first_name} {other.last_name}".strip() or other.username
            
            thread = threads_map.setdefault(
                other_id,
                {
                    'other_id': other_id,
                    'other_user': other_name,
                    'last_message': '',
                    'last_date': '',
                    'messages': [],
                },
            )
            # Gönderenin gerçek ismini al
            sender_name = msg.sender.username
            try:
                from apps.students.models import Student
                student = Student.objects.get(user=msg.sender)
                sender_name = f"{student.first_name} {student.last_name}".strip()
            except:
                try:
                    from apps.teachers.models import Teacher
                    teacher = Teacher.objects.get(user=msg.sender)
                    sender_name = f"{teacher.first_name} {teacher.last_name}".strip()
                except:
                    sender_name = f"{msg.sender.first_name} {msg.sender.last_name}".strip() or msg.sender.username
            
            thread['messages'].append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': sender_name,
                'message': msg.message,
                'text': msg.message,
                'is_me': (msg.sender_id == request.user.id),
                'is_read': msg.is_read,
                'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M'),
            })
            # Son mesaj bilgilerini güncelle
            thread['last_message'] = msg.message[:120] + '...' if len(msg.message) > 120 else msg.message
            thread['last_date'] = msg.created_at.strftime('%d.%m.%Y %H:%M')

    # Her thread için sadece son 50 mesajı tut (performans için)
    threads = []
    for t in threads_map.values():
        if len(t['messages']) > 50:
            t['messages'] = t['messages'][-50:]
        threads.append(t)

    # En son mesaja göre sondan başa doğru sırala
    threads.sort(key=lambda x: x['last_date'], reverse=True)
    threads = threads[:15]

    data = {
        'threads': threads
    }
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def api_send_message(request):
    """API: Send a message from floating chat"""
    try:
        data = json.loads(request.body)
        # Eski ve yeni payload formatlarını destekle
        recipient_id = data.get('recipient_id') or data.get('to')
        subject = data.get('subject') or 'Sohbet'
        message_text = data.get('message') or data.get('text')
        
        if not all([recipient_id, message_text]):
            return JsonResponse({
                'success': False,
                'error': 'Tüm alanlar gerekli'
            })
        
        recipient = User.objects.get(id=recipient_id)
        
        DirectMessage.objects.create(
            sender=request.user,
            recipient=recipient,
            subject=subject,
            message=message_text
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Mesaj başarıyla gönderildi'
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alıcı bulunamadı'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_recipients(request):
    """API: Get possible recipients for floating chat"""
    from apps.courses.models import Enrollment, CourseGroup
    from apps.teachers.models import Teacher
    from apps.students.models import Student
    
    recipients = []
    seen_ids = set()
    
    # If student, get their teachers AND classmates
    try:
        student = Student.objects.get(user=request.user)
        enrollments = Enrollment.objects.filter(
            student=student,
            status='enrolled'
        ).select_related('group__teacher__user', 'group')
        
        # Get teachers
        for enrollment in enrollments:
            if enrollment.group.teacher and enrollment.group.teacher.user:
                user_id = enrollment.group.teacher.user.id
                if user_id not in seen_ids:
                    seen_ids.add(user_id)
                    recipients.append({
                        'id': user_id,
                        'name': f"{enrollment.group.teacher.first_name} {enrollment.group.teacher.last_name}",
                        'role': 'Öğretmen'
                    })
        
        # Get classmates (other students in same courses)
        enrolled_groups = [e.group for e in enrollments]
        classmate_enrollments = Enrollment.objects.filter(
            group__in=enrolled_groups,
            status='enrolled'
        ).exclude(student=student).select_related('student__user').distinct()
        
        for enrollment in classmate_enrollments:
            user_id = enrollment.student.user.id
            if user_id not in seen_ids:
                seen_ids.add(user_id)
                recipients.append({
                    'id': user_id,
                    'name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                    'role': 'Öğrenci'
                })
    except Student.DoesNotExist:
        pass
    
    # If teacher, get their students AND other teachers
    try:
        teacher = Teacher.objects.get(user=request.user)
        
        # Get students
        course_groups = CourseGroup.objects.filter(teacher=teacher)
        enrollments = Enrollment.objects.filter(
            group__in=course_groups,
            status='enrolled'
        ).select_related('student__user').distinct()
        
        for enrollment in enrollments:
            user_id = enrollment.student.user.id
            if user_id not in seen_ids:
                seen_ids.add(user_id)
                recipients.append({
                    'id': user_id,
                    'name': f"{enrollment.student.first_name} {enrollment.student.last_name}",
                    'role': 'Öğrenci'
                })
        
        # Get other teachers
        other_teachers = Teacher.objects.exclude(user=request.user).select_related('user')
        for other_teacher in other_teachers:
            if other_teacher.user:
                user_id = other_teacher.user.id
                if user_id not in seen_ids:
                    seen_ids.add(user_id)
                    recipients.append({
                        'id': user_id,
                        'name': f"{other_teacher.first_name} {other_teacher.last_name}",
                        'role': 'Öğretmen'
                    })
    except Teacher.DoesNotExist:
        pass
    
    return JsonResponse({'recipients': recipients})


@login_required
@require_http_methods(["GET"])
def api_thread(request, user_id):
    """API: Get conversation between request.user and user_id"""
    try:
        other = get_object_or_404(User, id=user_id)

        qs = DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other) |
            Q(sender=other, recipient=request.user)
        ).select_related('sender', 'recipient').order_by('created_at')

        # Mark received messages from other as read
        DirectMessage.objects.filter(sender=other, recipient=request.user, is_read=False).update(is_read=True)

        messages_list = []
        for m in qs[-100:]:  # last 100 for performance
            # Gönderenin gerçek ismini al
            sender_name = m.sender.username
            try:
                from apps.students.models import Student
                student = Student.objects.get(user=m.sender)
                sender_name = f"{student.first_name} {student.last_name}".strip()
            except:
                try:
                    from apps.teachers.models import Teacher
                    teacher = Teacher.objects.get(user=m.sender)
                    sender_name = f"{teacher.first_name} {teacher.last_name}".strip()
                except:
                    sender_name = f"{m.sender.first_name} {m.sender.last_name}".strip() or m.sender.username
            
            messages_list.append({
                'id': m.id,
                'sender_id': m.sender_id,
                'sender_name': sender_name,
                'message': m.message,
                'text': m.message,  # floating chat için kısayol
                'is_me': (m.sender_id == request.user.id),
                'is_read': m.is_read,
                'created_at': m.created_at.strftime('%d.%m.%Y %H:%M'),
            })
        
        data = {'messages': messages_list}
        return JsonResponse(data)
    except Exception as e:
        # Herhangi bir hata durumunda bile sohbet penceresini çalışır bırakmak için
        return JsonResponse({
            'messages': [],
            'error': str(e),
        })


@login_required
@require_http_methods(["POST"])
def api_clear_conversation(request, user_id):
    """API: Clear conversation history with a specific user"""
    try:
        other = get_object_or_404(User, id=user_id)
        
        # Delete all messages between these two users
        DirectMessage.objects.filter(
            Q(sender=request.user, recipient=other) |
            Q(sender=other, recipient=request.user)
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Mesaj geçmişi temizlendi'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
