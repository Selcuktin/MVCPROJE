"""
Service Layer: Business logic and data processing operations.
Bu dosya ders işlemleri için business logic ve veri işleme operasyonlarını içerir.
"""
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import csv
from io import BytesIO, StringIO

from .models import Course, CourseGroup, Enrollment, Assignment, Submission, Announcement
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