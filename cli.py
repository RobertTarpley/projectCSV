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
    """CSV Tool - Profile and transform messy data files"""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--key", default=None, help="Key column for duplicate detection")
def profile(file_path: str, key: str | None):
    """Profile a data file
    Usage: python cli.py profile data.xlsx --key ClientMatterCode"""

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
    """
    Transform a data file

    Usage: python cli.py transform data.xlsx -c "ID:ClientMatterCode"
           -c "Status" --case proper -o clean.csv
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
