"""Integration tests for CLI commands."""

import pandas as pd
import pytest
from pathlib import Path
from click.testing import CliRunner
import tempfile
import os

from cli import cli


class TestCLIProfile:
    """Integration tests for the profile command."""
    
    def test_profile_basic_csv(self, tmp_path):
        """Test basic profiling of a CSV file."""
        # Create test CSV file
        csv_content = "Name,Age,Status\nAlice,30,Active\nBob,25,Pending\nCharlie,35,Active"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(csv_file)])
        
        assert result.exit_code == 0
        assert "File Profile" in result.output
        assert "Rows: 3" in result.output
        assert "Columns: 3" in result.output
        assert "Name: object" in result.output
        assert "Age: object" in result.output
        assert "Status: object" in result.output
    
    def test_profile_with_key_column(self, tmp_path):
        """Test profiling with key column specified."""
        # Create test CSV with valid ClientMatterCode
        csv_content = "ClientMatterCode,Name,Status\n12345.67890,Alice,Active\n11111.22222,Bob,Pending"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(csv_file), '--key', 'ClientMatterCode'])
        
        assert result.exit_code == 0
        assert "File Profile" in result.output
        assert "Rows: 2" in result.output
        # Should not have validation errors since codes are valid
        assert "Validation Errors" not in result.output
    
    def test_profile_with_validation_errors(self, tmp_path):
        """Test profiling that detects validation errors."""
        # Create test CSV with invalid ClientMatterCode
        csv_content = "ClientMatterCode,Name\n12345.67890,Alice\ninvalid,Bob\n12345.1,Charlie"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(csv_file), '--key', 'ClientMatterCode'])
        
        assert result.exit_code == 0
        assert "Validation Errors:" in result.output
        assert "Row 3: invalid" in result.output
        assert "Row 4: 12345.1" in result.output
    
    def test_profile_with_duplicates(self, tmp_path):
        """Test profiling that detects duplicates."""
        csv_content = "ClientMatterCode,Name\n12345.67890,Alice\n11111.22222,Bob\n12345.67890,Charlie"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(csv_file), '--key', 'ClientMatterCode'])
        
        assert result.exit_code == 0
        assert "Duplicates found on ClientMatterCode:" in result.output
        assert "Count: 1" in result.output
        assert "12345.67890" in result.output
    
    def test_profile_excel_file(self, tmp_path):
        """Test profiling an Excel file."""
        # Create test Excel file
        df = pd.DataFrame({
            "Name": ["Alice", "Bob"],
            "Age": [30, 25],
            "Status": ["Active", "Pending"]
        })
        xlsx_file = tmp_path / "test.xlsx"
        df.to_excel(xlsx_file, index=False, engine="openpyxl")
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(xlsx_file)])
        
        assert result.exit_code == 0
        assert "File Profile" in result.output
        assert "Rows: 2" in result.output
        assert "Columns: 3" in result.output
    
    def test_profile_nonexistent_file(self):
        """Test profiling a file that doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', 'nonexistent.csv'])
        
        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error:" in result.output
    
    def test_profile_missing_key_column(self, tmp_path):
        """Test profiling with key column that doesn't exist."""
        csv_content = "Name,Age\nAlice,30\nBob,25"
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(csv_content)
        
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', str(csv_file), '--key', 'NonexistentColumn'])
        
        assert result.exit_code == 0  # Should still succeed
        assert "Column 'NonexistentColumn' not found" in result.stderr
        assert "File Profile" in result.output


class TestCLITransform:
    """Integration tests for the transform command."""
    
    def test_basic_transform(self, tmp_path):
        """Test basic transformation workflow."""
        # Create input file
        csv_content = "OriginalName,OriginalAge,Status\nAlice,30,ACTIVE\nBob,25,PENDING"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'OriginalName:Name',
            '-c', 'OriginalAge:Age', 
            '--case', 'proper',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "Successfully wrote 2 rows" in result.output
        
        # Verify output file
        assert output_file.exists()
        output_df = pd.read_csv(output_file, dtype=str)  # Read as strings to match output format
        assert len(output_df) == 2
        assert list(output_df.columns) == ["Name", "Age"]
        assert output_df.iloc[0]["Name"] == "Alice"
        assert output_df.iloc[0]["Age"] == "30"
    
    def test_transform_with_case_conversion(self, tmp_path):
        """Test transformation with case conversion."""
        csv_content = "name,status\nalice smith,ACTIVE\nbob jones,PENDING"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'name:Name',
            '-c', 'status:Status',
            '--case', 'proper',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        
        output_df = pd.read_csv(output_file, dtype=str)
        assert output_df.iloc[0]["Name"] == "Alice Smith"
        assert output_df.iloc[0]["Status"] == "Active"
        assert output_df.iloc[1]["Name"] == "Bob Jones"
        assert output_df.iloc[1]["Status"] == "Pending"
    
    def test_transform_with_whitespace_trimming(self, tmp_path):
        """Test transformation trims whitespace."""
        csv_content = "name,age\n  Alice  ,  30  \n  Bob  ,  25  "
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'name:Name',
            '-c', 'age:Age',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        
        output_df = pd.read_csv(output_file, dtype=str)
        assert output_df.iloc[0]["Name"] == "Alice"  # Trimmed
        assert output_df.iloc[0]["Age"] == "30"      # Trimmed
    
    def test_transform_duplicate_handling_error(self, tmp_path):
        """Test transformation fails on duplicates when set to error."""
        csv_content = "ClientMatterCode,Name\n12345.67890,Alice\n12345.67890,Bob"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'ClientMatterCode',
            '-c', 'Name',
            '--duplicates', 'error',
            '--key', 'ClientMatterCode',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 1
        assert "Duplicate values found" in result.output
        assert not output_file.exists()  # Should not create output file on error
    
    def test_transform_duplicate_handling_keep_first(self, tmp_path):
        """Test transformation keeps first duplicate when set to keep-first."""
        csv_content = "ClientMatterCode,Name\n12345.67890,Alice\n12345.67890,Bob\n11111.22222,Charlie"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'ClientMatterCode',
            '-c', 'Name',
            '--duplicates', 'keep-first',
            '--key', 'ClientMatterCode',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert "Successfully wrote 2 rows" in result.output
        assert "Removed 1 duplicate rows" in result.output
        
        output_df = pd.read_csv(output_file, dtype=str)
        assert len(output_df) == 2
        assert output_df.iloc[0]["Name"] == "Alice"  # First occurrence kept
        assert output_df.iloc[1]["Name"] == "Charlie"
    
    def test_transform_validation_errors(self, tmp_path):
        """Test transformation fails on validation errors."""
        csv_content = "ClientMatterCode,Name\n12345.67890,Alice\ninvalid,Bob"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'ClientMatterCode',
            '-c', 'Name',
            '--key', 'ClientMatterCode',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 1
        assert "Validation Error:" in result.output
        assert "invalid" in result.output
        assert not output_file.exists()
    
    def test_transform_missing_source_column(self, tmp_path):
        """Test transformation fails when source column doesn't exist."""
        csv_content = "Name,Age\nAlice,30"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'NonexistentColumn:NewName',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 1
        assert "NonexistentColumn" in result.output
        assert "not found" in result.output
    
    def test_transform_empty_file(self, tmp_path):
        """Test transformation handles empty input file."""
        csv_content = "Name,Age\n"  # Header only, no data
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'Name',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 1
        assert "no data rows" in result.output
    
    def test_transform_excel_input(self, tmp_path):
        """Test transformation with Excel input file."""
        # Create Excel file
        df = pd.DataFrame({
            "Original Name": ["Alice Smith", "bob jones"],
            "Original Status": ["ACTIVE", "pending"]
        })
        xlsx_file = tmp_path / "input.xlsx"
        df.to_excel(xlsx_file, index=False, engine="openpyxl")
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(xlsx_file),
            '-c', 'Original Name:Name',
            '-c', 'Original Status:Status',
            '--case', 'proper',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        
        output_df = pd.read_csv(output_file, dtype=str)
        assert output_df.iloc[0]["Name"] == "Alice Smith"
        assert output_df.iloc[0]["Status"] == "Active"
        assert output_df.iloc[1]["Name"] == "Bob Jones"
        assert output_df.iloc[1]["Status"] == "Pending"
    
    def test_transform_creates_output_directory(self, tmp_path):
        """Test transformation creates output directory if it doesn't exist."""
        csv_content = "Name,Age\nAlice,30"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        # Output to nested directory that doesn't exist
        output_file = tmp_path / "subdir" / "nested" / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'Name',
            '-c', 'Age',
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.parent.exists()
    
    def test_transform_invalid_column_mapping_syntax(self, tmp_path):
        """Test transformation fails with invalid column mapping syntax."""
        csv_content = "Name,Age\nAlice,30"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', '',  # Empty mapping
            '--output', str(output_file)
        ])
        
        assert result.exit_code == 1
        assert "cannot be empty" in result.output
    
    def test_transform_no_columns_specified(self, tmp_path):
        """Test that transform command requires columns to be specified."""
        csv_content = "Name,Age\nAlice,30"
        input_file = tmp_path / "input.csv"
        input_file.write_text(csv_content)
        
        output_file = tmp_path / "output.csv"
        
        runner = CliRunner()
        result = runner.invoke(cli, [
            'transform', str(input_file),
            '--output', str(output_file)
        ])
        
        # Should fail because --columns/-c is required
        assert result.exit_code != 0


class TestCLIErrorHandling:
    """Tests for CLI error handling and edge cases."""
    
    def test_invalid_command(self):
        """Test invalid command name."""
        runner = CliRunner()
        result = runner.invoke(cli, ['invalid-command'])
        
        assert result.exit_code != 0
        assert "No such command" in result.output
    
    def test_help_command(self):
        """Test help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "CSV Tool" in result.output
        assert "profile" in result.output
        assert "transform" in result.output
    
    def test_profile_help(self):
        """Test profile command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['profile', '--help'])
        
        assert result.exit_code == 0
        assert "Profile a data file" in result.output
        assert "--key" in result.output
    
    def test_transform_help(self):
        """Test transform command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['transform', '--help'])
        
        assert result.exit_code == 0
        assert "Transform a data file" in result.output
        assert "--columns" in result.output
        assert "--case" in result.output
        assert "--duplicates" in result.output


class TestCLIEndToEnd:
    """End-to-end integration tests combining multiple operations."""
    
    def test_profile_then_transform_workflow(self, tmp_path):
        """Test realistic workflow: profile file, then transform it."""
        # Create messy input data
        csv_content = """ClientMatterCode,Client Name,Case Status,Notes
12345.67890,  ALICE CORP  ,ACTIVE,Important case
11111.22222,bob ltd,pending,Regular case
12345.1,charlie inc,CLOSED,Truncated code"""
        
        input_file = tmp_path / "messy_data.csv"
        input_file.write_text(csv_content)
        
        runner = CliRunner()
        
        # First, profile the data to understand issues
        profile_result = runner.invoke(cli, [
            'profile', str(input_file),
            '--key', 'ClientMatterCode'
        ])
        
        assert profile_result.exit_code == 0
        assert "Validation Errors:" in profile_result.output
        assert "12345.1" in profile_result.output  # Should detect truncation
        
        # Now transform the data (this will fail due to validation)
        output_file = tmp_path / "clean_data.csv"
        transform_result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'ClientMatterCode',
            '-c', 'Client Name:ClientName',
            '-c', 'Case Status:Status',
            '--case', 'proper',
            '--key', 'ClientMatterCode',
            '--output', str(output_file)
        ])
        
        assert transform_result.exit_code == 1  # Should fail due to validation error
        assert "Validation Error:" in transform_result.output
    
    def test_successful_data_cleaning_workflow(self, tmp_path):
        """Test successful end-to-end data cleaning workflow."""
        # Create data with only formatting issues (no validation errors)
        csv_content = """ClientMatterCode,Client Name,Case Status
12345.67890,  ALICE CORP  ,ACTIVE
11111.22222,bob ltd,pending
33333.44444,  CHARLIE INC  ,CLOSED"""
        
        input_file = tmp_path / "data.csv"
        input_file.write_text(csv_content)
        
        runner = CliRunner()
        
        # Profile the data
        profile_result = runner.invoke(cli, [
            'profile', str(input_file),
            '--key', 'ClientMatterCode'
        ])
        
        assert profile_result.exit_code == 0
        assert "Rows: 3" in profile_result.output
        assert "Validation Errors:" not in profile_result.output  # Should be clean
        
        # Transform the data
        output_file = tmp_path / "cleaned_data.csv"
        transform_result = runner.invoke(cli, [
            'transform', str(input_file),
            '-c', 'ClientMatterCode',
            '-c', 'Client Name:ClientName',
            '-c', 'Case Status:Status',
            '--case', 'proper',
            '--key', 'ClientMatterCode',
            '--output', str(output_file)
        ])
        
        assert transform_result.exit_code == 0
        assert "Successfully wrote 3 rows" in transform_result.output
        
        # Verify the cleaned data
        output_df = pd.read_csv(output_file, dtype=str)
        assert len(output_df) == 3
        assert list(output_df.columns) == ["ClientMatterCode", "ClientName", "Status"]
        
        # Check data cleaning worked
        assert output_df.iloc[0]["ClientName"] == "Alice Corp"  # Trimmed and proper case
        assert output_df.iloc[1]["ClientName"] == "Bob Ltd"     # Proper case
        assert output_df.iloc[0]["Status"] == "Active"         # Proper case
        assert output_df.iloc[1]["Status"] == "Pending"        # Proper case
        
        # Codes should be preserved exactly
        assert output_df.iloc[0]["ClientMatterCode"] == "12345.67890"
        assert output_df.iloc[1]["ClientMatterCode"] == "11111.22222"
        assert output_df.iloc[2]["ClientMatterCode"] == "33333.44444"