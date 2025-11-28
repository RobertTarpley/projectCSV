# Data profiling logic
import pandas as pd

from validators import validate_dataframe_codes


def profile_dataframe(
    df: pd.DataFrame, key_column: str | None = None
) -> dict[str, any]:
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
            print(f"Column '{key_column}' not found in DataFrame")

    validation_errors = None
    if key_column == "ClientMatterCode" and key_column in df.columns:
        validation_errors = validate_dataframe_codes(df, key_column)

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "columns_stats": columns_stats,
        "duplicate_info": duplicate_info,
        "validation_errors": validation_errors,
    }


def format_profile_output(profile: dict[str, any]) -> str:
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
