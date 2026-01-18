# test_error_logging_automation.py

import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime

class SimpleErrorLogger:
    """Simple error logging class for automation"""
    
    def __init__(self, log_directory):
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "errors.log"
        # Create the file immediately
        self.log_file.touch()
    
    def log_error(self, error_type, message):
        """Automatically log an error"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} | {error_type} | {message}\n")
        
        return True

class TestErrorLoggingAutomation(unittest.TestCase):
    """Automated testing for error logging system - SIMPLIFIED"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.logger = SimpleErrorLogger(Path(self.test_dir) / "logs")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_1_error_log_file_creation(self):
        """Test 1: Error log file is created automatically"""
        # Check if log file exists after logger initialization
        self.assertTrue(self.logger.log_file.exists(), 
                       "Error log file should be created automatically")
        self.assertTrue(os.path.getsize(self.logger.log_file) >= 0,
                       "Log file should exist (can be empty)")
    
    def test_2_error_logging_basic(self):
        """Test 2: Basic error logging works"""
        # Log an error
        result = self.logger.log_error(
            error_type="VALIDATION_ERROR",
            message="Invalid CSV header"
        )
        
        self.assertTrue(result, "Error logging should succeed")
        
        # Check file has content
        with open(self.logger.log_file, 'r') as f:
            content = f.read()
        
        self.assertIn("VALIDATION_ERROR", content, 
                     "Error type should be in log")
        self.assertIn("Invalid CSV header", content, 
                     "Error message should be in log")
    
    def test_3_multiple_errors_logging(self):
        """Test 3: Multiple errors can be logged"""
        errors = [
            ("FORMAT_ERROR", "Invalid date format"),
            ("FILE_ERROR", "File not found"),
            ("DATA_ERROR", "Missing required field")
        ]
        
        # Log all errors
        for error_type, message in errors:
            self.logger.log_error(error_type, message)
        
        # Count lines in log file
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3, 
                        "Should have 3 error entries in log")
    
    def test_4_error_log_format(self):
        """Test 4: Error log has correct format"""
        # Log a test error
        self.logger.log_error("TEST_ERROR", "Test message")
        
        # Read last line
        with open(self.logger.log_file, 'r') as f:
            lines = f.readlines()
            last_line = lines[-1].strip()
        
        # Check format: timestamp | error_type | message
        parts = last_line.split(" | ")
        self.assertEqual(len(parts), 3, 
                        "Log line should have 3 parts: timestamp | type | message")
        
        # Check parts
        timestamp, error_type, message = parts
        self.assertEqual(error_type, "TEST_ERROR", 
                        "Error type should match")
        self.assertEqual(message, "Test message", 
                        "Error message should match")

def run_tests():
    """Run all tests"""
    print("Running Error Logging Tests...")
    print("=" * 40)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestErrorLoggingAutomation)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)