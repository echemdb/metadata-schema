r"""
The mdstools suite.

EXAMPLES::

    >>> from mdstools.test.cli import invoke
    >>> invoke(cli, "--help")  # doctest: +NORMALIZE_WHITESPACE
    Usage: cli [OPTIONS] COMMAND [ARGS]...
    <BLANKLINE>
      The mdstools suite.
    <BLANKLINE>
    Options:
      --help  Show this message and exit.
    <BLANKLINE>
    Commands:
      flatten    Flatten a YAML metadata file into enriched Excel/CSV formats.
      unflatten  Unflatten an Excel/CSV file back to YAML metadata.

"""

# ********************************************************************
#  This file is part of mdstools.
#
#        Copyright (C) 2026 Albert Engstfeld
#
#  mdstools is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  mdstools is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mdstools. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************
import logging
from pathlib import Path

import click

logger = logging.getLogger("mdstools")


@click.group(help="The mdstools suite.")
def cli():
    r"""
    Entry point of the command line interface.

    This redirects to the individual commands listed below.
    """


@click.command(name="flatten")
@click.argument("yaml_file", type=click.Path(exists=True))
@click.option(
    "--schema-dir",
    type=click.Path(file_okay=False),
    default="schemas",
    help="Directory containing JSON Schema files.",
)
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="generated",
    help="Output directory for flattened files.",
)
@click.option(
    "--no-enrichment",
    is_flag=True,
    default=False,
    help="Disable schema enrichment (no Description/Example columns).",
)
def flatten(yaml_file, schema_dir, output_dir, no_enrichment):
    """
    Flatten a YAML metadata file into enriched Excel/CSV formats.
    \f

    EXAMPLES::

        >>> import os
        >>> from mdstools.test.cli import invoke
        >>> from mdstools.entrypoint import cli
        >>> invoke(cli, "flatten", "tests/simple_test.yaml", "--output-dir", "tests/generated/cli_convert")  # doctest: +NORMALIZE_WHITESPACE
        Loading tests/simple_test.yaml...
        Processed 17 fields
        Enrichment: 15/17 fields (88.2%) have descriptions
        <BLANKLINE>
        Exporting to tests/generated/cli_convert/
          ✓ simple_test.csv
          ✓ simple_test.xlsx
          ✓ simple_test_sheets.xlsx
        <BLANKLINE>
        Done!

    """
    from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
    from mdstools.metadata.metadata import Metadata

    yaml_path = Path(yaml_file)

    click.echo(f"Loading {yaml_path.as_posix()}...")
    metadata = Metadata.from_yaml(str(yaml_path))
    flattened = metadata.flatten()

    enriched = not no_enrichment
    if enriched:
        enriched_metadata = EnrichedFlattenedMetadata(
            flattened.rows, schema_dir=schema_dir
        )
        df = enriched_metadata.to_pandas()
    else:
        df = flattened.to_pandas()

    click.echo(f"Processed {len(df)} fields")

    if enriched:
        has_desc = df["Description"].notna() & (df["Description"] != "")
        desc_count = has_desc.sum()
        click.echo(
            f"Enrichment: {desc_count}/{len(df)} fields "
            f"({100*desc_count/len(df):.1f}%) have descriptions"
        )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    base_name = yaml_path.stem
    csv_path = out / f"{base_name}.csv"
    excel_path = out / f"{base_name}.xlsx"
    excel_multi_path = out / f"{base_name}_sheets.xlsx"

    click.echo(f"\nExporting to {out.as_posix()}/")
    if enriched:
        enriched_metadata.to_csv(str(csv_path))
        enriched_metadata.to_excel(str(excel_path))
        enriched_metadata.to_excel(str(excel_multi_path), separate_sheets=True)
    else:
        flattened.to_csv(str(csv_path))
        flattened.to_excel(str(excel_path))
        flattened.to_excel(str(excel_multi_path), separate_sheets=True)

    click.echo(f"  ✓ {csv_path.name}")
    click.echo(f"  ✓ {excel_path.name}")
    click.echo(f"  ✓ {excel_multi_path.name}")
    click.echo("\nDone!")


@click.command(name="unflatten")
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output-dir",
    type=click.Path(file_okay=False),
    default="generated",
    help="Output directory for YAML.",
)
@click.option(
    "--schema-file",
    type=click.Path(dir_okay=False),
    default=None,
    help="Optional JSON schema file to validate against.",
)
def unflatten(input_file, output_dir, schema_file):
    """
    Unflatten an Excel/CSV file back to YAML metadata.
    \f

    EXAMPLES::

        >>> import os
        >>> from mdstools.test.cli import invoke
        >>> from mdstools.entrypoint import cli
        >>> from mdstools.metadata.metadata import Metadata
        >>> metadata = Metadata.from_yaml("tests/simple_test.yaml")
        >>> flattened = metadata.flatten()
        >>> os.makedirs("tests/generated/cli_unflatten", exist_ok=True)
        >>> flattened.to_excel("tests/generated/cli_unflatten/input.xlsx")
        >>> invoke(cli, "unflatten", "tests/generated/cli_unflatten/input.xlsx", "--output-dir", "tests/generated/cli_unflatten")
        ✓ Wrote tests/generated/cli_unflatten/input.yaml

    """
    from mdstools.metadata.flattened_metadata import FlattenedMetadata

    input_path = Path(input_file)

    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        flattened = FlattenedMetadata.from_excel(str(input_path))
    elif input_path.suffix.lower() == ".csv":
        flattened = FlattenedMetadata.from_csv(str(input_path))
    else:
        raise click.ClickException("Input file must be .csv, .xls, or .xlsx")

    metadata = flattened.unflatten(schema_path=schema_file)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    output_path = out / f"{input_path.stem}.yaml"
    metadata.to_yaml(str(output_path))
    click.echo(f"✓ Wrote {output_path.as_posix()}")


cli.add_command(flatten)
cli.add_command(unflatten)


# Register command docstrings for doctesting.
# Since commands are not functions anymore due to their decorator, their
# docstrings would otherwise be ignored.
__test__ = {
    name: command.__doc__ for (name, command) in cli.commands.items() if command.__doc__
}
