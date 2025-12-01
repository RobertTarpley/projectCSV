# File reading (CSV, Excel)
from pathlib import Path
import chardet

import pandas as pd


def _read_csv_with_encoding_detection(file_path: str) -> pd.DataFrame:
    """Read CSV file with automatic encoding detection and error handling.
    
    Attempts to read a CSV file using common encodings first (utf-8-sig, utf-8, 
    cp1252, iso-8859-1), then falls back to chardet for detection if needed.
    Provides clear error messages when encoding cannot be determined.
    
    Args:
        file_path: Path to the CSV file to read.
        
    Returns:
        DataFrame with all columns as string type (dtype=str).
        
    Raises:
        ValueError: If encoding cannot be detected with sufficient confidence
                   or if the file cannot be read as a valid CSV.
    """
    # First try common encodings
    common_encodings = ['utf-8-sig', 'utf-8', 'cp1252', 'iso-8859-1']
    
    for encoding in common_encodings:
        try:
            return pd.read_csv(file_path, dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    
    # If common encodings fail, use chardet for detection
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
        
        detected = chardet.detect(raw_data)
        detected_encoding = detected['encoding']
        confidence = detected['confidence']
        
        if detected_encoding and confidence > 0.7:
            return pd.read_csv(file_path, dtype=str, encoding=detected_encoding)
        else:
            raise ValueError(
                f"Unable to detect file encoding with confidence. "
                f"Detected: {detected_encoding} (confidence: {confidence:.2f}). "
                f"Please save the file as UTF-8 and try again."
            )
    except Exception as e:
        raise ValueError(
            f"Failed to read CSV file: {str(e)}. "
            f"Please ensure the file is a valid CSV and try saving it as UTF-8."
        )


def read_file(file_path: str) -> pd.DataFrame:
    """Read data from CSV or Excel files with automatic format detection.
    
    Supports multiple file formats and handles encoding issues gracefully.
    All data is returned as string type to preserve formatting and avoid
    type inference issues during data transformation.
    
    Args:
        file_path: Path to the data file. Supported formats: .csv, .xlsx, .xls
        
    Returns:
        DataFrame with all columns as string type (dtype=str).
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file format is not supported or cannot be read.
        
    Examples:
        >>> df = read_file('data.csv')
        >>> df = read_file('data.xlsx')
    """
    path_obj = Path(file_path)

    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path_obj.suffix.lower()

    if extension == ".csv":
        return _read_csv_with_encoding_detection(file_path)
    elif extension == ".xlsx":
        return pd.read_excel(file_path, dtype=str, engine="openpyxl")
    elif extension == ".xls":
        return pd.read_excel(file_path, dtype=str, engine="xlrd")
    else:
        raise ValueError(f"Unsupported file format: {extension}")
