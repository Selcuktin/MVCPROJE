"""
Custom template tags for note display
"""
from django import template
from apps.notes.models import Note

register = template.Library()


@register.simple_tag
def get_student_note(student, course, exam_type):
    """Get student's note for specific course and exam type"""
    try:
        # Student objesi ise user'ı al
        user = student.user if hasattr(student, 'user') else student
        
        note = Note.objects.filter(
            student=user,
            course=course,
            exam_type=exam_type
        ).first()
        return note
    except:
        return None


@register.simple_tag
def get_student_average(student, course):
    """Calculate student's average for a course"""
    try:
        # Student objesi ise user'ı al
        user = student.user if hasattr(student, 'user') else student
        
        vize = Note.objects.filter(student=user, course=course, exam_type='vize').first()
        final = Note.objects.filter(student=user, course=course, exam_type='final').first()
        but_note = Note.objects.filter(student=user, course=course, exam_type='but').first()
        
        if not vize or not final:
            return None
        
        vize_score = float(vize.score) if vize.score else 0
        final_score = float(final.score) if final.score else 0
        
        # Eğer büt varsa ve final'den yüksekse, final yerine büt kullan
        if but_note and but_note.score:
            but_score = float(but_note.score)
            if but_score > final_score:
                final_score = but_score
        
        # Ortalama: %40 vize + %60 final
        average = (vize_score * 0.4) + (final_score * 0.6)
        return round(average, 1)
    except:
        return None


@register.simple_tag
def get_student_letter_grade(student, course):
    """Get student's letter grade for a course"""
    average = get_student_average(student, course)
    
    if average is None:
        return None
    
    # Harf notu hesaplama (Fotoğraftaki tabloya göre)
    if average >= 88:
        return 'AA'
    elif average >= 80:
        return 'BA'
    elif average >= 73:
        return 'BB'
    elif average >= 66:
        return 'CB'
    elif average >= 60:
        return 'CC'
    elif average >= 50:
        return 'DC'
    else:
        return 'FF'
