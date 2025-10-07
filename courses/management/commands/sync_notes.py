from django.core.management.base import BaseCommand
from notes.models import Note
from courses.models import Enrollment
from students.models import Student

class Command(BaseCommand):
    help = 'Note modelindeki notları Enrollment modeline aktarır'

    def handle(self, *args, **options):
        self.stdout.write('Notları senkronize ediliyor...')
        
        notes = Note.objects.all()
        updated_count = 0
        
        for note in notes:
            try:
                # Note'taki User'dan Student'ı bul
                try:
                    student = Student.objects.get(user=note.student)
                except Student.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'✗ Student bulunamadı: {note.student.get_full_name()} - {note.course.code}'
                        )
                    )
                    continue
                
                # Bu öğrencinin bu dersteki enrollment'ını bul
                enrollment = Enrollment.objects.filter(
                    student=student,
                    group__course=note.course
                ).first()
                
                if enrollment:
                    if note.exam_type == 'vize':
                        enrollment.midterm_grade = note.score
                    elif note.exam_type == 'final':
                        enrollment.final_grade = note.score
                    elif note.exam_type == 'but':
                        enrollment.makeup_grade = note.score
                    
                    enrollment.save()
                    updated_count += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {student.full_name} - {note.course.code} - {note.exam_type}: {note.score}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'✗ Enrollment bulunamadı: {student.full_name} - {note.course.code}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Hata: {note.student.get_full_name()} - {note.course.code}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Toplam {updated_count} not senkronize edildi.')
        )