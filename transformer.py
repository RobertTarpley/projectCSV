# Cleaning and transformation

from pathlib import Path

import pandas as pd

from validators import validate_dataframe_codes


class ColumnMapping:
    """Parse and store column mapping (source:dest or just name)"""

    def __init__(self, mapping_string: str):
        mapping_string = mapping_string.strip()

        if ":" in mapping_string:
            parts = mapping_string.split(":")
            self.source_name = parts[0].strip()
            self.dest_name = parts[1].strip()
        else:
            self.source_name = mapping_string
            self.dest_name = mapping_string

    @staticmethod
    def parse_mappings(mapping_strings: list[str]) -> list["ColumnMapping"]:
        return [ColumnMapping(s) for s in mapping_strings]


class TransformConfig:
    """Configuration for transformation"""

    def __init__(
        self,
        column_mappings: list[ColumnMapping],
        case_transform: str,
        duplicate_handling: str,
        key_column: str,
        output_path: str,
    ):
        self.column_mappings = column_mappings
        self.case_transform = case_transform  # 'upper', 'lower', 'proper', 'none'
        self.duplicate_handling = duplicate_handling  # 'error', 'keep-first'
        self.key_column = key_column
        self.output_path = output_path


def transform_dataframe(df: pd.DataFrame, config: TransformConfig) -> pd.DataFrame:
    # Implement transformation logic here
    # select and rename columns
    source_cols = [m.source_name for m in config.column_mappings]
    for col in source_cols:
        if col not in df.columns:
            raise ValueError(f"Column {col} not found in source file")
    df = df[source_cols].copy()
    rename_map = {m.source_name: m.dest_name for m in config.column_mappings}
    df = df.rename(columns=rename_map)

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
                df = df.drop_duplicates(subset=config.key_column, keep="first")
                print(f"Removed {duplicated.sum()} duplicate rows")

    # return transformed dataframe
    return df


def write_output(df: pd.DataFrame, output_path: Path) -> None:
    # write dataframe to UTF-8 csv

    try:
        df.to_csv(output_path, index=False, encoding="utf-8", lineterminator="\n")
    except OSError as e:
        raise OSError(f"Error writing output file: {e}") from e
