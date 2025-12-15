"""
Tests for Academic Term functionality
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from .models import AcademicTerm
from .services import AcademicTermService


class AcademicTermModelTest(TestCase):
    """Test AcademicTerm model"""
    
    def setUp(self):
        """Set up test data"""
        self.term_data = {
            'name': '2024-2025 Güz',
            'year_start': 2024,
            'year_end': 2025,
            'term_type': 'fall',
            'start_date': date(2024, 9, 16),
            'end_date': date(2025, 1, 31),
            'registration_start': date(2024, 9, 1),
            'registration_end': date(2024, 9, 15),
            'status': 'planned'
        }
    
    def test_create_academic_term(self):
        """Test creating an academic term"""
        term = AcademicTerm.objects.create(**self.term_data)
        
        self.assertEqual(term.name, '2024-2025 Güz')
        self.assertEqual(term.term_type, 'fall')
        self.assertEqual(term.status, 'planned')
        self.assertFalse(term.is_active)
    
    def test_auto_generate_name(self):
        """Test auto-generation of term name"""
        term = AcademicTerm.objects.create(
            year_start=2024,
            year_end=2025,
            term_type='spring',
            start_date=date(2025, 2, 1),
            end_date=date(2025, 6, 30)
        )
        
        self.assertEqual(term.name, '2024-2025 Bahar')
    
    def test_unique_together_constraint(self):
        """Test unique_together for year and term_type"""
        AcademicTerm.objects.create(**self.term_data)
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            AcademicTerm.objects.create(**self.term_data)
    
    def test_only_one_active_term(self):
        """Test that only one term can be active at a time"""
        term1 = AcademicTerm.objects.create(**self.term_data)
        term1.is_active = True
        term1.save()
        
        # Create second term and activate it
        term2_data = self.term_data.copy()
        term2_data['name'] = '2024-2025 Bahar'
        term2_data['term_type'] = 'spring'
        term2_data['start_date'] = date(2025, 2, 1)
        term2_data['end_date'] = date(2025, 6, 30)
        
        term2 = AcademicTerm.objects.create(**term2_data)
        term2.is_active = True
        term2.save()
        
        # Refresh term1 from database
        term1.refresh_from_db()
        
        # term1 should no longer be active
        self.assertFalse(term1.is_active)
        self.assertTrue(term2.is_active)
    
    def test_date_validation(self):
        """Test date validation"""
        invalid_data = self.term_data.copy()
        invalid_data['end_date'] = date(2024, 8, 1)  # Before start_date
        
        term = AcademicTerm(**invalid_data)
        with self.assertRaises(ValidationError):
            term.full_clean()
    
    def test_year_validation_fall_spring(self):
        """Test year validation for fall/spring terms"""
        invalid_data = self.term_data.copy()
        invalid_data['year_end'] = 2024  # Should be 2025
        
        term = AcademicTerm(**invalid_data)
        with self.assertRaises(ValidationError):
            term.full_clean()
    
    def test_is_registration_open(self):
        """Test registration open property"""
        # Set registration period to current date
        today = timezone.now().date()
        term_data = self.term_data.copy()
        term_data['start_date'] = today - timedelta(days=10)
        term_data['end_date'] = today + timedelta(days=90)
        term_data['registration_start'] = today - timedelta(days=5)
        term_data['registration_end'] = today + timedelta(days=5)
        
        term = AcademicTerm.objects.create(**term_data)
        self.assertTrue(term.is_registration_open)
    
    def test_is_current(self):
        """Test is_current property"""
        # Set term dates around current date
        today = timezone.now().date()
        term_data = self.term_data.copy()
        term_data['start_date'] = today - timedelta(days=30)
        term_data['end_date'] = today + timedelta(days=30)
        
        term = AcademicTerm.objects.create(**term_data)
        self.assertTrue(term.is_current)
    
    def test_get_active_term(self):
        """Test getting active term"""
        term = AcademicTerm.objects.create(**self.term_data)
        term.activate()
        
        active_term = AcademicTerm.get_active_term()
        self.assertEqual(active_term.id, term.id)
    
    def test_activate_method(self):
        """Test activate method"""
        term = AcademicTerm.objects.create(**self.term_data)
        term.activate()
        
        term.refresh_from_db()
        self.assertTrue(term.is_active)
        self.assertEqual(term.status, 'active')
    
    def test_complete_method(self):
        """Test complete method"""
        term = AcademicTerm.objects.create(**self.term_data)
        term.activate()
        term.complete()
        
        term.refresh_from_db()
        self.assertFalse(term.is_active)
        self.assertEqual(term.status, 'completed')


class AcademicTermServiceTest(TestCase):
    """Test AcademicTermService"""
    
    def setUp(self):
        """Set up test data"""
        self.service = AcademicTermService()
        self.term = AcademicTerm.objects.create(
            name='2024-2025 Güz',
            year_start=2024,
            year_end=2025,
            term_type='fall',
            start_date=date(2024, 9, 16),
            end_date=date(2025, 1, 31)
        )
    
    def test_get_active_term(self):
        """Test getting active term via service"""
        self.term.activate()
        
        active_term = self.service.get_active_term()
        self.assertEqual(active_term.id, self.term.id)
    
    def test_activate_term(self):
        """Test activating term via service"""
        result = self.service.activate_term(self.term.id)
        
        self.assertTrue(result['success'])
        self.term.refresh_from_db()
        self.assertTrue(self.term.is_active)
    
    def test_complete_term(self):
        """Test completing term via service"""
        self.term.activate()
        result = self.service.complete_term(self.term.id)
        
        self.assertTrue(result['success'])
        self.term.refresh_from_db()
        self.assertEqual(self.term.status, 'completed')
    
    def test_archive_term(self):
        """Test archiving term via service"""
        result = self.service.archive_term(self.term.id)
        
        self.assertTrue(result['success'])
        self.term.refresh_from_db()
        self.assertEqual(self.term.status, 'archived')
    
    def test_cannot_archive_active_term(self):
        """Test that active term cannot be archived"""
        self.term.activate()
        result = self.service.archive_term(self.term.id)
        
        self.assertFalse(result['success'])
        self.assertIn('Aktif dönem', result['error'])
