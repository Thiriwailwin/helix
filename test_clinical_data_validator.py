import csv
import tempfile
import re

# ========== RED PHASE ==========
# First, write tests that FAIL

# def test_filename_validation_red():
#     """RED: Write a failing test for filename validation"""
#     # This test WILL FAIL on purpose
#     filename = "CLINICALDATA_20240101120000.CSV"
#     pattern = r'^CLINICALDATA_\d{14}\.CSV$'
    
#     # Wrong assertion on purpose
#     assert re.match(pattern, filename) is None  # This will FAIL

# def test_dosage_validation_red():
#     """RED: Write a failing test for dosage validation"""
#     dosage = "100"
    
#     # Wrong assertion on purpose  
#     assert int(dosage) < 0  # This will FAIL

# ========== GREEN PHASE ==========
# Now, fix the tests to make them PASS

def test_filename_validation_green():
    """GREEN: Fix the filename test"""
    filename = "CLINICALDATA_20240101120000.CSV"
    pattern = r'^CLINICALDATA_\d{14}\.CSV$'
    
    # Correct assertion
    assert re.match(pattern, filename, re.IGNORECASE) is not None

def test_dosage_validation_green():
    """GREEN: Fix the dosage test"""
    dosage = "100"
    
    # Correct assertion
    assert int(dosage) > 0

# # ========== REFACTOR PHASE ==========
# # Create clean, reusable functions

# class ClinicalDataValidator:
#     """Refactored validator class"""
    
#     @staticmethod
#     def is_valid_filename(filename):
#         pattern = r'^CLINICALDATA_\d{14}\.CSV$'
#         return re.match(pattern, filename, re.IGNORECASE) is not None
    
#     @staticmethod
#     def is_valid_dosage(dosage):
#         try:
#             return int(dosage) > 0
#         except ValueError:
#             return False

# def test_refactored_validator():
#     """REFACTOR: Test the clean validator class"""
#     validator = ClinicalDataValidator()
    
#     # Test valid cases
#     assert validator.is_valid_filename("CLINICALDATA_20240101120000.CSV")
#     assert validator.is_valid_dosage("100")
    
#     # Test invalid cases
#     assert not validator.is_valid_filename("wrong.csv")
#     assert not validator.is_valid_dosage("-10")
#     assert not validator.is_valid_dosage("abc")

# # ========== INTEGRATION TEST ==========
# # Test with actual CSV file

# def test_csv_validation():
#     """Test creating and reading a CSV file"""
#     # Create temp CSV file
#     with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
#         writer = csv.writer(f)
#         writer.writerow(["PatientID", "Dosage_mg"])
#         writer.writerow(["P001", "100"])
#         temp_path = f.name
    
#     # Read and validate
#     with open(temp_path, 'r') as f:
#         reader = csv.reader(f)
#         rows = list(reader)
        
#         assert len(rows) == 2
#         assert rows[0][0] == "PatientID"
#         assert rows[1][1] == "100"
    
#     # Clean up
#     import os
#     os.unlink(temp_path)

# # ========== RUN ALL TESTS ==========
# def run_tests():
#     print("Starting TDD tests...")
    
#     # RED phase (should fail)
#     print("\n1. RED PHASE - Writing failing tests...")
#     try:
#         test_filename_validation_red()
#         print("  ERROR: Should have failed!")
#     except AssertionError:
#         print("  PASS: Test failed as expected")
    
#     try:
#         test_dosage_validation_red()
#         print("  ERROR: Should have failed!")
#     except AssertionError:
#         print("  PASS: Test failed as expected")
    
#     # GREEN phase (should pass)
#     print("\n2. GREEN PHASE - Making tests pass...")
#     test_filename_validation_green()
#     test_dosage_validation_green()
#     print("  PASS: All green tests pass")
    
#     # REFACTOR phase
#     print("\n3. REFACTOR PHASE - Clean code...")
#     test_refactored_validator()
#     test_csv_validation()
#     print("  PASS: All refactored tests pass")
    
#     print("\nTDD cycle completed successfully!")

if __name__ == "__main__":
    run_tests()