"""
Reporting & Analytics Module
Student transcripts, teacher analytics, export functionality
"""
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from decimal import Decimal
import csv
from io.StringIO import StringIO

from .services import GradebookService
from apps.courses.models import CourseGroup, Enrollment
from apps.students.models import Student
from apps.teachers.models import Teacher


class TranscriptGenerator:
    """Generate student transcripts"""
    
    def __init__(self):
        self.gradebook_service = GradebookService()
    
    def generate_transcript(self, student):
        """Generate full academic transcript"""
        transcript_data = self.gradebook_service.get_student_transcript(student)
        
        # Group by academic term
        by_term = {}
        for item in transcript_data['transcript']:
            term = item['term']
            if term:
                term_key = term.name
                if term_key not in by_term:
                    by_term[term_key] = {
                        'term': term,
                        'courses': [],
                        'credits': 0,
                        'term_gpa': 0
                    }
                by_term[term_key]['courses'].append(item)
        
        # Calculate term GPAs
        grade_points_map = {
            'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
            'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FD': 0.5, 'FF': 0.0
        }
        
        for term_data in by_term.values():
            term_credits = 0
            term_points = 0
            
            for course in term_data['courses']:
                credits = course['credits']
                points = grade_points_map.get(course['letter_grade'], 0)
                
                term_credits += credits
                term_points += credits * points
            
            term_data['credits'] = term_credits
            term_data['term_gpa'] = round(term_points / term_credits, 2) if term_credits > 0 else 0.0
        
        return {
            'student': student,
            'by_term': by_term,
            'cumulative_gpa': transcript_data['gpa'],
            'total_credits': transcript_data['total_credits'],
            'total_courses': transcript_data['total_courses']
        }
    
    def export_transcript_pdf(self, student):
        """Export transcript as PDF (placeholder)"""
        # Requires reportlab or similar
        # Implementation would go here
        return "PDF generation requires additional library"
    
    def export_transcript_csv(self, student):
        """Export transcript as CSV"""
        transcript = self.generate_transcript(student)
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Öğrenci Transkripti'])
        writer.writerow([f"{student.first_name} {student.last_name}"])
        writer.writerow([f"Numara: {student.school_number}"])
        writer.writerow([f"Genel Ortalama: {transcript['cumulative_gpa']}"])
        writer.writerow([f"Toplam Kredi: {transcript['total_credits']}"])
        writer.writerow([])
        
        # Courses by term
        for term_key, term_data in transcript['by_term'].items():
            writer.writerow([f"Dönem: {term_key}"])
            writer.writerow(['Ders Kodu', 'Ders Adı', 'Kredi', 'Harf Notu', 'Puan'])
            
            for course in term_data['courses']:
                writer.writerow([
                    course['course'].code,
                    course['course'].name,
                    course['credits'],
                    course['letter_grade'],
                    course['score']
                ])
            
            writer.writerow(['Dönem Ortalaması:', '', '', '', term_data['term_gpa']])
            writer.writerow([])
        
        return output.getvalue()


class TeacherAnalytics:
    """Analytics dashboard for teachers"""
    
    def get_course_analytics(self, course_group):
        """Get comprehensive analytics for a course"""
        service = GradebookService()
        stats = service.get_course_grade_statistics(course_group)
        
        # Enrollment trends
        enrollments = Enrollment.objects.filter(group=course_group)
        enrollment_stats = {
            'total': enrollments.count(),
            'enrolled': enrollments.filter(status='enrolled').count(),
            'dropped': enrollments.filter(status='dropped').count(),
            'completed': enrollments.filter(status='completed').count()
        }
        
        # Assignment completion rates
        from apps.courses.models import Assignment
        assignments = Assignment.objects.filter(group=course_group)
        
        assignment_stats = []
        for assignment in assignments:
            submissions = assignment.submissions.count()
            total_students = enrollment_stats['enrolled']
            completion_rate = (submissions / total_students * 100) if total_students > 0 else 0
            
            assignment_stats.append({
                'assignment': assignment,
                'submissions': submissions,
                'completion_rate': round(completion_rate, 1)
            })
        
        # Attendance (if tracked)
        # Activity metrics
        
        return {
            'grade_stats': stats,
            'enrollment_stats': enrollment_stats,
            'assignment_stats': assignment_stats,
            'course_group': course_group
        }
    
    def get_teacher_summary(self, teacher):
        """Get summary of all teacher's courses"""
        course_groups = CourseGroup.objects.filter(teacher=teacher, status='active')
        
        summary = {
            'total_courses': course_groups.count(),
            'total_students': 0,
            'courses': []
        }
        
        for group in course_groups:
            enrollments = Enrollment.objects.filter(
                group=group,
                status='enrolled'
            ).count()
            
            summary['total_students'] += enrollments
            summary['courses'].append({
                'group': group,
                'students': enrollments
            })
        
        return summary


class ExportService:
    """Export data in various formats"""
    
    @staticmethod
    def export_gradebook_csv(course_group):
        """Export gradebook as CSV"""
        from apps.gradebook.models import GradeCategory, Grade
        
        service = GradebookService()
        enrollments = Enrollment.objects.filter(
            group=course_group,
            status='enrolled'
        ).select_related('student').order_by('student__first_name')
        
        categories = GradeCategory.objects.filter(
            course_group=course_group,
            is_active=True
        ).prefetch_related('items')
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        header = ['Öğrenci No', 'Ad', 'Soyad']
        for category in categories:
            for item in category.items.all():
                header.append(f"{item.name}")
        header.extend(['Toplam', 'Harf Notu'])
        writer.writerow(header)
        
        # Data rows
        for enrollment in enrollments:
            result = service.calculate_student_course_grade(
                enrollment.student,
                course_group
            )
            
            row = [
                enrollment.student.school_number,
                enrollment.student.first_name,
                enrollment.student.last_name
            ]
            
            # Grades for each item
            for category in categories:
                for item in category.items.all():
                    grade = Grade.objects.filter(
                        student=enrollment.student,
                        item=item
                    ).first()
                    row.append(grade.score if grade and grade.score else '-')
            
            row.append(f"{result['total']:.1f}")
            row.append(result['letter_grade'])
            
            writer.writerow(row)
        
        return output.getvalue()
    
    @staticmethod
    def export_enrollment_list_csv(course_group):
        """Export enrollment list as CSV"""
        enrollments = Enrollment.objects.filter(
            group=course_group,
            status='enrolled'
        ).select_related('student').order_by('student__school_number')
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([f"Ders: {course_group.course.name} ({course_group.course.code})"])
        writer.writerow([f"Grup: {course_group.name}"])
        writer.writerow([f"Öğretmen: {course_group.teacher.first_name} {course_group.teacher.last_name}"])
        writer.writerow([])
        
        writer.writerow(['No', 'Öğrenci No', 'Ad', 'Soyad', 'E-posta', 'Kayıt Tarihi'])
        
        for idx, enrollment in enumerate(enrollments, 1):
            writer.writerow([
                idx,
                enrollment.student.school_number,
                enrollment.student.first_name,
                enrollment.student.last_name,
                enrollment.student.email,
                enrollment.enrollment_date.strftime('%d.%m.%Y')
            ])
        
        return output.getvalue()
