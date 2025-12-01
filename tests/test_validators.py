"""Tests for the validators module."""

import pandas as pd
import pytest

from validators import validate_client_matter_code, validate_dataframe_codes


class TestValidateClientMatterCode:
    """Tests for validate_client_matter_code function."""
    
    def test_valid_codes(self):
        """Test valid ClientMatterCode formats."""
        # Test basic valid format
        result = validate_client_matter_code("12345.67890")
        assert result == (True, None)
        
        # Test with different valid numbers
        result = validate_client_matter_code("11111.22222")
        assert result == (True, None)
        
        # Test with zeros
        result = validate_client_matter_code("00000.00000")
        assert result == (True, None)
        
        # Test with leading/trailing whitespace
        result = validate_client_matter_code("  12345.67890  ")
        assert result == (True, None)
    
    def test_empty_values(self):
        """Test empty or None values."""
        # Test None
        result = validate_client_matter_code(None)
        assert result == (False, "Client matter code is empty")
        
        # Test pandas NA
        result = validate_client_matter_code(pd.NA)
        assert result == (False, "Client matter code is empty")
    
    def test_empty_strings(self):
        """Test empty strings (these fall through to format validation)."""
        # Test empty string
        result = validate_client_matter_code("")
        assert result == (False, "Invalid format - missing period")
        
        # Test whitespace only
        result = validate_client_matter_code("   ")
        assert result == (False, "Invalid format - missing period")
    
    def test_truncation_detection(self):
        """Test detection of possible truncation."""
        # Test second part too short (1-4 digits)
        result = validate_client_matter_code("12345.1")
        assert result == (False, "Possible truncation - second part too short")
        
        result = validate_client_matter_code("12345.1234")
        assert result == (False, "Possible truncation - second part too short")
        
        # Test first part too short (1-4 digits)
        result = validate_client_matter_code("1.67890")
        assert result == (False, "Possible truncation - first part too short")
        
        result = validate_client_matter_code("1234.67890")
        assert result == (False, "Possible truncation - first part too short")
    
    def test_missing_period(self):
        """Test codes missing the required period."""
        result = validate_client_matter_code("1234567890")
        assert result == (False, "Invalid format - missing period")
        
        result = validate_client_matter_code("abcdefghij")
        assert result == (False, "Invalid format - missing period")
    
    def test_invalid_formats(self):
        """Test various invalid formats."""
        # Too many periods
        result = validate_client_matter_code("123.456.789")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        # Letters instead of numbers
        result = validate_client_matter_code("abcde.fghij")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        # Mixed letters and numbers
        result = validate_client_matter_code("12a45.67890")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        # Special characters
        result = validate_client_matter_code("12345.678@0")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        # Too long
        result = validate_client_matter_code("123456.678901")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        # Period at start/end
        result = validate_client_matter_code(".12345")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
        
        result = validate_client_matter_code("12345.")
        assert result == (False, "Invalid format - expected XXXXX.XXXXX")
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Test with integer input (should be converted to string)
        result = validate_client_matter_code(1234567890)
        assert result == (False, "Invalid format - missing period")
        
        # Test with float - Python converts to string with potential precision issues
        result = validate_client_matter_code(12345.67890)
        # Float precision might cause this to be treated as truncated
        assert result[0] == False  # Just check it's invalid, message may vary


class TestValidateDataframeCodes:
    """Tests for validate_dataframe_codes function."""
    
    def test_valid_dataframe(self):
        """Test validation on DataFrame with valid codes."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222", "00000.99999"],
            "Other": ["a", "b", "c"]
        })
        
        errors = validate_dataframe_codes(df, "ClientMatterCode")
        assert errors == []
    
    def test_missing_column(self):
        """Test error when column doesn't exist."""
        df = pd.DataFrame({
            "WrongColumn": ["12345.67890"],
            "Other": ["a"]
        })
        
        with pytest.raises(ValueError, match="Column 'ClientMatterCode' not found"):
            validate_dataframe_codes(df, "ClientMatterCode")
    
    def test_mixed_valid_invalid_codes(self):
        """Test DataFrame with mix of valid and invalid codes."""
        df = pd.DataFrame({
            "ClientMatterCode": [
                "12345.67890",  # valid
                "12345.1",      # truncated second part
                "1234.67890",   # truncated first part  
                None,           # empty
                "1234567890",   # missing period
                "33333.44444",  # valid
            ],
            "Other": ["a", "b", "c", "d", "e", "f"]
        })
        
        errors = validate_dataframe_codes(df, "ClientMatterCode")
        
        # Should return 4 errors (rows 2, 3, 4, 5 in display - remember +2 offset)
        assert len(errors) == 4
        
        # Check specific errors
        error_rows = [error["row"] for error in errors]
        assert error_rows == [3, 4, 5, 6]  # 1-based row numbers + header
        
        # Check error messages
        assert errors[0]["error"] == "Possible truncation - second part too short"
        assert errors[1]["error"] == "Possible truncation - first part too short"
        assert errors[2]["error"] == "Client matter code is empty"
        assert errors[3]["error"] == "Invalid format - missing period"
        
        # Check values are preserved
        assert errors[0]["value"] == "12345.1"
        assert errors[1]["value"] == "1234.67890"
        assert pd.isna(errors[2]["value"]) or errors[2]["value"] is None
        assert errors[3]["value"] == "1234567890"
    
    def test_empty_dataframe(self):
        """Test validation on empty DataFrame."""
        df = pd.DataFrame({"ClientMatterCode": []})
        
        errors = validate_dataframe_codes(df, "ClientMatterCode")
        assert errors == []
    
    def test_all_invalid_codes(self):
        """Test DataFrame where all codes are invalid."""
        df = pd.DataFrame({
            "ClientMatterCode": [
                "invalid",
                "",
                "12345",
                "abcde.fghij"
            ]
        })
        
        errors = validate_dataframe_codes(df, "ClientMatterCode")
        
        # All 4 rows should have errors
        assert len(errors) == 4
        
        # Check all rows are reported (2, 3, 4, 5 in display)
        error_rows = [error["row"] for error in errors]
        assert error_rows == [2, 3, 4, 5]


class TestRegexPatterns:
    """Test the regex patterns work correctly."""
    
    def test_main_pattern(self):
        """Test the main validation pattern."""
        from validators import pattern
        
        # Should match valid codes
        assert pattern.match("12345.67890") is not None
        assert pattern.match("00000.00000") is not None
        
        # Should not match invalid codes
        assert pattern.match("1234.67890") is None  # too short first part
        assert pattern.match("12345.6789") is None  # too short second part
        assert pattern.match("123456.67890") is None  # too long first part
        assert pattern.match("12345.678901") is None  # too long second part
    
    def test_truncation_patterns(self):
        """Test the truncation detection patterns."""
        from validators import sec_part_too_short, first_part_too_short
        
        # Second part too short pattern
        assert sec_part_too_short.match("12345.1") is not None
        assert sec_part_too_short.match("12345.1234") is not None
        assert sec_part_too_short.match("12345.12345") is None  # correct length
        
        # First part too short pattern  
        assert first_part_too_short.match("1.67890") is not None
        assert first_part_too_short.match("1234.67890") is not None
        assert first_part_too_short.match("12345.67890") is None  # correct length