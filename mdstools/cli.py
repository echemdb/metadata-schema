#!/usr/bin/env python
"""Command-line interface for mdstools metadata conversion."""

import argparse
from pathlib import Path

from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata
from mdstools.metadata.flattened_metadata import FlattenedMetadata
from mdstools.metadata.metadata import Metadata


def _build_convert_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert nested YAML metadata to enriched Excel/CSV formats"
    )
    parser.add_argument("yaml_file", type=str, help="Path to input YAML file")
    parser.add_argument(
        "--schema-dir",
        type=str,
        default="schemas",
        help="Directory containing JSON Schema files (default: schemas)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated",
        help="Output directory for converted files (default: generated)",
    )
    parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="Disable schema enrichment (no Description/Example columns)",
    )
    return parser


def _build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert metadata between YAML and tabular formats"
    )
    subparsers = parser.add_subparsers(dest="command")

    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert nested YAML metadata to enriched Excel/CSV formats",
    )
    _add_convert_args(convert_parser)

    unflatten_parser = subparsers.add_parser(
        "unflatten",
        help="Convert Excel/CSV metadata back to YAML",
    )
    _add_unflatten_args(unflatten_parser)

    return parser


def _add_convert_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("yaml_file", type=str, help="Path to input YAML file")
    parser.add_argument(
        "--schema-dir",
        type=str,
        default="schemas",
        help="Directory containing JSON Schema files (default: schemas)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated",
        help="Output directory for converted files (default: generated)",
    )
    parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="Disable schema enrichment (no Description/Example columns)",
    )


def _add_unflatten_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input_file", type=str, help="Path to input Excel/CSV file")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated",
        help="Output directory for YAML (default: generated)",
    )
    parser.add_argument(
        "--schema-file",
        type=str,
        default=None,
        help="Optional JSON schema file to validate against",
    )


def _run_convert(args: argparse.Namespace) -> int:
    yaml_path = Path(args.yaml_file)
    if not yaml_path.exists():
        print(f"Error: File not found: {yaml_path}")
        return 1

    # Load and flatten metadata
    print(f"Loading {yaml_path}...")
    metadata = Metadata.from_yaml(str(yaml_path))
    flattened = metadata.flatten()

    # Create enriched metadata if requested
    enriched = not args.no_enrichment
    if enriched:
        enriched_metadata = EnrichedFlattenedMetadata(
            flattened.rows, schema_dir=args.schema_dir
        )
        df = enriched_metadata.to_pandas()
    else:
        df = flattened.to_pandas()

    print(f"Processed {len(df)} fields")

    # Show enrichment stats if enabled
    if enriched:
        has_desc = df["Description"].notna() & (df["Description"] != "")
        desc_count = has_desc.sum()
        print(
            f"Enrichment: {desc_count}/{len(df)} fields "
            f"({100*desc_count/len(df):.1f}%) have descriptions"
        )

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Generate output filenames from input
    base_name = yaml_path.stem
    csv_path = output_dir / f"{base_name}.csv"
    excel_path = output_dir / f"{base_name}.xlsx"
    excel_multi_path = output_dir / f"{base_name}_sheets.xlsx"

    # Export files
    print(f"\nExporting to {output_dir}/")
    if enriched:
        enriched_metadata.to_csv(str(csv_path))
        print(f"  ✓ {csv_path.name}")

        enriched_metadata.to_excel(str(excel_path))
        print(f"  ✓ {excel_path.name}")

        # TODO: Implement separate_sheets in EnrichedFlattenedMetadata.to_excel()
        # For now, use single sheet
        enriched_metadata.to_excel(str(excel_multi_path))
        print(
            f"  ✓ {excel_multi_path.name} (Note: separate_sheets not yet implemented)"
        )
    else:
        flattened.to_csv(str(csv_path))
        print(f"  ✓ {csv_path.name}")

        flattened.to_excel(str(excel_path))
        print(f"  ✓ {excel_path.name}")

        # TODO: Implement separate_sheets
        flattened.to_excel(str(excel_multi_path))
        print(f"  ✓ {excel_multi_path.name}")

    print("\nDone!")
    return 0


def _run_unflatten(args: argparse.Namespace) -> int:
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        flattened = FlattenedMetadata.from_excel(str(input_path))
    elif input_path.suffix.lower() == ".csv":
        flattened = FlattenedMetadata.from_csv(str(input_path))
    else:
        print("Error: Input file must be .csv, .xls, or .xlsx")
        return 1

    metadata = flattened.unflatten(schema_path=args.schema_file)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{input_path.stem}.yaml"
    metadata.to_yaml(str(output_path))
    print(f"✓ Wrote {output_path}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """Convert metadata between YAML and tabular formats."""
    import sys

    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] in {"convert", "unflatten"}:
        parser = _build_main_parser()
        args = parser.parse_args(argv)
        if args.command == "convert":
            return _run_convert(args)
        if args.command == "unflatten":
            return _run_unflatten(args)
        parser.print_help()
        return 1

    # Legacy: treat args as convert parameters
    parser = _build_convert_parser()
    args = parser.parse_args(argv)
    return _run_convert(args)


if __name__ == "__main__":
    import sys

    sys.exit(main())
