"""
Gradebook Service Layer
Business logic for grade calculations
"""
from django.db import transaction
from django.db.models import Sum, Avg, Count, Q
from decimal import Decimal

from .models import GradeCategory, GradeItem, Grade
from apps.courses.models import Enrollment, CourseGroup
from apps.students.models import Student


class GradebookService:
    """Service for gradebook operations"""
    
    def calculate_student_course_grade(self, student, course_group):
        """
        Calculate student's total grade in a course
        Returns: {'total': Decimal, 'breakdown': dict, 'letter_grade': str}
        """
        # Get all grades for this student in this course
        grades = Grade.objects.filter(
            student=student,
            item__category__course_group=course_group,
            is_excused=False
        ).select_related('item', 'item__category')

        # If there is no entered score at all, don't show 0/FF
        has_any_score = grades.filter(score__isnull=False).exists()
        
        total_score = Decimal('0')
        breakdown = {}
        
        # Group by category
        categories = GradeCategory.objects.filter(
            course_group=course_group,
            is_active=True
        ).prefetch_related('items__grades')

        # If Bütünleme has a score, ignore Final category (makeup replaces final)
        has_makeup = False
        but_cat = categories.filter(name__iexact='Bütünleme').first()
        if but_cat:
            has_makeup = grades.filter(item__category=but_cat, score__isnull=False).exists()
        
        for category in categories:
            if has_makeup and category.name.lower() == 'final':
                continue
            category_items = category.items.filter(
                status__in=['published', 'graded'],
                is_extra_credit=False
            )
            
            if not category_items.exists():
                continue
            
            # Calculate category score
            category_total = Decimal('0')
            for item in category_items:
                grade = grades.filter(item=item).first()
                if grade and grade.score is not None:
                    # Weighted score in category - ensure all values are Decimal
                    score = Decimal(str(grade.score))
                    max_score = Decimal(str(item.max_score))
                    weight_in_category = Decimal(str(item.weight_in_category))
                    
                    item_percentage = (score / max_score) * Decimal('100')
                    weighted = item_percentage * (weight_in_category / Decimal('100'))
                    category_total += weighted
            
            # Apply category weight to course
            category_contribution = category_total * (category.weight / 100)
            total_score += category_contribution
            
            breakdown[category.name] = {
                'score': float(category_total),
                'weight': float(category.weight),
                'contribution': float(category_contribution)
            }
        
        # Add extra credit
        extra_items = GradeItem.objects.filter(
            category__course_group=course_group,
            is_extra_credit=True,
            status__in=['published', 'graded']
        )
        
        extra_credit = Decimal('0')
        for item in extra_items:
            grade = grades.filter(item=item).first()
            if grade and grade.score is not None:
                score = Decimal(str(grade.score))
                max_score = Decimal(str(item.max_score))
                item_percentage = (score / max_score) * Decimal('100')
                extra_credit += item_percentage
        
        total_score += extra_credit
        
        # Cap at 100
        if total_score > 100:
            total_score = Decimal('100')
        
        letter_grade = self._calculate_letter_grade(float(total_score)) if has_any_score else None
        
        return {
            'total': float(total_score) if has_any_score else None,
            'breakdown': breakdown if has_any_score else {},
            'extra_credit': float(extra_credit),
            'letter_grade': letter_grade
        }
    
    def _calculate_letter_grade(self, score):
        """
        Convert numeric score to letter grade
        Based on Selçuk University official grading system
        
        DOĞRU TABLO:
        88-100: AA (4.00) - Mükemmel
        80-87:  BA (3.50) - Çok İyi
        73-79:  BB (3.00) - İyi
        66-72:  CB (2.50) - Orta
        60-65:  CC (2.00) - Yeterli
        55-59:  DC (1.50) - Şartlı Geçer
        50-54:  DD (1.00) - Şartlı Geçer
        0-49:   FF (0.00) - Başarısız
        """
        if score >= 88:
            return 'AA'  # Mükemmel (4.00)
        elif score >= 80:
            return 'BA'  # Çok İyi (3.50)
        elif score >= 73:
            return 'BB'  # İyi (3.00)
        elif score >= 66:
            return 'CB'  # Orta (2.50)
        elif score >= 60:
            return 'CC'  # Yeterli (2.00)
        elif score >= 55:
            return 'DC'  # Şartlı Geçer (1.50)
        elif score >= 50:
            return 'DD'  # Şartlı Geçer (1.00)
        else:
            return 'FF'  # Başarısız (0.00)
    
    @transaction.atomic
    def update_enrollment_grades(self, enrollment):
        """Update Enrollment model with calculated grades"""
        result = self.calculate_student_course_grade(
            enrollment.student,
            enrollment.group
        )
        
        # Update the grade field (not final_grade)
        enrollment.grade = result['letter_grade']
        enrollment.save()
        
        return result
    
    def get_course_grade_statistics(self, course_group):
        """Get grade statistics for a course"""
        enrollments = Enrollment.objects.filter(
            group=course_group,
            status='enrolled'
        )
        
        stats = {
            'total_students': enrollments.count(),
            'graded': 0,
            'average': 0,
            'grade_distribution': {},
            'category_averages': {}
        }
        
        graded_count = 0
        total_sum = Decimal('0')
        
        for enrollment in enrollments:
            result = self.calculate_student_course_grade(
                enrollment.student,
                course_group
            )
            
            if result['total'] is not None and result['total'] > 0:
                graded_count += 1
                total_sum += Decimal(str(result['total']))
                
                # Count by letter grade
                letter = result['letter_grade']
                if letter:
                    stats['grade_distribution'][letter] = stats['grade_distribution'].get(letter, 0) + 1
        
        stats['graded'] = graded_count
        if graded_count > 0:
            stats['average'] = float(total_sum / graded_count)
        
        return stats
    
    def get_student_transcript(self, student):
        """Get student's complete transcript"""
        enrollments = Enrollment.objects.filter(
            student=student,
            status__in=['enrolled', 'completed']
        ).select_related('group__course', 'group__academic_term').order_by('-group__academic_term__start_date')
        
        transcript = []
        total_credits = 0
        total_points = 0
        
        grade_points = {
            'AA': 4.0, 'BA': 3.5, 'BB': 3.0, 'CB': 2.5,
            'CC': 2.0, 'DC': 1.5, 'DD': 1.0, 'FD': 0.5, 'FF': 0.0
        }
        
        for enrollment in enrollments:
            result = self.calculate_student_course_grade(
                student,
                enrollment.group
            )
            
            # Get individual exam scores
            vize_score = None
            final_score = None
            resit_score = None
            
            try:
                vize_item = GradeItem.objects.filter(
                    category__course_group=enrollment.group,
                    name='Vize Sınavı'
                ).first()
                if vize_item:
                    vize_grade = Grade.objects.filter(student=student, item=vize_item).first()
                    if vize_grade:
                        vize_score = vize_grade.score
                
                final_item = GradeItem.objects.filter(
                    category__course_group=enrollment.group,
                    name='Final Sınavı'
                ).first()
                if final_item:
                    final_grade = Grade.objects.filter(student=student, item=final_item).first()
                    if final_grade:
                        final_score = final_grade.score
                
                resit_item = GradeItem.objects.filter(
                    category__course_group=enrollment.group,
                    name='Bütünleme Sınavı'
                ).first()
                if resit_item:
                    resit_grade = Grade.objects.filter(student=student, item=resit_item).first()
                    if resit_grade:
                        resit_score = resit_grade.score
            except:
                pass
            
            credits = enrollment.group.course.credits
            letter = result['letter_grade']
            points = grade_points.get(letter, 0.0)
            
            transcript.append({
                'course': enrollment.group.course,
                'group': enrollment.group,
                'term': enrollment.group.academic_term,
                'score': result['total'],
                'letter_grade': letter,
                'credits': credits,
                'grade_points': points,
                'status': enrollment.status,
                'midterm_score': vize_score,
                'final_score': final_score,
                'resit_score': resit_score
            })
            
            if letter != 'FF':  # Only count passing grades
                total_credits += credits
                total_points += points * credits
        
        gpa = (total_points / total_credits) if total_credits > 0 else 0.0
        
        return {
            'transcript': transcript,
            'total_credits': total_credits,
            'gpa': round(gpa, 2),
            'total_courses': len(transcript)
        }
    
    @transaction.atomic
    def bulk_grade_entry(self, item_id, grade_data):
        """
        Bulk grade entry for multiple students
        grade_data: [{'student_id': 1, 'score': 85}, ...]
        Returns: {'success': int, 'failed': int, 'errors': []}
        """
        try:
            item = GradeItem.objects.get(id=item_id)
        except GradeItem.DoesNotExist:
            return {
                'success': 0,
                'failed': 0,
                'errors': ['GradeItem bulunamadı']
            }
        
        success_count = 0
        failed_count = 0
        errors = []
        
        for data in grade_data:
            try:
                student = Student.objects.get(id=data['student_id'])
                
                grade, created = Grade.objects.update_or_create(
                    student=student,
                    item=item,
                    defaults={
                        'score': data['score'],
                        'feedback': data.get('feedback', '')
                    }
                )
                success_count += 1
            except Student.DoesNotExist:
                failed_count += 1
                errors.append(f"Student ID {data['student_id']} not found")
            except Exception as e:
                failed_count += 1
                errors.append(f"Error for student {data.get('student_id')}: {str(e)}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'errors': errors
        }
