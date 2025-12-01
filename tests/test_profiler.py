"""Tests for the profiler module."""

import pandas as pd
import pytest
from io import StringIO
import sys

from profiler import profile_dataframe, format_profile_output


class TestProfileDataframe:
    """Tests for profile_dataframe function."""
    
    def test_basic_profiling(self):
        """Test basic DataFrame profiling."""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [30, 25, 35],
            "Status": ["Active", "Pending", "Active"]
        })
        
        profile = profile_dataframe(df)
        
        assert profile["total_rows"] == 3
        assert profile["total_columns"] == 3
        assert profile["duplicate_info"] is None
        assert profile["validation_errors"] is None
        
        # Check column stats
        assert len(profile["columns_stats"]) == 3
        
        # Find each column's stats
        name_stats = next(col for col in profile["columns_stats"] if col["name"] == "Name")
        age_stats = next(col for col in profile["columns_stats"] if col["name"] == "Age")
        status_stats = next(col for col in profile["columns_stats"] if col["name"] == "Status")
        
        assert name_stats["unique_values"] == 3
        assert name_stats["missing_values"] == 0
        
        assert age_stats["unique_values"] == 3
        assert age_stats["missing_values"] == 0
        
        assert status_stats["unique_values"] == 2  # "Active" appears twice
        assert status_stats["missing_values"] == 0
    
    def test_empty_dataframe(self):
        """Test profiling an empty DataFrame."""
        df = pd.DataFrame()
        
        profile = profile_dataframe(df)
        
        assert profile["total_rows"] == 0
        assert profile["total_columns"] == 0
        assert profile["columns_stats"] == []
        assert profile["duplicate_info"] is None
        assert profile["validation_errors"] is None
    
    def test_dataframe_with_nulls(self):
        """Test profiling DataFrame with missing values."""
        df = pd.DataFrame({
            "Name": ["Alice", None, "Charlie", ""],
            "Age": [30, None, 35, 25],
            "Status": ["Active", "Pending", None, "Active"]
        })
        
        profile = profile_dataframe(df)
        
        assert profile["total_rows"] == 4
        assert profile["total_columns"] == 3
        
        # Check missing values counting
        name_stats = next(col for col in profile["columns_stats"] if col["name"] == "Name")
        age_stats = next(col for col in profile["columns_stats"] if col["name"] == "Age")
        status_stats = next(col for col in profile["columns_stats"] if col["name"] == "Status")
        
        assert name_stats["missing_values"] == 1  # Only None counts as missing, not ""
        assert age_stats["missing_values"] == 1
        assert status_stats["missing_values"] == 1
    
    def test_dataframe_with_duplicates(self):
        """Test duplicate detection functionality."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222", "12345.67890", "33333.44444"],
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Status": ["Active", "Pending", "Active", "Active"]
        })
        
        profile = profile_dataframe(df, key_column="ClientMatterCode")
        
        assert profile["total_rows"] == 4
        assert profile["duplicate_info"] is not None
        
        dup_info = profile["duplicate_info"]
        assert dup_info["count"] == 1  # One duplicate (first occurrence not counted)
        assert dup_info["column"] == "ClientMatterCode"
        assert "12345.67890" in dup_info["values"]
        assert len(dup_info["values"]) == 1  # Only one unique duplicated value
    
    def test_no_duplicates(self):
        """Test when no duplicates are found."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222", "33333.44444"],
            "Name": ["Alice", "Bob", "Charlie"]
        })
        
        profile = profile_dataframe(df, key_column="ClientMatterCode")
        
        assert profile["duplicate_info"] is None
    
    def test_missing_key_column(self, capsys):
        """Test behavior when key column doesn't exist."""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": [30, 25]
        })
        
        profile = profile_dataframe(df, key_column="NonexistentColumn")
        
        # Check that error message was printed to stderr
        captured = capsys.readouterr()
        assert "Column 'NonexistentColumn' not found in DataFrame" in captured.err
        
        # Profile should still be generated without duplicate info
        assert profile["total_rows"] == 2
        assert profile["duplicate_info"] is None
        assert profile["validation_errors"] is None
    
    def test_validation_errors(self):
        """Test integration with validation errors."""
        df = pd.DataFrame({
            "ClientMatterCode": [
                "12345.67890",  # valid
                "12345.1",      # invalid - truncation
                "invalid",      # invalid - bad format
                "11111.22222"   # valid
            ],
            "Name": ["Alice", "Bob", "Charlie", "David"]
        })
        
        profile = profile_dataframe(df, key_column="ClientMatterCode")
        
        assert profile["validation_errors"] is not None
        assert len(profile["validation_errors"]) == 2  # Two invalid codes
        
        # Check that validation errors are properly formatted
        errors = profile["validation_errors"]
        assert errors[0]["row"] == 3  # Second row (0-indexed + header offset)
        assert errors[1]["row"] == 4  # Third row
    
    def test_mixed_data_types(self):
        """Test profiling with mixed data types."""
        df = pd.DataFrame({
            "String": ["Alice", "Bob"],
            "Integer": [30, 25],
            "Float": [30.5, 25.7],
            "Boolean": [True, False],
            "Date": pd.to_datetime(["2023-01-01", "2023-01-02"])
        })
        
        profile = profile_dataframe(df)
        
        assert profile["total_rows"] == 2
        assert profile["total_columns"] == 5
        
        # Check that all columns are accounted for
        column_names = [col["name"] for col in profile["columns_stats"]]
        assert set(column_names) == {"String", "Integer", "Float", "Boolean", "Date"}
        
        # Check that data types are captured
        for col_stat in profile["columns_stats"]:
            assert "type" in col_stat
            assert col_stat["type"] is not None


class TestFormatProfileOutput:
    """Tests for format_profile_output function."""
    
    def test_basic_format_output(self):
        """Test basic profile formatting."""
        profile = {
            "total_rows": 3,
            "total_columns": 2,
            "columns_stats": [
                {"name": "Name", "type": "object", "unique_values": 3, "missing_values": 0},
                {"name": "Age", "type": "int64", "unique_values": 3, "missing_values": 0}
            ],
            "duplicate_info": None,
            "validation_errors": None
        }
        
        output = format_profile_output(profile)
        
        assert "File Profile" in output
        assert "Rows: 3" in output
        assert "Columns: 2" in output
        assert "Column Statistics:" in output
        assert "Name: object" in output
        assert "Age: int64" in output
        assert "Unique Values: 3" in output
        assert "Missing Values: 0" in output
    
    def test_format_with_duplicates(self):
        """Test formatting when duplicates are found."""
        profile = {
            "total_rows": 4,
            "total_columns": 2,
            "columns_stats": [
                {"name": "Code", "type": "object", "unique_values": 3, "missing_values": 0},
                {"name": "Name", "type": "object", "unique_values": 4, "missing_values": 0}
            ],
            "duplicate_info": {
                "count": 1,
                "column": "Code", 
                "values": ["12345.67890"]
            },
            "validation_errors": None
        }
        
        output = format_profile_output(profile)
        
        assert "Duplicates found on Code:" in output
        assert "Count: 1" in output
        assert "Values: 12345.67890" in output
    
    def test_format_with_validation_errors(self):
        """Test formatting when validation errors are present."""
        profile = {
            "total_rows": 3,
            "total_columns": 2,
            "columns_stats": [
                {"name": "Code", "type": "object", "unique_values": 3, "missing_values": 0}
            ],
            "duplicate_info": None,
            "validation_errors": [
                {"row": 2, "value": "invalid", "error": "Invalid format"},
                {"row": 3, "value": "12345.1", "error": "Possible truncation"}
            ]
        }
        
        output = format_profile_output(profile)
        
        assert "Validation Errors:" in output
        assert "Row 2: invalid - Invalid format" in output
        assert "Row 3: 12345.1 - Possible truncation" in output
    
    def test_format_with_empty_validation_errors(self):
        """Test formatting when validation errors list is empty."""
        profile = {
            "total_rows": 2,
            "total_columns": 1,
            "columns_stats": [
                {"name": "Code", "type": "object", "unique_values": 2, "missing_values": 0}
            ],
            "duplicate_info": None,
            "validation_errors": []  # Empty list
        }
        
        output = format_profile_output(profile)
        
        # Should not include validation errors section
        assert "Validation Errors:" not in output
    
    def test_format_complete_profile(self):
        """Test formatting a complete profile with all sections."""
        profile = {
            "total_rows": 5,
            "total_columns": 3,
            "columns_stats": [
                {"name": "Code", "type": "object", "unique_values": 4, "missing_values": 1},
                {"name": "Name", "type": "object", "unique_values": 5, "missing_values": 0},
                {"name": "Status", "type": "object", "unique_values": 2, "missing_values": 0}
            ],
            "duplicate_info": {
                "count": 1,
                "column": "Code",
                "values": ["12345.67890"]
            },
            "validation_errors": [
                {"row": 2, "value": "invalid", "error": "Bad format"}
            ]
        }
        
        output = format_profile_output(profile)
        
        # Check all sections are present
        assert "File Profile" in output
        assert "Rows: 5" in output
        assert "Columns: 3" in output
        assert "Column Statistics:" in output
        assert "Code: object" in output
        assert "Missing Values: 1" in output
        assert "Duplicates found on Code:" in output
        assert "Count: 1" in output
        assert "Validation Errors:" in output
        assert "Row 2: invalid - Bad format" in output
    
    def test_format_with_multiple_duplicate_values(self):
        """Test formatting when multiple different values are duplicated."""
        profile = {
            "total_rows": 6,
            "total_columns": 1,
            "columns_stats": [
                {"name": "Code", "type": "object", "unique_values": 4, "missing_values": 0}
            ],
            "duplicate_info": {
                "count": 2,
                "column": "Code",
                "values": ["12345.67890", "11111.22222"]  # Two different duplicated values
            },
            "validation_errors": None
        }
        
        output = format_profile_output(profile)
        
        assert "Duplicates found on Code:" in output
        assert "Count: 2" in output
        assert "Values: 12345.67890, 11111.22222" in output
    
    def test_format_column_types_preserved(self):
        """Test that column data types are properly formatted."""
        profile = {
            "total_rows": 2,
            "total_columns": 4,
            "columns_stats": [
                {"name": "String", "type": "object", "unique_values": 2, "missing_values": 0},
                {"name": "Integer", "type": "int64", "unique_values": 2, "missing_values": 0},
                {"name": "Float", "type": "float64", "unique_values": 2, "missing_values": 0},
                {"name": "Boolean", "type": "bool", "unique_values": 2, "missing_values": 0}
            ],
            "duplicate_info": None,
            "validation_errors": None
        }
        
        output = format_profile_output(profile)
        
        assert "String: object" in output
        assert "Integer: int64" in output  
        assert "Float: float64" in output
        assert "Boolean: bool" in output


class TestProfilerIntegration:
    """Integration tests combining profiling and formatting."""
    
    def test_end_to_end_profiling(self):
        """Test complete profiling workflow."""
        df = pd.DataFrame({
            "ClientMatterCode": [
                "12345.67890",  # valid
                "12345.67890",  # duplicate
                "11111.1",      # invalid
                "22222.33333"   # valid
            ],
            "Name": ["Alice", "Bob", "Charlie", "David"],
            "Age": [30, 25, None, 35]
        })
        
        # Profile the data
        profile = profile_dataframe(df, key_column="ClientMatterCode")
        
        # Format the output
        output = format_profile_output(profile)
        
        # Verify profile contains all expected information
        assert profile["total_rows"] == 4
        assert profile["duplicate_info"] is not None
        assert profile["validation_errors"] is not None
        assert len(profile["validation_errors"]) == 1  # One invalid code
        
        # Verify formatted output is comprehensive
        assert "File Profile" in output
        assert "Rows: 4" in output
        assert "Duplicates found" in output
        assert "Validation Errors:" in output
        assert "Missing Values: 1" in output  # Age has one missing value
    
    def test_profiling_with_no_key_column(self):
        """Test profiling without specifying a key column."""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob", "Alice"],  # Duplicate names, but no key column specified
            "Age": [30, 25, 30]
        })
        
        profile = profile_dataframe(df)  # No key_column specified
        output = format_profile_output(profile)
        
        assert profile["duplicate_info"] is None
        assert profile["validation_errors"] is None
        assert "Duplicates found" not in output
        assert "Validation Errors" not in output
        
        # But basic stats should still work
        assert profile["total_rows"] == 3
        assert "Rows: 3" in output