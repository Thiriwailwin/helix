import pytest
from helix import ClinicalDataValidator
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch

class TestClinicalDataValidator:
    """Test the ClinicalDataValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary directories for testing
        self.temp_dir = tempfile.mkdtemp()
        self.download_dir = Path(self.temp_dir) / "Downloads"
        self.archive_dir = Path(self.temp_dir) / "Archive"
        self.error_dir = Path(self.temp_dir) / "Errors"
        
        # Create validator instance
        self.validator = ClinicalDataValidator(
            self.download_dir,
            self.archive_dir,
            self.error_dir
        )
    
    def teardown_method(self):
        """Clean up after tests"""
    
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_filename_validation_valid(self):
        """Test valid filename pattern"""
        valid_filenames = [
            "CLINICALDATA_20240101120000.CSV",
            "CLINICALDATA_20231225143000.csv",
            "CLINICALDATA_20240115123045.CSV"
        ]
        
        for filename in valid_filenames:
            result = self.validator._validate_filename_pattern(filename)
            assert result == True, f"Filename {filename} should be valid"
    
    def test_filename_validation_invalid(self):
        """Test invalid filename patterns"""
        invalid_filenames = [
            # "clinicaldata_20240101120000.csv",  
            "CLINICALDATA_20240101.CSV",  # wrong timestamp length
            "DATA_20240101120000.CSV",  # wrong prefix
            "CLINICALDATA_20240101120000.TXT",  # wrong extension
            "CLINICALDATA_2024-01-01-120000.CSV",  # wrong format
            "CLINICALDATA_20240101120000",  # no extension
            "20240101120000.CSV",  # no prefix
            "CLINICALDATA_.CSV",  # no timestamp
        ]
        
        for filename in invalid_filenames:
            result = self.validator._validate_filename_pattern(filename)
            assert result == False, f"Filename {filename} should be invalid"
    
    def test_create_valid_csv_file(self):
        """Create a valid CSV file for testing"""
        import csv
        
        # Create test CSV file
        test_file = self.download_dir / "test_valid.csv"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        header = ["PatientID", "TrialCode", "DrugCode", "Dosage_mg", 
                 "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"]
        
        data = [
            ["PT001", "TRIAL001", "DRUG001", "100", "2024-01-01", 
             "2024-06-01", "Improved", "None", "Analyst1"],
            ["PT002", "TRIAL001", "DRUG001", "150", "2024-01-02",
             "2024-06-02", "No Change", "Headache", "Analyst2"],
        ]
        
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
        
        # Store the file path as instance variable instead of returning
        self.test_file_path = test_file
    
    def test_csv_validation_valid(self):
        """Test validation of valid CSV content"""
        # First call the method that creates the file
        self.test_create_valid_csv_file()
        # use the stored file path
        test_file = self.test_file_path
        
        is_valid, errors, record_count = self.validator._validate_csv_content(
            test_file, 
            status_queue=None
        )
        
        assert is_valid == True, f"Valid CSV should pass validation. Errors: {errors}"
        assert record_count == 2, f"Should have 2 valid records, got {record_count}"
        assert len(errors) == 0, f"No errors expected, got: {errors}"
    
    def test_csv_validation_invalid_header(self):
        """Test CSV with invalid header"""
        import csv
        
        test_file = self.download_dir / "test_invalid_header.csv"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # Wrong header
        header = ["PatientID", "WrongField", "DrugCode", "Dosage_mg", 
                 "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"]
        
        with open(test_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
        
        is_valid, errors, record_count = self.validator._validate_csv_content(
            test_file, 
            status_queue=None
        )
        
        assert is_valid == False, "Invalid header should fail validation"
        assert "Invalid header" in str(errors)
    
    def test_processed_files_logging(self):
        """Test that processed files are logged correctly"""
        test_filename = "CLINICALDATA_20240101120000.CSV"
        
        # Initially not processed
        assert test_filename not in self.validator.processed_files
        
        # Mark as processed
        self.validator._save_processed_file(test_filename)
        
        # Should now be in processed files
        assert test_filename in self.validator.processed_files
        
        # Create new validator instance to test persistence
        validator2 = ClinicalDataValidator(
            self.download_dir,
            self.archive_dir,
            self.error_dir
        )
        
        # Should load previously processed files
        assert test_filename in validator2.processed_files