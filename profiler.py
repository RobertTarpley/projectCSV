# Data profiling logic
import pandas as pd
import click

from validators import validate_dataframe_codes


def profile_dataframe(
    df: pd.DataFrame, key_column: str | None = None
) -> dict[str, any]:
    """Analyze DataFrame structure, data quality, and business rule compliance.
    
    Provides comprehensive data profiling including row/column counts, missing
    values, unique values, duplicate detection, and ClientMatterCode validation.
    
    Args:
        df: The DataFrame to analyze.
        key_column: Optional column name for duplicate detection and validation.
                   If provided, will check for duplicates and validate ClientMatterCodes.
                   
    Returns:
        A dictionary containing:
        - 'total_rows': Number of data rows
        - 'total_columns': Number of columns  
        - 'columns_stats': List of per-column statistics
        - 'duplicate_info': Duplicate analysis (None if no key_column or no duplicates)
        - 'validation_errors': List of validation errors (None if no key_column)
        
    Examples:
        >>> df = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Age': [30, 25]})
        >>> profile = profile_dataframe(df)
        >>> profile['total_rows']
        2
    """
    total_rows = len(df)
    total_columns = len(df.columns)

    # calculate per-column stats:
    columns_stats = []
    for column in df.columns:
        columns_stats.append(
            {
                "name": column,
                "type": df[column].dtype,
                "unique_values": df[column].nunique(),
                "missing_values": df[column].isnull().sum(),
            }
        )

    # check for dups
    duplicate_info = None
    if key_column is not None:
        if key_column in df.columns:
            duplicated_mask = df[key_column].duplicated(keep=False)
            duplicate_count = df[key_column].duplicated().sum()

            if duplicate_count > 0:
                duplicate_info = {
                    "count": duplicate_count,
                    "column": key_column,
                    "values": df[duplicated_mask][key_column].unique().tolist(),
                }
        else:
            click.echo(f"Column '{key_column}' not found in DataFrame", err=True)

    validation_errors = None
    if key_column is not None and key_column in df.columns:
        validation_errors = validate_dataframe_codes(df, key_column)

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "columns_stats": columns_stats,
        "duplicate_info": duplicate_info,
        "validation_errors": validation_errors,
    }


def format_profile_output(profile: dict[str, any]) -> str:
    """Format a profile dictionary into human-readable text output.
    
    Converts the structured profile data from profile_dataframe() into a
    formatted string suitable for display to users.
    
    Args:
        profile: Profile dictionary returned by profile_dataframe().
        
    Returns:
        Formatted string with file statistics, column details, duplicates,
        and validation errors in a readable format.
        
    Examples:
        >>> profile = {'total_rows': 3, 'total_columns': 2, 'columns_stats': [...]}
        >>> output = format_profile_output(profile)
        >>> 'Rows: 3' in output
        True
    """
    output = "File Profile\n"
    output += "============\n"
    output += f"Rows: {profile['total_rows']}\n"
    output += f"Columns: {profile['total_columns']}\n\n"

    output += "Column Statistics:\n"
    for column in profile["columns_stats"]:
        output += f"{column['name']}: {column['type']}\n"
        output += f"Unique Values: {column['unique_values']}\n"
        output += f"Missing Values: {column['missing_values']}\n\n"

    if profile["duplicate_info"] is not None:
        output += f"Duplicates found on {profile['duplicate_info']['column']}:\n"
        output += f"  Count: {profile['duplicate_info']['count']}\n"
        output += (
            f"  Values: {', '.join(map(str, profile['duplicate_info']['values']))}\n"
        )

    if profile["validation_errors"] is not None and profile["validation_errors"]:
        output += "\nValidation Errors:\n"
        for error in profile["validation_errors"]:
            output += f"  Row {error['row']}: {error['value']} - {error['error']}\n"

    return output
