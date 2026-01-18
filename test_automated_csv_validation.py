import unittest
import os
import tempfile
import csv
from pathlib import Path

class TestCSVValidationAutomation(unittest.TestCase):
    """Automated testing for CSV validation system"""
    
    def setUp(self):
        """Set up test environment with temporary directories"""
        self.test_dir = tempfile.mkdtemp()
        self.valid_data_dir = Path(self.test_dir) / "valid_data"
        self.invalid_data_dir = Path(self.test_dir) / "invalid_data"
        
        self.valid_data_dir.mkdir(parents=True, exist_ok=True)
        self.invalid_data_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_positive_csv_validation(self):
        """Test with valid CSV files (Positive testing)"""
        # Create valid CSV file
        valid_file = self.valid_data_dir / "positive_test.csv"
        
        header = ["ID", "Name", "Value"]
        data = [
            ["001", "Test Data 1", "100"],
            ["002", "Test Data 2", "200"]
        ]
        
        with open(valid_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(data)
        
        # Validate file existence and content
        self.assertTrue(valid_file.exists(), "Valid CSV file should be created")
        
        # Read back and verify content
        with open(valid_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("ID,Name,Value", content, "Header should be present")
            self.assertIn("001,Test Data 1,100", content, "Data row 1 should be present")
            self.assertIn("002,Test Data 2,200", content, "Data row 2 should be present")
    
    def test_negative_csv_validation(self):
        """Test with invalid CSV files (Negative testing)"""
        # Create invalid CSV file
        invalid_file = self.invalid_data_dir / "negative_test.csv"
        
        # Missing header
        data = [
            ["001", "Test Data 1"],
            ["002", "Test Data 2"]
        ]
        
        with open(invalid_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data)
        
        # File should exist but be invalid
        self.assertTrue(invalid_file.exists(), "Invalid CSV file should be created")
        
        # Verify it's actually invalid by checking content
        with open(invalid_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Without header, first line should be data
            self.assertNotIn("ID,Name,Value", lines[0], "Header should be missing")
            self.assertIn("001,Test Data 1", lines[0], "First data row should be present")
    
    def test_csv_file_format_validation(self):
        """Test CSV file format requirements"""
        test_file = self.valid_data_dir / "format_test.csv"
        
        # Test .csv extension validation
        self.assertTrue(str(test_file).endswith('.csv'), 
                       "File should have .csv extension")
        
        # Test file naming convention
        valid_filename = "DATA_20240101_001.csv"
        invalid_filename = "data.txt"
        
        self.assertTrue(valid_filename.endswith('.csv'), 
                       "Valid filename should end with .csv")
        self.assertFalse(invalid_filename.endswith('.csv'), 
                        "Invalid filename should not be recognized as CSV")
    
    def test_automated_test_suite_execution(self):
        """Test that the automated test suite runs completely"""
        test_files = [
            self.valid_data_dir / "test1.csv",
            self.valid_data_dir / "test2.csv",
            self.invalid_data_dir / "error1.csv"
        ]
        
        # Create multiple test files
        for i, file_path in enumerate(test_files):
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([f"Header{i}"])
                writer.writerow([f"Data{i}"])
        
        # Verify all test files were created
        created_files = list(self.valid_data_dir.glob("*.csv")) + \
                       list(self.invalid_data_dir.glob("*.csv"))
        
        self.assertEqual(len(created_files), 3, 
                        "All three test files should be created")

if __name__ == '__main__':
    # Run automated tests
    unittest.main(verbosity=2)