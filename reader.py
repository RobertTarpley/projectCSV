# File reading (CSV, Excel)
from pathlib import Path

import pandas as pd


def read_file(file_path: str) -> pd.DataFrame:
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path_obj.suffix.lower()

    if extension == ".csv":
        try:
            return pd.read_csv(file_path, dtype=str, encoding="utf-8-sig")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, dtype=str, encoding="latin-1")
    elif extension == ".xlsx":
        return pd.read_excel(file_path, dtype=str, engine="openpyxl")
    elif extension == ".xls":
        return pd.read_excel(file_path, dtype=str, engine="xlrd")
    else:
        raise ValueError(f"Unsupported file format: {extension}")
