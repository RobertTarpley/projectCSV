# CSV Tool

A command-line utility for profiling and transforming messy CSV/Excel files, designed for preparing bulk uploads to case management systems.

## Problem

When preparing data for bulk uploads, you often receive "dirty" files from business users or third parties with:

- Inconsistent column naming conventions
- Extra whitespace, mixed case, irregular formatting
- Duplicate records
- Truncated values (e.g., Excel dropping trailing zeros from codes like `12345.00001`)

This tool provides a quick way to profile incoming data and transform it into clean, validated CSV files ready for upload.

## Features

### Profile Command

Analyze a data file before working with it:

- Row and column counts
- Null counts and unique values per column
- Duplicate detection on a key column
- Format validation for ClientMatterCode fields (XXXXX.XXXXX)

### Transform Command

Clean and reshape data for upload:

- Select specific columns from source file
- Rename columns (map source names → destination names)
- Apply case transformation (upper/lower/proper/none)
- Trim whitespace, normalize nulls to empty strings
- Validate ClientMatterCode format and uniqueness
- Handle duplicates (error out or keep first occurrence)
- Output UTF-8 encoded CSV

## Planned Usage

```bash
# Profile a file
python cli.py profile data.xlsx
python cli.py profile data.xlsx --key MatterID

# Transform a file
python cli.py transform source.xlsx \
    --columns "MatterID:ClientMatterCode" "Col Foo:ColumnFoo" "Status" \
    --case proper \
    --duplicates keep-first \
    --output clean.csv
```

### Column Mapping Syntax

- `SourceName:DestName` — Select and rename
- `ColumnName` — Select, keep same name

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `--case` | upper, lower, proper, none | none | Case transformation for text |
| `--duplicates` | keep-first, error | error | Duplicate key handling |
| `--key` | column name | ClientMatterCode | Key column for uniqueness checks |

## ClientMatterCode Validation

The tool validates that ClientMatterCode values match the expected format:

- Pattern: `XXXXX.XXXXX` (5 digits, period, 5 digits)
- Detects likely truncation (e.g., `12345.1` flagged as problematic)

## Technical Decisions

- **Input formats**: CSV and Excel (.xlsx, .xls)
- **Error handling**: Fail fast with clear error messages including row numbers
- **Output**: Always UTF-8 CSV

## Project Structure (Planned)

```
csv_tool/
├── cli.py           # Entry point, argument parsing
├── reader.py        # File reading (CSV, Excel)
├── profiler.py      # Data profiling logic
├── transformer.py   # Cleaning and transformation
└── validators.py    # Validation rules
```

## Dependencies

- pandas
- openpyxl (for Excel support)
