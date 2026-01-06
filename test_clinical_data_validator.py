import pytest
import tempfile
import os
from pathlib import Path
import csv

# We'll need to import the validator class from your main code
# This will be mocked or we'll refactor to make it testable

class TestClinicalDataValidator:
    """Test suite for ClinicalDataValidator class"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.test_dir = tempfile.mkdtemp()
        self.download_dir = Path(self.test_dir) / "downloads"
        self.archive_dir = Path(self.test_dir) / "archive"
        self.error_dir = Path(self.test_dir) / "errors"
        
        # Create directories
        self.download_dir.mkdir(parents=True)
        self.archive_dir.mkdir(parents=True)
        self.error_dir.mkdir(parents=True)
    
    def teardown_method(self):
        """Cleanup after each test"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_validate_filename_pattern_valid(self):
        """Test 1: RED PHASE - This test will FAIL initially
        Testing that a valid filename pattern passes validation"""
        # Arrange
        from helix import ClinicalDataValidator  
        validator = ClinicalDataValidator(
            str(self.download_dir),
            str(self.archive_dir),
            str(self.error_dir)
        )
        
        valid_filename = "CLINICALDATA_20240101120000.CSV"
        
        # Act
        result = validator._validate_filename_pattern(valid_filename)
        
        # Assert - This will FAIL initially (Red phase)
        assert result is True, "Valid filename should pass validation"
    
    def test_validate_filename_pattern_invalid(self):
        """Test 2: RED PHASE - This test will FAIL initially
        Testing that an invalid filename pattern fails validation"""
        # Arrange
        from helix_soft import ClinicalDataValidator  # Import from your main file
        validator = ClinicalDataValidator(
            str(self.download_dir),
            str(self.archive_dir),
            str(self.error_dir)
        )
        
        invalid_filename = "WRONGFORMAT_20240101.CSV"
        
        # Act
        result = validator._validate_filename_pattern(invalid_filename)
        
        # Assert - This will FAIL initially (Red phase)
        assert result is False, "Invalid filename should fail validation"
    
    def test_csv_validation_with_correct_header(self):
        """Test 3: Test CSV header validation"""
        # Arrange
        from helix_soft import ClinicalDataValidator
        validator = ClinicalDataValidator(
            str(self.download_dir),
            str(self.archive_dir),
            str(self.error_dir)
        )
        
        # Create a test CSV file with correct header
        test_file = self.download_dir / "test.csv"
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["PatientID", "TrialCode", "DrugCode", "Dosage_mg", 
                           "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"])
            writer.writerow(["P001", "T001", "D001", "100", 
                           "2024-01-01", "2024-01-10", "Improved", "None", "Dr. Smith"])
        
        # Act
        is_valid, errors, record_count = validator._validate_csv_content(str(test_file))
        
        # Assert - This should pass
        assert is_valid is True, "CSV with correct header should be valid"
        assert len(errors) == 0, "There should be no errors"
        assert record_count == 1, "Should count 1 valid record"