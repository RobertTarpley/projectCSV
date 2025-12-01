# CSV Tool

A production-ready command-line utility for profiling and transforming messy CSV/Excel files, designed for preparing bulk uploads to case management systems.

[![Tests](https://img.shields.io/badge/tests-105%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](#testing)

## Problem

When preparing data for bulk uploads, you often receive "dirty" files from business users or third parties with:

- Inconsistent column naming conventions
- Extra whitespace, mixed case, irregular formatting
- Duplicate records
- Truncated values (e.g., Excel dropping trailing zeros from codes like `12345.00001`)
- Encoding issues (non-UTF-8 files)
- Business rule violations

This tool provides a robust, battle-tested solution for profiling incoming data and transforming it into clean, validated CSV files ready for upload.

## Features

### Profile Command

Analyze a data file before working with it:

- Row and column counts
- Null counts and unique values per column
- Duplicate detection on a key column
- Format validation for ClientMatterCode fields (XXXXX.XXXXX)

### Transform Command

Clean and reshape data for upload with comprehensive validation:

- **Column Operations**: Select specific columns, rename with flexible mapping syntax
- **Data Cleaning**: Trim whitespace, normalize nulls, apply case transformations
- **Encoding Handling**: Automatic encoding detection with chardet, UTF-8 output
- **Business Rules**: Validate ClientMatterCode format (XXXXX.XXXXX) with truncation detection
- **Duplicate Management**: Error on duplicates or keep first occurrence
- **Error Reporting**: Detailed validation errors with specific row numbers and issues
- **File Safety**: Create output directories automatically, comprehensive error handling

## Future Enhancements

The following features would enhance the tool's capabilities for future versions:

### 🚀 Nice-to-Have Features
- **Multi-format Output**: Export to Excel, JSON, and other formats beyond CSV
- **Advanced Validation Rules**: Custom validation patterns for different business domains
- **Data Type Inference**: Smart detection and conversion of dates, numbers, and categorical data
- **Configuration Files**: YAML/JSON config files for complex transformation pipelines
- **Batch Processing**: Process multiple files in a directory with parallel execution
- **Interactive Mode**: Step-by-step guided transformation with preview capabilities
- **Data Sampling**: Process and validate large files using representative samples
- **Custom Transformations**: Plugin system for domain-specific data cleaning rules
- **Audit Logging**: Detailed transformation logs with before/after statistics
- **Web Interface**: Browser-based GUI for non-technical users
- **API Integration**: REST API for programmatic access and system integration
- **Database Connectivity**: Direct import/export to SQL databases
- **Advanced Analytics**: Data quality scoring and transformation recommendations

### 📊 Performance Optimizations
- **Streaming Processing**: Handle files larger than available memory
- **Chunked Processing**: Process large datasets in configurable chunks
- **Parallel Execution**: Multi-threaded processing for CPU-intensive operations

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd project_csv_formatter

# Install with uv (recommended)
uv sync

# Install the CLI tool locally
uv pip install -e .

# Or install with pip
pip install -e .
```

After installation, you can use the `csv-tool` command directly from anywhere:

```bash
# Global CLI usage after installation
csv-tool profile data.xlsx --key ClientMatterCode
csv-tool transform data.xlsx -c "Name" -c "ID:ClientMatterCode" -o clean.csv
```

## Requirements

- Python 3.11+
- Dependencies: pandas, openpyxl, click, xlrd, chardet

## Usage

### Development Usage (without installation)

```bash
# Profile a file
uv run python cli.py profile data.xlsx
uv run python cli.py profile data.xlsx --key MatterID

# Transform a file
uv run python cli.py transform source.xlsx \
    --columns "MatterID:ClientMatterCode" "Col Foo:ColumnFoo" "Status" \
    --case proper \
    --duplicates keep-first \
    --output clean.csv
```

### Production Usage (after installation)

```bash
# Profile a file
csv-tool profile data.xlsx
csv-tool profile data.xlsx --key MatterID

# Transform a file
csv-tool transform source.xlsx \
    -c "MatterID:ClientMatterCode" -c "Col Foo:ColumnFoo" -c "Status" \
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

- **Input formats**: CSV and Excel (.xlsx, .xls) with automatic encoding detection
- **Error handling**: Fail fast with comprehensive error messages including row numbers
- **Output**: Always UTF-8 CSV with Unix line endings
- **Data integrity**: All data preserved as strings to prevent type inference issues
- **Unicode safety**: Robust handling of various encodings with chardet fallback
- **Testing**: 97% test coverage with 105 comprehensive unit and integration tests

## Project Structure

```
project_csv_formatter/
├── cli.py                    # CLI interface with Click
├── reader.py                 # File reading with encoding detection
├── profiler.py               # Data profiling and analysis
├── transformer.py            # Data cleaning and transformation
├── validators.py             # Business rule validation
├── pyproject.toml            # Project configuration and dependencies
├── tests/                    # Comprehensive test suite
│   ├── test_cli_integration.py   # End-to-end CLI tests
│   ├── test_profiler.py         # Profiling function tests
│   ├── test_reader.py           # File reading tests
│   ├── test_transformer.py     # Transformation logic tests
│   └── test_validators.py      # Validation rule tests
└── test_scripts/             # Legacy test files
```

## Dependencies

- pandas (>=2.3.3) - Data manipulation and analysis
- openpyxl (>=3.1.5) - Excel .xlsx support
- xlrd (>=2.0.2) - Excel .xls support  
- click (>=8.3.1) - CLI framework
- chardet (>=5.0.0) - Automatic encoding detection

### Development Dependencies

- pytest (>=8.3.3) - Testing framework
- pytest-cov (>=6.0.0) - Test coverage reporting

## Testing

The project includes comprehensive test coverage with 105 tests achieving 97% coverage:

```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=. --cov-report=term-missing

# Run specific test modules
uv run pytest tests/test_validators.py
uv run pytest tests/test_cli_integration.py
```

### Test Categories

- **Unit Tests**: Individual function testing for all modules
- **Integration Tests**: End-to-end CLI workflow testing  
- **Edge Cases**: Error handling, empty files, encoding issues
- **Business Rules**: ClientMatterCode validation scenarios
