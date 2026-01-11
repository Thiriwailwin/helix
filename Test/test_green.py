import re

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