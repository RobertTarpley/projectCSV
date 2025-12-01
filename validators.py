# Validation rules
import re

import pandas as pd

pattern = re.compile(r"^\d{5}\.\d{5}$")
sec_part_too_short = re.compile(r"^\d+\.\d{1,4}$")
first_part_too_short = re.compile(r"^\d{1,4}\.\d+$")


def validate_client_matter_code(value: str) -> tuple[bool, str | None]:
    """Validate a ClientMatterCode value against business rules.
    
    Validates that the code follows the expected XXXXX.XXXXX format (5 digits, 
    period, 5 digits) and detects common issues like truncation.
    
    Args:
        value: The ClientMatterCode value to validate. Can be string, number, or None.
        
    Returns:
        A tuple of (is_valid, error_message). If valid, error_message is None.
        If invalid, error_message describes the specific issue.
        
    Examples:
        >>> validate_client_matter_code("12345.67890")
        (True, None)
        >>> validate_client_matter_code("12345.1")
        (False, "Possible truncation - second part too short")
    """
    if value is None or pd.isna(value):
        return (False, "Client matter code is empty")

    value_string = str(value).strip()

    if re.match(pattern, value_string):
        return (True, None)
    elif re.match(sec_part_too_short, value_string):
        return (False, "Possible truncation - second part too short")
    elif re.match(first_part_too_short, value_string):
        return (False, "Possible truncation - first part too short")
    elif "." not in value_string:
        return (False, "Invalid format - missing period")
    else:
        return (False, "Invalid format - expected XXXXX.XXXXX")


def validate_dataframe_codes(df: pd.DataFrame, key_column: str) -> list[dict[str, any]]:
    """Validate all ClientMatterCode values in a DataFrame column.
    
    Applies ClientMatterCode validation to every value in the specified column
    and returns a list of validation errors with row numbers and details.
    
    Args:
        df: The DataFrame containing the data to validate.
        key_column: The name of the column containing ClientMatterCode values.
        
    Returns:
        A list of error dictionaries. Each dictionary contains:
        - 'row': The row number (1-based, accounting for header)
        - 'value': The invalid value
        - 'error': Description of the validation error
        
    Raises:
        ValueError: If the specified key_column is not found in the DataFrame.
        
    Examples:
        >>> df = pd.DataFrame({'Code': ['12345.67890', 'invalid']})
        >>> errors = validate_dataframe_codes(df, 'Code')
        >>> len(errors)
        1
        >>> errors[0]['row']
        3
    """
    if key_column not in df.columns:
        raise ValueError(f"Column '{key_column}' not found")

    error_list = []

    for index, value in df[key_column].items():
        is_valid, error_message = validate_client_matter_code(value)
        if not is_valid:
            error_list.append(
                {
                    "row": index + 2,  # accounts for 0-indexing and header row
                    "value": value,
                    "error": error_message,
                }
            )

    return error_list
