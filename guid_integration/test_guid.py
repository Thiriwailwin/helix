# test_guid.py
import pytest
from helix import ClinicalDataValidator
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import uuid

class TestGUIDGeneration:
    """Test GUID generation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
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
    
    @patch('helix.requests.get')
    def test_generate_guid_api_success(self, mock_get):
        """Test successful API GUID generation"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["api-generated-uuid-1234"]
        mock_get.return_value = mock_response
        
        guid = self.validator._generate_guid()
        
        # Verify API was called
        mock_get.assert_called_once_with(
            "https://www.uuidtools.com/api/generate/v4",
            timeout=5
        )
        
        # Verify returned GUID
        assert guid == "api-generated-uuid-1234"
    
    @patch('helix.requests.get')
    def test_generate_guid_api_failure_fallback(self, mock_get):
        """Test fallback to local UUID when API fails"""
        # Mock API failure (timeout)
        mock_get.side_effect = Exception("API failed")
        
        # Mock uuid.uuid4 to return predictable value
        with patch('helix.uuid.uuid4') as mock_uuid:
            test_uuid = uuid.UUID('12345678-1234-1234-1234-123456789012')
            mock_uuid.return_value = test_uuid
            
            guid = self.validator._generate_guid()
        
        # Should use fallback UUID
        assert guid == str(test_uuid)
        # API should have been called (and failed)
        assert mock_get.called
    
    @patch('helix.requests.get')
    def test_generate_guid_api_timeout_retry(self, mock_get):
        """Test retry logic on timeout"""
        from requests.exceptions import Timeout
        
        # First call times out, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["retry-success-uuid"]
        
        mock_get.side_effect = [Timeout("Timeout"), mock_response]
        
        guid = self.validator._generate_guid()
        
        # Should retry and succeed
        assert mock_get.call_count == 2
        assert guid == "retry-success-uuid"
    
    def test_log_api_failure(self):
        """Test API failure logging"""
        error_message = "Test API failure"
        
        # Call the method
        self.validator._log_api_failure(error_message)
        
        # Check log file was created
        log_path = self.error_dir / "api_failures.log"
        assert log_path.exists()
        
        # Check log content
        with open(log_path, 'r') as f:
            content = f.read()
            assert "API Failure" in content
            assert error_message in content
    
  
