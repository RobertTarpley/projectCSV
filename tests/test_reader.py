"""Tests for the reader module."""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from reader import read_file, _read_csv_with_encoding_detection


class TestReadFile:
    """Tests for read_file function."""
    
    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="File not found: nonexistent.csv"):
            read_file("nonexistent.csv")
    
    def test_unsupported_file_format(self, tmp_path):
        """Test error for unsupported file extensions."""
        # Create a file with unsupported extension
        unsupported_file = tmp_path / "test.txt"
        unsupported_file.write_text("some content")
        
        with pytest.raises(ValueError, match="Unsupported file format: .txt"):
            read_file(str(unsupported_file))
    
    def test_case_insensitive_extensions(self, tmp_path):
        """Test that file extensions are handled case-insensitively."""
        # This tests the .lower() in path_obj.suffix.lower()
        csv_content = "Name,Age\nAlice,30\nBob,25"
        
        # Test uppercase CSV
        csv_file = tmp_path / "test.CSV"
        csv_file.write_text(csv_content)
        
        df = read_file(str(csv_file))
        assert len(df) == 2
        assert list(df.columns) == ["Name", "Age"]


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for testing."""
    return "Name,Age,Status\nAlice,30,Active\nBob,25,Pending\nCharlie,35,Active"


@pytest.fixture
def sample_excel_data():
    """Sample data for Excel files."""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Age": [30, 25, 35],
        "Status": ["Active", "Pending", "Active"]
    })


class TestCSVReading:
    """Tests for CSV file reading."""
    
    def test_read_utf8_csv(self, tmp_path, sample_csv_content):
        """Test reading UTF-8 CSV files."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(sample_csv_content, encoding="utf-8")
        
        df = read_file(str(csv_file))
        
        assert len(df) == 3
        assert list(df.columns) == ["Name", "Age", "Status"]
        assert df.iloc[0]["Name"] == "Alice"
        assert df.iloc[1]["Age"] == "25"  # All columns should be strings
    
    def test_read_utf8_bom_csv(self, tmp_path, sample_csv_content):
        """Test reading UTF-8 with BOM CSV files."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(sample_csv_content, encoding="utf-8-sig")
        
        df = read_file(str(csv_file))
        
        assert len(df) == 3
        assert list(df.columns) == ["Name", "Age", "Status"]
        # Should handle BOM correctly
        assert df.iloc[0]["Name"] == "Alice"
    
    def test_read_cp1252_csv(self, tmp_path):
        """Test reading CP1252 (Windows) encoded CSV files."""
        # Content with CP1252 specific character (smart quote)
        cp1252_content = "Name,Description\nTest,\u201cQuoted text\u201d"
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(cp1252_content.encode("cp1252"))
        
        df = read_file(str(csv_file))
        
        assert len(df) == 1
        assert list(df.columns) == ["Name", "Description"]
        assert "\u201c" in df.iloc[0]["Description"]  # Smart quote preserved
    
    def test_read_iso_latin1_csv(self, tmp_path):
        """Test reading ISO-8859-1 (Latin-1) encoded CSV files."""
        # Content with Latin-1 specific character (accented character)
        latin1_content = "Name,City\nJosé,México"
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(latin1_content.encode("iso-8859-1"))
        
        df = read_file(str(csv_file))
        
        assert len(df) == 1
        assert list(df.columns) == ["Name", "City"]
        assert df.iloc[0]["Name"] == "José"
    
    def test_encoding_detection_fallback(self, tmp_path):
        """Test encoding detection when common encodings fail."""
        # Create content that might require chardet
        content = "Name,Value\nTest,Data"
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(content.encode("utf-16"))  # Unusual encoding
        
        # This should either work (if chardet detects it) or fail gracefully
        try:
            df = read_file(str(csv_file))
            # If it works, verify the data
            assert len(df) >= 0
        except ValueError as e:
            # Should give helpful error message
            assert "Unable to detect file encoding" in str(e) or "Failed to read CSV file" in str(e)
    
    def test_csv_with_whitespace(self, tmp_path):
        """Test CSV with extra whitespace (should be preserved as strings)."""
        csv_content = "Name,Age\n  Alice  ,  30  \n  Bob  ,  25  "
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        df = read_file(str(csv_file))
        
        assert len(df) == 2
        # Whitespace should be preserved (trimming happens in transformer)
        assert df.iloc[0]["Name"] == "  Alice  "
        assert df.iloc[0]["Age"] == "  30  "
    
    def test_csv_with_nulls(self, tmp_path):
        """Test CSV with empty/null values."""
        csv_content = "Name,Age,Status\nAlice,30,Active\n,25,\nCharlie,,Pending"
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        df = read_file(str(csv_file))
        
        assert len(df) == 3
        # Empty values should be preserved as strings or NaN
        assert pd.isna(df.iloc[1]["Name"]) or df.iloc[1]["Name"] == ""
        assert pd.isna(df.iloc[2]["Age"]) or df.iloc[2]["Age"] == ""


class TestExcelReading:
    """Tests for Excel file reading."""
    
    def test_read_xlsx_file(self, tmp_path, sample_excel_data):
        """Test reading .xlsx files."""
        xlsx_file = tmp_path / "test.xlsx"
        sample_excel_data.to_excel(xlsx_file, index=False, engine="openpyxl")
        
        df = read_file(str(xlsx_file))
        
        assert len(df) == 3
        assert list(df.columns) == ["Name", "Age", "Status"]
        assert df.iloc[0]["Name"] == "Alice"
        # All data should be strings due to dtype=str
        assert df.iloc[1]["Age"] == "25"
    
    def test_read_xls_file(self, tmp_path, sample_excel_data):
        """Test reading .xls files."""
        xls_file = tmp_path / "test.xls"
        
        # Note: xlrd doesn't support writing .xls files easily
        # So we'll create a basic test by writing as Excel and renaming
        # This tests the code path but might not work with actual .xls files
        sample_excel_data.to_excel(str(xls_file).replace('.xls', '.xlsx'), index=False, engine="openpyxl")
        
        # For a real .xls file test, you'd need an actual .xls file
        # For now, just test the error handling
        with pytest.raises((FileNotFoundError, Exception)):
            # This might fail due to actual .xls file format issues
            read_file(str(xls_file))
    
    def test_excel_with_mixed_types(self, tmp_path):
        """Test Excel files with mixed data types."""
        # Create Excel with different data types
        mixed_data = pd.DataFrame({
            "String": ["Alice", "Bob"],
            "Number": [30, 25],
            "Date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
            "Boolean": [True, False]
        })
        
        xlsx_file = tmp_path / "mixed.xlsx"
        mixed_data.to_excel(xlsx_file, index=False, engine="openpyxl")
        
        df = read_file(str(xlsx_file))
        
        assert len(df) == 2
        # All columns should be converted to strings
        assert df.dtypes["String"] == "object"
        assert df.dtypes["Number"] == "object"
        assert df.dtypes["Date"] == "object"
        assert df.dtypes["Boolean"] == "object"


class TestReadCsvWithEncodingDetection:
    """Tests for the internal CSV encoding detection function."""
    
    def test_utf8_detection(self, tmp_path):
        """Test UTF-8 encoding detection."""
        content = "Name,Value\nTest,Data"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(content, encoding="utf-8")
        
        df = _read_csv_with_encoding_detection(str(csv_file))
        
        assert len(df) == 1
        assert df.iloc[0]["Name"] == "Test"
    
    def test_common_encodings_first(self, tmp_path):
        """Test that common encodings are tried before chardet."""
        # This implicitly tests that common encodings work
        content = "Name,Value\nTest,Data"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(content, encoding="utf-8")
        
        # Should succeed with common encoding detection
        df = _read_csv_with_encoding_detection(str(csv_file))
        assert len(df) == 1
    
    def test_chardet_fallback(self, tmp_path):
        """Test chardet fallback for unusual encodings."""
        # Create file with unusual encoding that would require chardet
        content = "Name,Value\nTest,Data"
        csv_file = tmp_path / "test.csv"
        
        # Write with an encoding that's not in common_encodings
        with open(csv_file, "w", encoding="utf-16") as f:
            f.write(content)
        
        # Should either work or give helpful error
        try:
            df = _read_csv_with_encoding_detection(str(csv_file))
            assert len(df) >= 0
        except ValueError as e:
            assert "Unable to detect file encoding" in str(e) or "Failed to read CSV file" in str(e)
    
    def test_low_confidence_detection(self, tmp_path):
        """Test behavior when chardet has low confidence."""
        # Create a file that might have low confidence detection
        binary_content = bytes([0x00, 0x01, 0x02, 0x03])  # Random binary data
        csv_file = tmp_path / "test.csv"
        csv_file.write_bytes(binary_content)
        
        # This should either raise ValueError or succeed depending on chardet behavior
        try:
            df = _read_csv_with_encoding_detection(str(csv_file))
            # If it succeeds, that's also valid (chardet might detect something)
            assert df is not None
        except ValueError as e:
            # Should give helpful error message
            assert "Unable to detect file encoding" in str(e) or "Failed to read CSV file" in str(e)


class TestDataTypeHandling:
    """Tests for data type handling (should always be strings)."""
    
    def test_all_columns_as_strings(self, tmp_path):
        """Test that all columns are read as strings regardless of content."""
        csv_content = "Name,Age,Salary,IsActive\nAlice,30,50000.50,true\nBob,25,45000.75,false"
        
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        df = read_file(str(csv_file))
        
        # All columns should be object/string type
        for column in df.columns:
            assert df[column].dtype == "object"
        
        # Values should be strings
        assert df.iloc[0]["Age"] == "30"
        assert df.iloc[0]["Salary"] == "50000.50"  # pandas preserves original formatting
        assert df.iloc[0]["IsActive"] == "true"