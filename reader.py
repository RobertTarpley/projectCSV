# File reading (CSV, Excel)
from pathlib import Path

import pandas as pd


def read_file(file_path: str) -> pd.DataFrame:
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path_obj.suffix.lower()

    if extension == ".csv":
        return pd.read_csv(file_path)
    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path, engine="openpyxl")
    else:
        raise ValueError(f"Unsupported file format: {extension}")
