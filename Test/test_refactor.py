
import csv
import tempfile
import re

class ClinicalDataValidator:
    """Refactored validator class"""
    
    @staticmethod
    def is_valid_filename(filename):
        pattern = r'^CLINICALDATA_\d{14}\.CSV$'
        return re.match(pattern, filename, re.IGNORECASE) is not None
    
    @staticmethod
    def is_valid_dosage(dosage):
        try:
            return int(dosage) > 0
        except ValueError:
            return False

def test_refactored_validator():
    """REFACTOR: Test the clean validator class"""
    validator = ClinicalDataValidator()
    
    # Test valid cases
    assert validator.is_valid_filename("CLINICALDATA_20240101120000.CSV")
    assert validator.is_valid_dosage("100")
    
    # Test invalid cases
    assert not validator.is_valid_filename("wrong.csv")
    assert not validator.is_valid_dosage("-10")
    assert not validator.is_valid_dosage("abc")

def test_dosage_validation_green():
    """GREEN: Fix the dosage test"""
    dosage = "100"
    
    # Correct assertion
    assert int(dosage) > 0


    
