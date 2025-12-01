# Cleaning and transformation

from pathlib import Path

import pandas as pd
import click

from validators import validate_dataframe_codes


class ColumnMapping:
    """Parse and store column mapping configuration.
    
    Handles column mapping syntax of either 'source:destination' format for
    renaming columns, or just 'column_name' to keep the same name.
    
    Attributes:
        source_name (str): The name of the column in the source data.
        dest_name (str): The desired name for the column in the output.
    """

    def __init__(self, mapping_string: str):
        """Initialize a ColumnMapping from a mapping string.
        
        Args:
            mapping_string: Either 'source:destination' or 'column_name'.
                          Whitespace around names is automatically trimmed.
                          
        Raises:
            ValueError: If mapping_string is empty or has invalid syntax.
            
        Examples:
            >>> mapping = ColumnMapping("Name")
            >>> mapping.source_name == mapping.dest_name == "Name"
            True
            >>> mapping = ColumnMapping("Old Name:New Name")
            >>> mapping.source_name == "Old Name"
            True
        """
        mapping_string = mapping_string.strip()
        
        # Validate input is not empty
        if not mapping_string:
            raise ValueError("Column mapping cannot be empty")

        if ":" in mapping_string:
            parts = mapping_string.split(":")
            
            # Validate colon syntax
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid column mapping syntax: '{mapping_string}'. "
                    f"Expected format: 'source:destination' or 'column_name'"
                )
            
            self.source_name = parts[0].strip()
            self.dest_name = parts[1].strip()
            
            # Validate both parts are not empty
            if not self.source_name:
                raise ValueError(
                    f"Invalid column mapping: '{mapping_string}'. "
                    f"Source column name cannot be empty"
                )
            if not self.dest_name:
                raise ValueError(
                    f"Invalid column mapping: '{mapping_string}'. "
                    f"Destination column name cannot be empty"
                )
        else:
            self.source_name = mapping_string
            self.dest_name = mapping_string

    @staticmethod
    def parse_mappings(mapping_strings: list[str]) -> list["ColumnMapping"]:
        """Parse a list of mapping strings into ColumnMapping objects.
        
        Convenience method for bulk parsing of column mappings from CLI input.
        
        Args:
            mapping_strings: List of strings in 'source:destination' or 'column_name' format.
            
        Returns:
            List of ColumnMapping objects ready for use in transformation.
            
        Raises:
            ValueError: If any mapping string has invalid syntax.
            
        Examples:
            >>> mappings = ColumnMapping.parse_mappings(["Name", "Old:New"])
            >>> len(mappings)
            2
        """
        return [ColumnMapping(s) for s in mapping_strings]


class TransformConfig:
    """Configuration container for data transformation operations.
    
    Encapsulates all settings needed for transforming a DataFrame including
    column mapping, case conversion, duplicate handling, and validation.
    
    Attributes:
        column_mappings (list[ColumnMapping]): Column selection and renaming rules.
        case_transform (str): Text case conversion ('upper', 'lower', 'proper', 'none').
        duplicate_handling (str): How to handle duplicates ('error', 'keep-first').
        key_column (str): Column name for duplicate detection and validation.
        output_path (str): Path where transformed data will be written.
    """

    def __init__(
        self,
        column_mappings: list[ColumnMapping],
        case_transform: str,
        duplicate_handling: str,
        key_column: str,
        output_path: str,
    ):
        """Initialize transformation configuration.
        
        Args:
            column_mappings: List of ColumnMapping objects defining column selection/renaming.
            case_transform: Text case conversion method ('upper', 'lower', 'proper', 'none').
            duplicate_handling: Duplicate row handling strategy ('error', 'keep-first').
            key_column: Column name for duplicate detection and ClientMatterCode validation.
            output_path: File path where transformed data will be written.
        """
        self.column_mappings = column_mappings
        self.case_transform = case_transform  # 'upper', 'lower', 'proper', 'none'
        self.duplicate_handling = duplicate_handling  # 'error', 'keep-first'
        self.key_column = key_column
        self.output_path = output_path


def transform_dataframe(df: pd.DataFrame, config: TransformConfig) -> pd.DataFrame:
    """Transform a DataFrame according to the provided configuration.
    
    Applies a comprehensive data transformation pipeline including column selection,
    renaming, whitespace trimming, case conversion, data validation, and duplicate
    handling. Ensures data quality and consistency for business use.
    
    Args:
        df: Source DataFrame to transform. Must contain all required source columns.
        config: TransformConfig object specifying all transformation rules.
        
    Returns:
        Cleaned and transformed DataFrame ready for output.
        
    Raises:
        ValueError: If DataFrame is empty, no columns specified, source columns
                   missing, validation errors found, or all data filtered out.
                   
    Examples:
        >>> df = pd.DataFrame({'Old': ['  Alice  '], 'Age': ['30']})
        >>> mappings = [ColumnMapping('Old:New'), ColumnMapping('Age')]
        >>> config = TransformConfig(mappings, 'proper', 'error', 'Age', 'out.csv')
        >>> result = transform_dataframe(df, config)
        >>> result.iloc[0]['New']
        'Alice'
    """
    # Handle edge case: empty DataFrame
    if df.empty:
        raise ValueError("Cannot transform an empty DataFrame")
    
    # Handle edge case: no column mappings
    if not config.column_mappings:
        raise ValueError("No column mappings specified")
    
    # Implement transformation logic here
    # select and rename columns
    source_cols = [m.source_name for m in config.column_mappings]
    for col in source_cols:
        if col not in df.columns:
            available_cols = ', '.join(df.columns.tolist())
            raise ValueError(
                f"Column '{col}' not found in source file. "
                f"Available columns: {available_cols}"
            )
    
    df = df[source_cols].copy()
    rename_map = {m.source_name: m.dest_name for m in config.column_mappings}
    df = df.rename(columns=rename_map)
    
    # Handle edge case: all rows filtered out after column selection
    if df.empty:
        raise ValueError("No data remaining after column selection")

    # trim whitespace
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.strip()

    # normalize nulls
    df = df.fillna("")

    # apply case transformation
    if config.case_transform == "upper":
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.upper()
    elif config.case_transform == "lower":
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.lower()
    elif config.case_transform == "proper":
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.title()

    # validate key column
    if config.key_column in df.columns:
        errors = validate_dataframe_codes(df, config.key_column)
        if errors:
            error_msg = "Validation errors found:\n"
            for error in errors:
                error_msg += (
                    f"  Row {error['row']}: {error['value']} - {error['error']} \n"
                )
            raise ValueError(error_msg)

    # handle duplicates
    if config.key_column in df.columns:
        duplicated = df[config.key_column].duplicated()
        if duplicated.any():
            if config.duplicate_handling == "error":
                dup_values = df[duplicated][config.key_column].tolist()
                raise ValueError(f"Duplicate values found in key column: {dup_values}")
            elif config.duplicate_handling == "keep-first":
                original_count = len(df)
                df = df.drop_duplicates(subset=config.key_column, keep="first")
                removed_count = original_count - len(df)
                click.echo(f"Removed {removed_count} duplicate rows")
                
                # Handle edge case: all rows were duplicates
                if df.empty:
                    raise ValueError("All rows were duplicates - no data remaining")

    # return transformed dataframe
    return df


def write_output(df: pd.DataFrame, output_path: Path) -> None:
    """Write DataFrame to UTF-8 CSV file with comprehensive error handling.
    
    Creates output directories as needed and writes the DataFrame to a CSV file
    using UTF-8 encoding with Unix line endings. Provides specific error messages
    for common failure scenarios like permission issues.
    
    Args:
        df: DataFrame to write to file. Must not be empty.
        output_path: Path object specifying where to write the CSV file.
                    Parent directories will be created if they don't exist.
                    
    Raises:
        ValueError: If the DataFrame is empty.
        PermissionError: If lacking write permissions to the output location.
        OSError: For other file system errors (disk full, invalid path, etc.).
        
    Examples:
        >>> df = pd.DataFrame({'Name': ['Alice'], 'Age': ['30']})
        >>> write_output(df, Path('output.csv'))
    """
    
    # Handle edge case: empty DataFrame
    if df.empty:
        raise ValueError("Cannot write an empty DataFrame to file")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False, encoding="utf-8", lineterminator="\n")
    except PermissionError as e:
        raise PermissionError(f"Permission denied writing to '{output_path}': {e}") from e
    except OSError as e:
        raise OSError(f"Error writing output file '{output_path}': {e}") from e
