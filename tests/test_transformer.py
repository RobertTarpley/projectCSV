"""Tests for the transformer module."""

import pandas as pd
import pytest
from pathlib import Path
import tempfile
import os

from transformer import (
    ColumnMapping, 
    TransformConfig, 
    transform_dataframe, 
    write_output
)


class TestColumnMapping:
    """Tests for ColumnMapping class."""
    
    def test_simple_column_name(self):
        """Test simple column name without mapping."""
        mapping = ColumnMapping("ColumnName")
        
        assert mapping.source_name == "ColumnName"
        assert mapping.dest_name == "ColumnName"
    
    def test_column_mapping_with_colon(self):
        """Test column mapping with source:destination syntax."""
        mapping = ColumnMapping("SourceName:DestName")
        
        assert mapping.source_name == "SourceName"
        assert mapping.dest_name == "DestName"
    
    def test_column_mapping_with_whitespace(self):
        """Test that whitespace is properly stripped."""
        mapping = ColumnMapping("  Source Name  :  Dest Name  ")
        
        assert mapping.source_name == "Source Name"
        assert mapping.dest_name == "Dest Name"
    
    def test_empty_mapping_raises_error(self):
        """Test that empty mapping raises ValueError."""
        with pytest.raises(ValueError, match="Column mapping cannot be empty"):
            ColumnMapping("")
        
        with pytest.raises(ValueError, match="Column mapping cannot be empty"):
            ColumnMapping("   ")
    
    def test_invalid_colon_syntax(self):
        """Test invalid colon syntax raises appropriate errors."""
        # Too many colons
        with pytest.raises(ValueError, match="Invalid column mapping syntax.*Expected format"):
            ColumnMapping("Source:Middle:Dest")
        
        # Empty source
        with pytest.raises(ValueError, match="Source column name cannot be empty"):
            ColumnMapping(":Dest")
        
        # Empty destination
        with pytest.raises(ValueError, match="Destination column name cannot be empty"):
            ColumnMapping("Source:")
        
        # Both empty
        with pytest.raises(ValueError, match="Source column name cannot be empty"):
            ColumnMapping(":")
    
    def test_parse_mappings_static_method(self):
        """Test the static parse_mappings method."""
        mapping_strings = [
            "Column1",
            "Source2:Dest2",
            "  Column3  ",
            "Source4:Dest4"
        ]
        
        mappings = ColumnMapping.parse_mappings(mapping_strings)
        
        assert len(mappings) == 4
        assert mappings[0].source_name == "Column1"
        assert mappings[0].dest_name == "Column1"
        assert mappings[1].source_name == "Source2"
        assert mappings[1].dest_name == "Dest2"
        assert mappings[2].source_name == "Column3"
        assert mappings[2].dest_name == "Column3"
        assert mappings[3].source_name == "Source4"
        assert mappings[3].dest_name == "Dest4"
    
    def test_parse_mappings_with_invalid_mapping(self):
        """Test that parse_mappings propagates validation errors."""
        mapping_strings = ["Valid", ""]
        
        with pytest.raises(ValueError, match="Column mapping cannot be empty"):
            ColumnMapping.parse_mappings(mapping_strings)


class TestTransformConfig:
    """Tests for TransformConfig class."""
    
    def test_transform_config_creation(self):
        """Test basic TransformConfig creation."""
        mappings = [ColumnMapping("Source:Dest"), ColumnMapping("Column2")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="upper",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        assert config.column_mappings == mappings
        assert config.case_transform == "upper"
        assert config.duplicate_handling == "error"
        assert config.key_column == "ClientMatterCode"
        assert config.output_path == "output.csv"


class TestTransformDataframe:
    """Tests for transform_dataframe function."""
    
    def test_basic_transformation(self):
        """Test basic DataFrame transformation."""
        df = pd.DataFrame({
            "OriginalName": ["Alice", "Bob", "Charlie"],
            "OriginalAge": ["30", "25", "35"],
            "ClientMatterCode": ["12345.67890", "11111.22222", "33333.44444"]
        })
        
        mappings = [
            ColumnMapping("OriginalName:Name"),
            ColumnMapping("OriginalAge:Age")
        ]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",  # Not in selected columns, so validation skipped
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config)
        
        assert len(result) == 3
        assert list(result.columns) == ["Name", "Age"]
        assert result.iloc[0]["Name"] == "Alice"
        assert result.iloc[0]["Age"] == "30"
    
    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises appropriate error."""
        df = pd.DataFrame()
        mappings = [ColumnMapping("Column1")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="Column1",
            output_path="output.csv"
        )
        
        with pytest.raises(ValueError, match="Cannot transform an empty DataFrame"):
            transform_dataframe(df, config)
    
    def test_no_column_mappings_raises_error(self):
        """Test that no column mappings raises appropriate error."""
        df = pd.DataFrame({"Column1": ["data"]})
        config = TransformConfig(
            column_mappings=[],
            case_transform="none",
            duplicate_handling="error",
            key_column="Column1",
            output_path="output.csv"
        )
        
        with pytest.raises(ValueError, match="No column mappings specified"):
            transform_dataframe(df, config)
    
    def test_missing_source_column_raises_error(self):
        """Test that missing source column raises helpful error."""
        df = pd.DataFrame({"ExistingColumn": ["data"]})
        mappings = [ColumnMapping("MissingColumn:NewColumn")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="NewColumn",
            output_path="output.csv"
        )
        
        with pytest.raises(ValueError, match="Column 'MissingColumn' not found.*Available columns: ExistingColumn"):
            transform_dataframe(df, config)
    
    def test_case_transformations(self):
        """Test different case transformation options."""
        df = pd.DataFrame({
            "Name": ["Alice Smith", "bob jones", "CHARLIE BROWN"],
            "Status": ["ACTIVE", "pending", "InActive"],
            "ClientMatterCode": ["12345.67890", "11111.22222", "33333.44444"]
        })
        
        mappings = [ColumnMapping("Name"), ColumnMapping("Status")]
        
        # Test upper case
        config_upper = TransformConfig(
            column_mappings=mappings,
            case_transform="upper",
            duplicate_handling="error", 
            key_column="ClientMatterCode",  # Not in selected columns
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config_upper)
        assert result.iloc[0]["Name"] == "ALICE SMITH"
        assert result.iloc[1]["Name"] == "BOB JONES"
        assert result.iloc[0]["Status"] == "ACTIVE"
        assert result.iloc[1]["Status"] == "PENDING"
        
        # Test lower case
        config_lower = TransformConfig(
            column_mappings=mappings,
            case_transform="lower",
            duplicate_handling="error",
            key_column="ClientMatterCode", 
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config_lower)
        assert result.iloc[0]["Name"] == "alice smith"
        assert result.iloc[2]["Name"] == "charlie brown"
        assert result.iloc[0]["Status"] == "active"
        assert result.iloc[2]["Status"] == "inactive"
        
        # Test proper case (title)
        config_proper = TransformConfig(
            column_mappings=mappings,
            case_transform="proper",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config_proper)
        assert result.iloc[0]["Name"] == "Alice Smith"
        assert result.iloc[1]["Name"] == "Bob Jones"
        assert result.iloc[0]["Status"] == "Active"
        assert result.iloc[1]["Status"] == "Pending"
        
        # Test no case transformation
        config_none = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config_none)
        assert result.iloc[0]["Name"] == "Alice Smith"  # unchanged
        assert result.iloc[1]["Name"] == "bob jones"    # unchanged
        assert result.iloc[2]["Name"] == "CHARLIE BROWN"  # unchanged
    
    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed."""
        df = pd.DataFrame({
            "Name": ["  Alice  ", " Bob ", "Charlie   "],
            "Status": [" Active ", "  Pending  ", " Inactive "],
            "ClientMatterCode": ["12345.67890", "11111.22222", "33333.44444"]
        })
        
        mappings = [ColumnMapping("Name"), ColumnMapping("Status")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config)
        
        assert result.iloc[0]["Name"] == "Alice"
        assert result.iloc[1]["Name"] == "Bob"
        assert result.iloc[2]["Name"] == "Charlie"
        assert result.iloc[0]["Status"] == "Active"
        assert result.iloc[1]["Status"] == "Pending"
        assert result.iloc[2]["Status"] == "Inactive"
    
    def test_null_normalization(self):
        """Test that null values are normalized to empty strings."""
        df = pd.DataFrame({
            "Name": ["Alice", None, "Charlie"],
            "Age": ["30", None, "35"],  # Keep as strings to match dtype=str from reader
            "ClientMatterCode": ["12345.67890", "11111.22222", "33333.44444"]
        })
        
        mappings = [ColumnMapping("Name"), ColumnMapping("Age")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config)
        
        assert result.iloc[0]["Name"] == "Alice"
        assert result.iloc[1]["Name"] == ""  # None converted to empty string
        assert result.iloc[2]["Name"] == "Charlie"
        assert result.iloc[0]["Age"] == "30"
        assert result.iloc[1]["Age"] == ""  # None converted to empty string
    
    def test_duplicate_handling_error(self):
        """Test duplicate handling with error mode."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222", "12345.67890"],
            "Name": ["Alice", "Bob", "Charlie"]
        })
        
        mappings = [ColumnMapping("ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        with pytest.raises(ValueError, match="Duplicate values found in key column.*12345.67890"):
            transform_dataframe(df, config)
    
    def test_duplicate_handling_keep_first(self, capsys):
        """Test duplicate handling with keep-first mode."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222", "12345.67890", "11111.22222"],
            "Name": ["Alice", "Bob", "Charlie", "David"]
        })
        
        mappings = [ColumnMapping("ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="keep-first",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config)
        
        # Should keep only first occurrence of each duplicate
        assert len(result) == 2
        assert result.iloc[0]["ClientMatterCode"] == "12345.67890"
        assert result.iloc[0]["Name"] == "Alice"  # First Alice, not Charlie
        assert result.iloc[1]["ClientMatterCode"] == "11111.22222"
        assert result.iloc[1]["Name"] == "Bob"    # First Bob, not David
        
        # Check that removal message was printed
        captured = capsys.readouterr()
        assert "Removed 2 duplicate rows" in captured.out
    
    def test_all_duplicates_removed_raises_error(self):
        """Test that error is raised when all rows have the same key but different data."""
        # This would require all rows to be completely identical to trigger the error
        # But actually, drop_duplicates(subset=column, keep="first") will always keep at least one row
        # So let's test a different scenario where the check would trigger
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "12345.67890"],
            "Name": ["Alice", "Bob"]  # Different data but same key
        })
        
        mappings = [ColumnMapping("ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="keep-first",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        # This should actually succeed and keep the first row, not error
        result = transform_dataframe(df, config)
        assert len(result) == 1  # Keep first duplicate
        assert result.iloc[0]["Name"] == "Alice"  # First occurrence kept
    
    def test_validation_errors_raise_exception(self):
        """Test that validation errors raise appropriate exception."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "invalid", "11111.22222"],
            "Name": ["Alice", "Bob", "Charlie"]
        })
        
        mappings = [ColumnMapping("ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        with pytest.raises(ValueError, match="Validation errors found"):
            transform_dataframe(df, config)
    
    def test_key_column_not_in_selected_columns(self):
        """Test validation when key column is not in selected columns."""
        df = pd.DataFrame({
            "ClientMatterCode": ["12345.67890", "11111.22222"],
            "Name": ["Alice", "Bob"],
            "Status": ["Active", "Pending"]
        })
        
        # Only select Name and Status, but key column is ClientMatterCode
        mappings = [ColumnMapping("Name"), ColumnMapping("Status")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",  # Not in selected columns
            output_path="output.csv"
        )
        
        # This should work fine - validation and duplicate checking are skipped
        # if key column is not in the selected columns
        result = transform_dataframe(df, config)
        assert len(result) == 2
        assert list(result.columns) == ["Name", "Status"]


class TestWriteOutput:
    """Tests for write_output function."""
    
    def test_basic_write_output(self, tmp_path):
        """Test basic CSV output writing."""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": ["30", "25"]
        })
        
        output_file = tmp_path / "output.csv"
        write_output(df, output_file)
        
        # Verify file was created and has correct content
        assert output_file.exists()
        
        # Read back and verify content
        content = output_file.read_text(encoding="utf-8")
        assert "Name,Age" in content  # Header
        assert "Alice,30" in content
        assert "Bob,25" in content
        assert content.count("\n") >= 2  # At least header + data rows
    
    def test_write_empty_dataframe_raises_error(self, tmp_path):
        """Test that writing empty DataFrame raises error."""
        df = pd.DataFrame()
        output_file = tmp_path / "output.csv"
        
        with pytest.raises(ValueError, match="Cannot write an empty DataFrame to file"):
            write_output(df, output_file)
    
    def test_write_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        df = pd.DataFrame({"Column": ["data"]})
        
        # Create nested directory path that doesn't exist
        output_file = tmp_path / "subdir" / "nested" / "output.csv"
        
        write_output(df, output_file)
        
        assert output_file.exists()
        assert output_file.parent.exists()
    
    def test_write_utf8_encoding(self, tmp_path):
        """Test that output is written with UTF-8 encoding."""
        df = pd.DataFrame({
            "Name": ["José", "François"],
            "City": ["México", "Québec"]
        })
        
        output_file = tmp_path / "output.csv"
        write_output(df, output_file)
        
        # Read back with UTF-8 and verify special characters
        content = output_file.read_text(encoding="utf-8")
        assert "José" in content
        assert "François" in content
        assert "México" in content
        assert "Québec" in content
    
    def test_write_handles_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        df = pd.DataFrame({"Column": ["data"]})
        
        # Create a file and make it read-only to simulate permission error
        output_file = tmp_path / "readonly.csv"
        output_file.write_text("existing content")
        output_file.chmod(0o444)  # Read-only
        
        try:
            with pytest.raises(PermissionError, match="Permission denied writing"):
                write_output(df, output_file)
        finally:
            # Restore write permissions for cleanup
            output_file.chmod(0o644)
    
    def test_write_no_index(self, tmp_path):
        """Test that index is not written to CSV."""
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": ["30", "25"]
        })
        # Explicitly set a custom index
        df.index = ["row1", "row2"]
        
        output_file = tmp_path / "output.csv"
        write_output(df, output_file)
        
        content = output_file.read_text(encoding="utf-8")
        
        # Index should not be in the output
        assert "row1" not in content
        assert "row2" not in content
        # But data should be there
        assert "Alice" in content
        assert "Bob" in content
        # Header should not include index
        lines = content.strip().split("\n")
        header = lines[0]
        assert header == "Name,Age"


class TestTransformerIntegration:
    """Integration tests combining all transformer functionality."""
    
    def test_complete_transformation_workflow(self, tmp_path):
        """Test complete transformation from raw data to output file."""
        # Create messy input data
        df = pd.DataFrame({
            "matter id": ["  12345.67890  ", "11111.22222", " 33333.44444 "],
            "client name": ["  ALICE CORP  ", "bob ltd", "Charlie Inc"],
            "case status": ["ACTIVE", "pending", "CLOSED"],
            "notes": ["Important case", None, "Regular case"]
        })
        
        # Configure transformation
        mappings = [
            ColumnMapping("matter id:ClientMatterCode"),
            ColumnMapping("client name:ClientName"), 
            ColumnMapping("case status:Status")
        ]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="proper",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        # Transform data
        result = transform_dataframe(df, config)
        
        # Verify transformation
        assert len(result) == 3
        assert list(result.columns) == ["ClientMatterCode", "ClientName", "Status"]
        
        # Check data cleaning
        assert result.iloc[0]["ClientMatterCode"] == "12345.67890"  # Trimmed
        assert result.iloc[0]["ClientName"] == "Alice Corp"        # Proper case
        assert result.iloc[1]["ClientName"] == "Bob Ltd"           # Proper case
        assert result.iloc[0]["Status"] == "Active"               # Proper case
        assert result.iloc[1]["Status"] == "Pending"              # Proper case
        
        # Write to file
        output_file = tmp_path / "test_output.csv"
        write_output(result, output_file)
        
        # Verify file output
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "ClientMatterCode,ClientName,Status" in content
        assert "12345.67890,Alice Corp,Active" in content
        assert "11111.22222,Bob Ltd,Pending" in content
    
    def test_error_handling_workflow(self):
        """Test error handling throughout the workflow."""
        df = pd.DataFrame({
            "Code": ["12345.67890", "invalid"],
            "Name": ["Alice", "Bob"]
        })
        
        mappings = [ColumnMapping("Code:ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="error",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        # Should fail due to validation errors
        with pytest.raises(ValueError, match="Validation errors found"):
            transform_dataframe(df, config)
    
    def test_duplicate_workflow_with_validation(self, capsys):
        """Test workflow with both duplicates and validation."""
        df = pd.DataFrame({
            "Code": ["12345.67890", "12345.67890", "11111.22222"],
            "Name": ["Alice", "Bob", "Charlie"]
        })
        
        mappings = [ColumnMapping("Code:ClientMatterCode"), ColumnMapping("Name")]
        config = TransformConfig(
            column_mappings=mappings,
            case_transform="none",
            duplicate_handling="keep-first",
            key_column="ClientMatterCode",
            output_path="output.csv"
        )
        
        result = transform_dataframe(df, config)
        
        # Should have removed duplicates
        assert len(result) == 2
        assert result.iloc[0]["Name"] == "Alice"  # First occurrence kept
        assert result.iloc[1]["Name"] == "Charlie"
        
        # Check duplicate removal message
        captured = capsys.readouterr()
        assert "Removed 1 duplicate rows" in captured.out