"""
Service Layer: Business logic and data processing operations.
Bu dosya ders işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import csv
from io import BytesIO, StringIO
import os
import re
import difflib
from typing import List, Dict, Any, Optional

from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement, AssignmentHistory, ExampleQuestion, Quiz, QuizQuestion, QuizChoice
from apps.students.models import Student
from apps.teachers.models import Teacher


class CourseService:
    """Course business logic service"""
    
    def get_filtered_courses(self, filters):
        """Get courses with applied filters"""
        queryset = Course.objects.filter(status='active')
        
        if filters.get('search'):
            queryset = queryset.filter(
                Q(code__icontains=filters['search']) |
                Q(name__icontains=filters['search']) |
                Q(department__icontains=filters['search'])
            )
        
        if filters.get('department'):
            queryset = queryset.filter(department__icontains=filters['department'])
            
        if filters.get('semester'):
            queryset = queryset.filter(semester=filters['semester'])
            
        return queryset.order_by('code')
    
    def get_course_with_details(self, course):
        """Get course with related enrollments and content"""
        enrollments = Enrollment.objects.filter(
            group__course=course,
            status='enrolled'
        ).select_related('student', 'group').order_by('student__first_name')
        
        # Get course contents
        try:
            from .models import CourseContent
            contents = CourseContent.objects.filter(
                course=course,
                is_active=True
            ).order_by('week_number', 'upload_date')
        except:
            contents = []
        
        return {
            'course': course,
            'enrollments': enrollments,
            'enrolled_count': enrollments.count(),
            'contents': contents,
            'teacher': course.groups.filter(status='active').first().teacher if course.groups.filter(status='active').exists() else None
        }
    
    def create_course(self, form_data):
        """Create new course"""
        course = Course.objects.create(**form_data)
        return course
    
    def update_course(self, course, form_data):
        """Update existing course"""
        for key, value in form_data.items():
            setattr(course, key, value)
        course.save()
        return course
    
    def delete_course(self, course):
        """Delete course (soft delete)"""
        course.status = 'inactive'
        course.save()
        return True


class AssignmentService:
    """Assignment business logic service"""
    
    def get_user_assignments(self, user, user_type, filters):
        """Get assignments based on user type and filters"""
        if user_type == 'student':
            try:
                student = Student.objects.get(user=user)
                queryset = Assignment.objects.filter(
                    group__enrollments__student=student,
                    status='active'
                ).select_related('group__course').prefetch_related('submissions', 'group__enrollments')
            except Student.DoesNotExist:
                queryset = Assignment.objects.none()
                
        elif user_type == 'teacher':
            try:
                teacher = Teacher.objects.get(user=user)
                queryset = Assignment.objects.filter(
                    group__teacher=teacher
                ).select_related('group__course').prefetch_related('submissions', 'group__enrollments')
            except Teacher.DoesNotExist:
                queryset = Assignment.objects.none()
        else:
            queryset = Assignment.objects.select_related('group__course', 'group__teacher').prefetch_related('submissions', 'group__enrollments')
        
        # Apply filters
        if filters.get('course'):
            queryset = queryset.filter(group__course_id=filters['course'])
        
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        return queryset.order_by('-create_date')
    
    def get_assignment_with_details(self, assignment, user):
        """Get assignment with submissions and user-specific data"""
        data = {'assignment': assignment}
        
        # Get submissions for teachers
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'teacher':
            data['submissions'] = assignment.submissions.select_related('student')
        
        # Get user's submission for students
        if hasattr(user, 'userprofile') and user.userprofile.user_type == 'student':
            try:
                student = Student.objects.get(user=user)
                data['submission'] = Submission.objects.filter(
                    assignment=assignment, student=student
                ).first()
                data['can_submit'] = timezone.now() <= assignment.due_date
            except Student.DoesNotExist:
                data['submission'] = None
                data['can_submit'] = False
        
        return data
    
    def create_assignment(self, form_data, user):
        """Create new assignment"""
        try:
            teacher = Teacher.objects.get(user=user)
            assignment = Assignment.objects.create(**form_data)
            return assignment
        except Teacher.DoesNotExist:
            raise ValueError("Only teachers can create assignments")
    
    def submit_assignment(self, assignment, user, submission_data):
        """Submit assignment"""
        try:
            student = Student.objects.get(user=user)
            
            # Check if already submitted
            if Submission.objects.filter(assignment=assignment, student=student).exists():
                raise ValueError("Assignment already submitted")
            
            # Check deadline
            if timezone.now() > assignment.due_date:
                raise ValueError("Assignment deadline has passed")
            
            submission = Submission.objects.create(
                assignment=assignment,
                student=student,
                **submission_data
            )
            return submission
            
        except Student.DoesNotExist:
            raise ValueError("Only students can submit assignments")


class ReportService:
    """Report generation service"""
    
    def generate_student_report(self, format_type='pdf'):
        """Generate student report in specified format"""
        enrollments = Enrollment.objects.select_related('student', 'group__course', 'group__teacher')
        
        if format_type == 'pdf':
            return self._generate_pdf_report(enrollments, 'student_report')
        elif format_type == 'excel':
            return self._generate_excel_report(enrollments, 'student_report')
        elif format_type == 'csv':
            return self._generate_csv_report(enrollments, 'student_report')
        else:
            raise ValueError("Unsupported format type")
    
    def generate_course_report(self, course, format_type='pdf'):
        """Generate course report"""
        enrollments = Enrollment.objects.filter(group__course=course).select_related('student', 'group')
        
        if format_type == 'pdf':
            return self._generate_pdf_report(enrollments, f'course_report_{course.code}')
        elif format_type == 'excel':
            return self._generate_excel_report(enrollments, f'course_report_{course.code}')
        elif format_type == 'csv':
            return self._generate_csv_report(enrollments, f'course_report_{course.code}')
    
    def generate_assignment_report(self, assignment, format_type='pdf'):
        """Generate assignment report"""
        submissions = Submission.objects.filter(assignment=assignment).select_related('student')
        
        if format_type == 'pdf':
            return self._generate_assignment_pdf_report(submissions, assignment)
        elif format_type == 'excel':
            return self._generate_assignment_excel_report(submissions, assignment)
        elif format_type == 'csv':
            return self._generate_assignment_csv_report(submissions, assignment)
    
    def _generate_pdf_report(self, data, filename):
        """Generate PDF report"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # PDF content generation
        y = 750
        p.drawString(100, y, f"Report: {filename}")
        y -= 30
        
        for item in data:
            if hasattr(item, 'student'):
                text = f"{item.student.full_name} - {item.group.course.name}"
                p.drawString(100, y, text)
                y -= 20
                if y < 100:
                    p.showPage()
                    y = 750
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        return response
    
    def _generate_excel_report(self, data, filename):
        """Generate Excel report"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        
        # Headers
        headers = ['Student', 'Course', 'Teacher', 'Grade', 'Status']
        for col, header in enumerate(headers, 1):
            ws.cell(row=1, column=col, value=header)
        
        # Data
        for row, item in enumerate(data, 2):
            if hasattr(item, 'student'):
                ws.cell(row=row, column=1, value=item.student.full_name)
                ws.cell(row=row, column=2, value=item.group.course.name)
                ws.cell(row=row, column=3, value=item.group.teacher.full_name)
                ws.cell(row=row, column=4, value=getattr(item, 'grade', 'N/A'))
                ws.cell(row=row, column=5, value=item.get_status_display())
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        wb.save(response)
        return response
    
    def _generate_csv_report(self, data, filename):
        """Generate CSV report"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Student', 'Course', 'Teacher', 'Grade', 'Status'])
        
        for item in data:
            if hasattr(item, 'student'):
                writer.writerow([
                    item.student.full_name,
                    item.group.course.name,
                    item.group.teacher.full_name,
                    getattr(item, 'grade', 'N/A'),
                    item.get_status_display()
                ])
        
        return response
    
    def _generate_assignment_pdf_report(self, submissions, assignment):
        """Generate assignment-specific PDF report"""
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        y = 750
        p.drawString(100, y, f"Assignment Report: {assignment.title}")
        y -= 30
        p.drawString(100, y, f"Course: {assignment.group.course.name}")
        y -= 30
        p.drawString(100, y, f"Due Date: {assignment.due_date.strftime('%d.%m.%Y %H:%M')}")
        y -= 50
        
        p.drawString(100, y, "Submissions:")
        y -= 30
        
        for submission in submissions:
            text = f"{submission.student.full_name} - Score: {submission.score or 'Not graded'}"
            p.drawString(120, y, text)
            y -= 20
            if y < 100:
                p.showPage()
                y = 750
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="assignment_{assignment.id}_report.pdf"'
        return response
    
    def _generate_assignment_excel_report(self, submissions, assignment):
        """Generate assignment-specific Excel report"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Assignment {assignment.id}"
        
        # Assignment info
        ws.cell(row=1, column=1, value="Assignment:")
        ws.cell(row=1, column=2, value=assignment.title)
        ws.cell(row=2, column=1, value="Course:")
        ws.cell(row=2, column=2, value=assignment.group.course.name)
        ws.cell(row=3, column=1, value="Due Date:")
        ws.cell(row=3, column=2, value=assignment.due_date.strftime('%d.%m.%Y %H:%M'))
        
        # Headers
        headers = ['Student', 'Submission Date', 'Score', 'Status', 'Feedback']
        for col, header in enumerate(headers, 1):
            ws.cell(row=5, column=col, value=header)
        
        # Data
        for row, submission in enumerate(submissions, 6):
            ws.cell(row=row, column=1, value=submission.student.full_name)
            ws.cell(row=row, column=2, value=submission.submission_date.strftime('%d.%m.%Y %H:%M'))
            ws.cell(row=row, column=3, value=submission.score or 'Not graded')
            ws.cell(row=row, column=4, value=submission.get_status_display())
            ws.cell(row=row, column=5, value=submission.feedback or '')
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="assignment_{assignment.id}_report.xlsx"'
        wb.save(response)
        return response
    
    def _generate_assignment_csv_report(self, submissions, assignment):
        """Generate assignment-specific CSV report"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="assignment_{assignment.id}_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([f'Assignment: {assignment.title}'])
        writer.writerow([f'Course: {assignment.group.course.name}'])
        writer.writerow([f'Due Date: {assignment.due_date.strftime("%d.%m.%Y %H:%M")}'])
        writer.writerow([])  # Empty row
        writer.writerow(['Student', 'Submission Date', 'Score', 'Status', 'Feedback'])
        
        for submission in submissions:
            writer.writerow([
                submission.student.full_name,
                submission.submission_date.strftime('%d.%m.%Y %H:%M'),
                submission.score or 'Not graded',
                submission.get_status_display(),
                submission.feedback or ''
            ])
        
        return response


class TeacherCourseAssignmentService:
    """Teacher-Course Assignment business logic service"""
    
    def get_current_assignments(self, filters=None):
        """Get current teacher-course assignments with filters"""
        queryset = CourseGroup.objects.filter(status='active').select_related('course', 'teacher')
        
        if filters:
            if filters.get('search'):
                queryset = queryset.filter(
                    Q(course__code__icontains=filters['search']) |
                    Q(course__name__icontains=filters['search']) |
                    Q(teacher__first_name__icontains=filters['search']) |
                    Q(teacher__last_name__icontains=filters['search']) |
                    Q(teacher__department__icontains=filters['search'])
                )
            
            if filters.get('teacher_id'):
                queryset = queryset.filter(teacher_id=filters['teacher_id'])
            
            if filters.get('course_id'):
                queryset = queryset.filter(course_id=filters['course_id'])
            
            if filters.get('department'):
                queryset = queryset.filter(course__department__icontains=filters['department'])
            
            if filters.get('semester'):
                queryset = queryset.filter(semester__icontains=filters['semester'])
        
        return queryset.order_by('-semester', 'course__code')
    
    def get_assignment_history(self, filters=None, limit=50):
        """Get assignment history with filters"""
        queryset = AssignmentHistory.objects.select_related(
            'course_group__course', 'teacher', 'performed_by'
        )
        
        if filters:
            if filters.get('teacher_id'):
                queryset = queryset.filter(teacher_id=filters['teacher_id'])
            
            if filters.get('course_id'):
                queryset = queryset.filter(course_group__course_id=filters['course_id'])
            
            if filters.get('action'):
                queryset = queryset.filter(action=filters['action'])
        
        return queryset[:limit]
    
    def check_compatibility(self, teacher, course):
        """Check if teacher is compatible with course (department match)"""
        compatibility = {
            'is_compatible': False,
            'score': 0,
            'reasons': []
        }
        
        # Check department match
        if teacher.department.lower() == course.department.lower():
            compatibility['is_compatible'] = True
            compatibility['score'] = 100
            compatibility['reasons'].append('Bölüm uyumu: Mükemmel')
        elif teacher.department.lower() in course.department.lower() or course.department.lower() in teacher.department.lower():
            compatibility['is_compatible'] = True
            compatibility['score'] = 70
            compatibility['reasons'].append('Bölüm uyumu: Kısmen uyumlu')
        else:
            compatibility['reasons'].append(f'Bölüm uyumsuzluğu: Öğretmen ({teacher.department}) - Ders ({course.department})')
        
        # Check if teacher already has this course
        existing_assignments = CourseGroup.objects.filter(
            teacher=teacher,
            course=course,
            status='active'
        ).count()
        
        if existing_assignments > 0:
            compatibility['reasons'].append(f'Öğretmen bu dersi zaten veriyor ({existing_assignments} grup)')
            compatibility['score'] = max(0, compatibility['score'] - 20)
        
        return compatibility
    
    def check_schedule_conflicts(self, teacher, course, semester, schedule):
        """Check for schedule conflicts with teacher's other courses"""
        conflicts = []
        
        # Get teacher's other active course groups in the same semester
        other_groups = CourseGroup.objects.filter(
            teacher=teacher,
            semester=semester,
            status='active'
        ).exclude(course=course)
        
        for group in other_groups:
            # Simple schedule conflict check (can be enhanced with proper time parsing)
            if group.schedule and schedule:
                # Check if schedules overlap (basic check)
                if self._schedules_overlap(group.schedule, schedule):
                    conflicts.append({
                        'group': group,
                        'conflict_type': 'Zaman çakışması',
                        'message': f"{group.course.code} ({group.schedule}) ile çakışma var"
                    })
        
        return conflicts
    
    def _schedules_overlap(self, schedule1, schedule2):
        """Check if two schedules overlap (simplified)"""
        # This is a simplified check - in production, proper time parsing should be used
        days1 = self._extract_days(schedule1)
        days2 = self._extract_days(schedule2)
        
        # Check if same day
        if set(days1) & set(days2):
            # Check if time ranges overlap (simplified)
            times1 = self._extract_times(schedule1)
            times2 = self._extract_times(schedule2)
            
            if times1 and times2:
                # Simple overlap check
                return True  # Simplified - should parse times properly
        
        return False
    
    def _extract_days(self, schedule):
        """Extract days from schedule string"""
        days_map = {
            'pazartesi': 'monday', 'salı': 'tuesday', 'çarşamba': 'wednesday',
            'perşembe': 'thursday', 'cuma': 'friday', 'cumartesi': 'saturday', 'pazar': 'sunday'
        }
        days = []
        schedule_lower = schedule.lower()
        for tr_day, en_day in days_map.items():
            if tr_day in schedule_lower:
                days.append(en_day)
        return days
    
    def _extract_times(self, schedule):
        """Extract time ranges from schedule string"""
        import re
        # Match time patterns like "09:00-12:00"
        times = re.findall(r'\d{2}:\d{2}', schedule)
        return times if len(times) >= 2 else None
    
    def assign_course_to_teacher(self, course, teacher, semester, classroom, schedule, performed_by):
        """Assign course to teacher"""
        # Check compatibility
        compatibility = self.check_compatibility(teacher, course)
        
        # Check conflicts
        conflicts = self.check_schedule_conflicts(teacher, course, semester, schedule)
        
        # Create course group
        course_group = CourseGroup.objects.create(
            course=course,
            teacher=teacher,
            semester=semester,
            classroom=classroom,
            schedule=schedule,
            status='active'
        )
        
        # Log assignment history
        action = 'bulk_assign' if hasattr(self, '_bulk_mode') else 'assign'
        AssignmentHistory.objects.create(
            course_group=course_group,
            teacher=teacher,
            action=action,
            description=f"{course.code} - {course.name} dersi {teacher.full_name} öğretmenine atandı.",
            performed_by=performed_by
        )
        
        return {
            'success': True,
            'course_group': course_group,
            'compatibility': compatibility,
            'conflicts': conflicts,
            'warnings': [] if compatibility['is_compatible'] and not conflicts else ['Uyumluluk uyarıları var']
        }
    
    def remove_assignment(self, course_group_id, performed_by):
        """Remove course assignment from teacher"""
        course_group = get_object_or_404(CourseGroup, pk=course_group_id)
        teacher = course_group.teacher
        course = course_group.course
        
        # Log removal history
        AssignmentHistory.objects.create(
            course_group=course_group,
            teacher=teacher,
            action='remove',
            description=f"{course.code} - {course.name} dersi {teacher.full_name} öğretmeninden kaldırıldı.",
            performed_by=performed_by
        )
        
        # Soft delete - set status to inactive
        course_group.status = 'inactive'
        course_group.save()
        
        return {'success': True, 'message': 'Atama başarıyla kaldırıldı'}
    
    def bulk_assign(self, course_ids, teacher_ids, semester, classroom, schedule, performed_by):
        """Bulk assign courses to teachers"""
        self._bulk_mode = True
        results = []
        
        for course_id in course_ids:
            course = Course.objects.get(pk=course_id)
            for teacher_id in teacher_ids:
                teacher = Teacher.objects.get(pk=teacher_id)
                result = self.assign_course_to_teacher(
                    course, teacher, semester, classroom, schedule, performed_by
                )
                results.append(result)
        
        delattr(self, '_bulk_mode')
        return results
    
    def bulk_remove(self, course_group_ids, performed_by):
        """Bulk remove course assignments"""
        results = []
        for group_id in course_group_ids:
            result = self.remove_assignment(group_id, performed_by)
            results.append(result)
        return results
    
    def get_teacher_availability(self, teacher):
        """Get teacher's availability status"""
        active_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
        
        total_courses = active_groups.values('course').distinct().count()
        total_groups = active_groups.count()
        total_students = Enrollment.objects.filter(
            group__in=active_groups,
            status='enrolled'
        ).count()
        
        return {
            'teacher': teacher,
            'total_courses': total_courses,
            'total_groups': total_groups,
            'total_students': total_students,
            'is_available': total_groups < 10,  # Max 10 groups
            'workload_percentage': min(100, (total_groups / 10) * 100)
        }


def solve_question_with_ai(question: ExampleQuestion) -> str:
    """Gemini entegrasyonu: ENV'den GEMINI_API_KEY varsa gerçek çağrı, yoksa fallback."""
    api_key = os.environ.get('GEMINI_API_KEY')
    prompt = (
        "Aşağıdaki soruyu detaylı ve adım adım çöz. Türkçe açıkla.\n"
        "Soru Başlığı: " + (question.title or "") + "\n"
        "Soru İçeriği:\n" + (question.content or "") + "\n"
        "Format:\n- Yaklaşım\n- Adım adım çözüm\n- Varsa formüller\n- Sonuç\n"
    )
    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(prompt)
            text = getattr(resp, 'text', None)
            if text:
                return text
        except Exception:
            pass
    # Fallback
    base = "Yapay Zeka Çözüm Taslağı\n\n"
    if question.question_type == 'quiz':
        return base + (
            f"Soru Başlığı: {question.title}\n"
            "Yaklaşım: Şıkları eleme + tanım/formül doğrulama.\n"
            "Adımlar: Şık analizi → Uygun formül → Sonuç."
        )
    return base + (
        f"Soru Başlığı: {question.title}\n"
        "Çözüm Adımları: Varsayımlar → Tanımlar → Formüller → Ara Hesaplamalar → Sonuç.\n"
        "Kontrol: Birim, sınır koşulları ve mantık kontrolü yapın."
    )


def _split_choices(block: str):
    """A), B), C) ... veya A.,B.,C. şıklarını tespit eder, metni normalize eder."""
    # Şık başlıklarını satır başında ara
    parts = re.split(r"(?m)^(A\)|A\.|A\s*\-|A\:)\s*|^(B\)|B\.|B\s*\-|B\:)\s*|^(C\)|C\.|C\s*\-|C\:)\s*|^(D\)|D\.|D\s*\-|D\:)\s*|^(E\)|E\.|E\s*\-|E\:)\s*", block)
    # re.split dönen yapı etiketler de içerir; basit normalize için satırları birleştir
    cleaned = re.sub(r"\n{2,}", "\n", block).strip()
    return cleaned


def parse_questions_from_text(text: str):
    """Metinden birden çok soruyu yakala. 'Soru 1', '1.', '1)' vb. başlıklarına göre böler.
    Quiz ise şıkları korur. Basit heuristics; gerekirse geliştirilebilir.
    Dönen değer: list[ {title, content, type} ]
    """
    if not text:
        return []
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Soruları başlıklarına göre böl: "Soru 1", "1)", "1." satır başları
    chunks = re.split(r"(?m)^\s*(Soru\s*\d+\s*:?|\d+\)|\d+\.)\s*", text)
    # re.split ilk boş/giriş metni de verebilir; tekrar birleştirirken başlıkları ekle
    results = []
    buffer = []
    title_counter = 0
    for part in chunks:
        if not part:
            continue
        # Başlık gibi görünen parça: 'Soru 1', '1)' vb.
        if re.fullmatch(r"(Soru\s*\d+\s*:?|\d+\)|\d+\.)", part.strip(), flags=re.IGNORECASE):
            # önceki buffer'ı kaydet
            if buffer:
                body = "".join(buffer).strip()
                if body:
                    title_counter += 1
                    results.append({
                        'title': f'Soru {title_counter}',
                        'content': _split_choices(body),
                        'type': 'quiz' if re.search(r"(?m)^(A\)|A\.|B\)|B\.|C\)|C\.|D\)|D\.|E\)|E\.)", body) else 'solution'
                    })
            buffer = []
        else:
            buffer.append(part)
    if buffer:
        body = "".join(buffer).strip()
        if body:
            title_counter += 1
            results.append({
                'title': f'Soru {title_counter}',
                'content': _split_choices(body),
                'type': 'quiz' if re.search(r"(?m)^(A\)|A\.|B\)|B\.|C\)|C\.|D\)|D\.|E\)|E\.)", body) else 'solution'
            })
    return results


def parse_questions_from_docx(file_obj):
    """DOCX içeriğini okuyup text'e çevirir ve parse_questions_from_text ile ayrıştırır."""
    try:
        from docx import Document
        document = Document(file_obj)
        full_text = []
        for p in document.paragraphs:
            full_text.append(p.text)
        text = "\n".join(full_text)
        return parse_questions_from_text(text)
    except Exception:
        return []


# --------- QUIZ PARSING ---------
QUIZ_CHOICE_PATTERN = re.compile(r"^(?P<label>[ABCDE])\)|^(?P<label2>[ABCDE])\.|^(?P<label3>[ABCDE])\s*\-\s*", re.MULTILINE)


def _extract_text_from_pdf(file_obj) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_obj)
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or '')
        return "\n".join(pages)
    except Exception:
        return ''


def parse_quiz_from_text(text: str):
    """Soru ve şıkları çıkar, doğru şık yıldızlı (*A) gibi işaretlenmişse algılar."""
    items = parse_questions_from_text(text)
    quiz_items = []
    for it in items:
        content = it['content']
        # Şıkları bul
        blocks = re.split(r"(?m)^(A\)|A\.|B\)|B\.|C\)|C\.|D\)|D\.|E\)|E\.)\s*", content)
        # blocks karışık gelir; daha basit: satırlara bak
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        question_lines = []
        choices = []
        for line in lines:
            m = re.match(r"^(\*?)([ABCDE])\)?\.?\s*(.+)$", line)
            if m:
                star, label, ctext = m.groups()
                choices.append({'label': label, 'text': ctext.strip(), 'correct': bool(star)})
            else:
                question_lines.append(line)
        question_text = " ".join(question_lines) or it['content']
        correct = None
        for c in choices:
            if c['correct']:
                correct = c['label']
                break
        quiz_items.append({'title': it['title'], 'question': question_text, 'choices': choices, 'correct': correct})
    return quiz_items


def parse_quiz_from_docx(file_obj):
    items = parse_questions_from_docx(file_obj)
    joined = "\n\n".join([f"{it['title']}\n{it['content']}" for it in items])
    return parse_quiz_from_text(joined)


def parse_quiz_from_pdf(file_obj):
    text = _extract_text_from_pdf(file_obj)
    return parse_quiz_from_text(text)


def create_quiz_from_items(course: Course, teacher, title: str, quiz_type: str, items: list, duration_minutes: int = 20) -> Quiz:
    quiz = Quiz.objects.create(course=course, created_by=teacher, title=title, quiz_type=quiz_type, duration_minutes=duration_minutes, is_published=False)
    order = 1
    for it in items:
        q = QuizQuestion.objects.create(quiz=quiz, order=order, text=it.get('question') or it.get('title'))
        correct_obj = None
        for ch in it.get('choices') or []:
            choice = QuizChoice.objects.create(question=q, label=ch.get('label',''), text=ch.get('text',''))
            if it.get('correct') and ch.get('label') == it['correct']:
                correct_obj = choice
        if correct_obj:
            q.correct_choice = correct_obj
            q.save(update_fields=['correct_choice'])
        order += 1
    return quiz


# --------- FEEDBACK GENERATION ---------
def generate_feedback(student, assignment: Assignment, rubric: Dict[str, int] | None = None) -> str:
    """Template tabanlı basit geri bildirim üretimi.
    - templates/utils/feedback_templates/default.txt dosyasını kullanır.
    - rubric: {'içerik': 40, 'biçim': 20, 'özgünlük': 40} gibi dağılım.
    """
    rubric = rubric or {'İçerik': 40, 'Biçim': 20, 'Özgünlük': 40}
    # Derlem konteksti
    ctx = {
        'student_name': getattr(student, 'full_name', ''),
        'course_code': assignment.group.course.code,
        'course_name': assignment.group.course.name,
        'assignment_title': assignment.title,
        'due_date': assignment.due_date,
        'rubric': rubric,
    }
    # Şablon yolu
    try:
        from django.template.loader import render_to_string
        text = render_to_string('utils/feedback_templates/default.txt', ctx)
        return text.strip()
    except Exception:
        # Fallback düz metin
        lines = [
            f"{ctx['student_name']} için geri bildirim - {ctx['course_code']} {ctx['course_name']}",
            f"Ödev: {ctx['assignment_title']}",
            "",
            "Güçlü Yönler: Konu hakimiyeti ve örneklerle destekleme başarılı.",
            "Geliştirilecek Alanlar: Biçimlendirme, kaynakça ve görsel destek artırılabilir.",
            "Öneriler: Rubriğe göre eksik kalan kısımlara odaklanın.",
        ]
        return "\n".join(lines)


# --------- PLAGIARISM CHECK ---------
def _shingles(text: str, n: int = 5) -> set:
    s = re.sub(r"\s+", " ", (text or '').lower()).strip()
    return set(s[i:i+n] for i in range(max(0, len(s) - n + 1)))


def check_plagiarism(submission_text: str, corpus: List[str]) -> Dict[str, Any]:
    """Basit benzerlik ölçümleri: Jaccard(shingles) ve difflib ratio.
    Döner: {'max_similarity': float, 'items': [{'jaccard': x, 'ratio': y, 'index': i}]}
    """
    if not submission_text or not corpus:
        return {'max_similarity': 0.0, 'items': []}
    sub_sh = _shingles(submission_text)
    results = []
    max_sim = 0.0
    for idx, doc in enumerate(corpus):
        doc_sh = _shingles(doc)
        inter = len(sub_sh & doc_sh)
        union = len(sub_sh | doc_sh) or 1
        jacc = inter / union
        ratio = difflib.SequenceMatcher(None, submission_text, doc).ratio()
        sim = max(jacc, ratio)
        max_sim = max(max_sim, sim)
        results.append({'index': idx, 'jaccard': round(jacc, 4), 'ratio': round(ratio, 4)})
    return {'max_similarity': round(max_sim, 4), 'items': results}


# --------- FILE TEXT EXTRACTION (PDF/DOCX/TXT) ---------
def extract_text_from_upload(file_field) -> str:
    """Extract text from uploaded file robustly (PDF, DOCX, TXT fallback).
    - Tries PyPDF2 first for PDFs; if empty, tries pdfminer.six if available.
    - For DOCX, uses python-docx.
    - Otherwise attempts utf-8/latin-1 decode.
    """
    if not file_field or not hasattr(file_field, 'name'):
        return ''
    name = (file_field.name or '').lower()
    try:
        if name.endswith('.pdf'):
            # Try PyPDF2
            try:
                with file_field.open('rb') as f:
                    text = _extract_text_from_pdf(f)
                if text and text.strip():
                    return text
            except Exception:
                pass
            # Try pdfminer.six
            try:
                from pdfminer.high_level import extract_text as pdfminer_extract
                with file_field.open('rb') as f:
                    data = f.read()
                from io import BytesIO
                return pdfminer_extract(BytesIO(data)) or ''
            except Exception:
                return ''
        elif name.endswith('.docx'):
            try:
                from docx import Document
                with file_field.open('rb') as f:
                    data = f.read()
                from io import BytesIO
                doc = Document(BytesIO(data))
                return "\n".join([p.text or '' for p in doc.paragraphs])
            except Exception:
                return ''
        else:
            # Plain text or others
            try:
                with file_field.open('rb') as f:
                    raw = f.read()
                try:
                    return raw.decode('utf-8', errors='ignore')
                except Exception:
                    return raw.decode('latin-1', errors='ignore')
            except Exception:
                return ''
    except Exception:
        return ''