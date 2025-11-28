# Validation rules
import re

import pandas as pd

pattern = re.compile(r"^\d{5}\.\d{5}$")
sec_part_too_short = re.compile(r"^\d+\.\d{1,4}$")
first_part_too_short = re.compile(r"^\d{1,4}\.\d+$")


def validate_client_matter_code(value: str) -> tuple[bool, str | None]:
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
