# Entry point, argument parsing
import sys
from pathlib import Path

import click

from profiler import format_profile_output, profile_dataframe
from reader import read_file
from transformer import (
    ColumnMapping,
    TransformConfig,
    transform_dataframe,
    write_output,
)


@click.group()
def cli():
    """CSV Tool - Profile and transform messy data files.
    
    A command-line tool for analyzing and transforming CSV/Excel files.
    Provides data profiling capabilities and comprehensive data transformation
    with validation, duplicate handling, and formatting standardization.
    
    Use 'profile' to analyze data quality and 'transform' to clean and format data.
    """
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--key", default=None, help="Key column for duplicate detection")
def profile(file_path: str, key: str | None):
    """Analyze data file structure, quality, and business rule compliance.
    
    Generates a comprehensive report showing row/column counts, data types,
    missing values, unique counts, duplicate detection, and ClientMatterCode
    validation when a key column is specified.
    
    Args:
        file_path: Path to CSV or Excel file to analyze.
        key: Optional column name for duplicate detection and validation.
             If specified, will validate ClientMatterCode format (XXXXX.XXXXX).
             
    Examples:
        \\b
        Profile basic file structure:
        $ python cli.py profile data.csv
        
        \\b
        Profile with ClientMatterCode validation:
        $ python cli.py profile data.xlsx --key ClientMatterCode
    """

    try:
        df = read_file(file_path)
        profile_data = profile_dataframe(df, key_column=key)
        output = format_profile_output(profile_data)
        click.echo(output)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--columns",
    "-c",
    multiple=True,
    required=True,
    help='Column mappings: "Source:Dest" or "ColumnName"',
)
@click.option(
    "--case",
    type=click.Choice(["lower", "upper", "proper", "none"]),
    default="none",
    help="Case transformation to apply",
)
@click.option(
    "--duplicates",
    type=click.Choice(["keep-first", "error"]),
    default="error",
    help="How to handle duplicate keys",
)
@click.option(
    "--key", default="ClientMatterCode", help="Key column for uniqueness validation"
)
@click.option(
    "--output", "-o", type=click.Path(), required=True, help="Output CSV file path"
)
def transform(
    source_file: str, columns: tuple, case: str, duplicates: str, key: str, output: str
):
    """Clean and transform data files with comprehensive validation.
    
    Applies a complete data transformation pipeline including column selection/renaming,
    whitespace trimming, case conversion, ClientMatterCode validation, and duplicate
    handling. Outputs clean, standardized UTF-8 CSV files ready for business use.
    
    Args:
        source_file: Path to input CSV or Excel file.
        columns: Column mappings in 'Source:Destination' or 'ColumnName' format.
                Can be specified multiple times for multiple columns.
        case: Text case transformation ('lower', 'upper', 'proper', 'none').
        duplicates: How to handle duplicate key values ('keep-first', 'error').
        key: Column name for duplicate detection and ClientMatterCode validation.
        output: Path for output CSV file. Directories will be created if needed.
        
    Examples:
        \\b
        Basic transformation with column renaming:
        $ python cli.py transform data.xlsx -c "ID:ClientMatterCode" -c "Name" -o clean.csv
        
        \\b
        Full transformation with case conversion and duplicate removal:
        $ python cli.py transform messy.csv -c "Client ID:ClientMatterCode" -c "Client Name:ClientName" 
            --case proper --duplicates keep-first -o cleaned.csv
    """

    try:
        column_mappings = ColumnMapping.parse_mappings(list(columns))
        config = TransformConfig(
            column_mappings=column_mappings,
            case_transform=case,
            duplicate_handling=duplicates,
            key_column=key,
            output_path=output,
        )

        df = read_file(source_file)

        if df.empty:
            click.echo("Warning: Input file contains no data rows", err=True)
            sys.exit(1)

        transformed_df = transform_dataframe(df, config)
        write_output(transformed_df, Path(output))
        click.echo(f"Successfully wrote {len(transformed_df)} rows to {output}")

    except ValueError as e:
        click.echo(f"Validation Error:\n{e}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
