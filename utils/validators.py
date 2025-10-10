"""
Custom validators for the application
"""
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

def validate_tc_no(value):
    """Validate Turkish ID number"""
    if not value.isdigit() or len(value) != 11:
        raise ValidationError('TC kimlik numarası 11 haneli olmalıdır.')
    
    # TC kimlik numarası algoritması
    digits = [int(d) for d in value]
    
    # İlk 10 hanenin toplamı
    sum_first_10 = sum(digits[:10])
    if sum_first_10 % 10 != digits[10]:
        raise ValidationError('Geçersiz TC kimlik numarası.')
    
    # 1,3,5,7,9. hanelerin toplamının 7 katı ile 2,4,6,8,10. hanelerin toplamının farkı
    odd_sum = sum(digits[i] for i in range(0, 9, 2))
    even_sum = sum(digits[i] for i in range(1, 8, 2))
    
    if (odd_sum * 7 - even_sum) % 10 != digits[9]:
        raise ValidationError('Geçersiz TC kimlik numarası.')

def validate_phone_number(value):
    """Validate Turkish phone number"""
    phone_regex = RegexValidator(
        regex=r'^(\+90|0)?[5][0-9]{9}$',
        message='Geçerli bir telefon numarası giriniz. Örnek: 05551234567'
    )
    phone_regex(value)

def validate_school_number(value):
    """Validate school number format"""
    if not re.match(r'^\d{8,12}$', value):
        raise ValidationError('Okul numarası 8-12 haneli olmalıdır.')

def validate_course_code(value):
    """Validate course code format"""
    if not re.match(r'^[A-Z]{2,4}\d{3}$', value):
        raise ValidationError('Ders kodu formatı: ABC123 (2-4 harf + 3 rakam)')

def validate_grade_score(value):
    """Validate grade score (0-100)"""
    if not (0 <= value <= 100):
        raise ValidationError('Not 0-100 arasında olmalıdır.')

def validate_credits(value):
    """Validate course credits (1-10)"""
    if not (1 <= value <= 10):
        raise ValidationError('Kredi sayısı 1-10 arasında olmalıdır.')

def validate_capacity(value):
    """Validate course capacity"""
    if value < 1:
        raise ValidationError('Kapasite en az 1 olmalıdır.')
    if value > 500:
        raise ValidationError('Kapasite en fazla 500 olabilir.')

def validate_file_extension(value):
    """Validate uploaded file extensions"""
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
    ext = value.name.lower().split('.')[-1]
    if f'.{ext}' not in allowed_extensions:
        raise ValidationError(f'Desteklenen dosya formatları: {", ".join(allowed_extensions)}')

def validate_file_size(value):
    """Validate uploaded file size (max 10MB)"""
    max_size = 10 * 1024 * 1024  # 10MB
    if value.size > max_size:
        raise ValidationError('Dosya boyutu en fazla 10MB olabilir.')

def validate_semester_format(value):
    """Validate semester format (YYYY-Season)"""
    if not re.match(r'^\d{4}-(Fall|Spring|Summer)$', value):
        raise ValidationError('Dönem formatı: YYYY-Fall/Spring/Summer (örn: 2024-Fall)')

def validate_classroom_format(value):
    """Validate classroom format"""
    if not re.match(r'^[A-Z]\d{3}$', value):
        raise ValidationError('Sınıf formatı: A123 (1 harf + 3 rakam)')

def validate_schedule_format(value):
    """Validate schedule format"""
    days = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
    pattern = r'^(' + '|'.join(days) + r') \d{2}:\d{2}-\d{2}:\d{2}$'
    if not re.match(pattern, value):
        raise ValidationError('Program formatı: Pazartesi 09:00-12:00')