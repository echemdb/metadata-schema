#!/usr/bin/env python
"""
Command-line interface for mdstools metadata conversion.
"""

import argparse
from pathlib import Path

import yaml

from mdstools.metadata.metadata import Metadata
from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata


def main():
    """Convert YAML metadata to enriched tabular formats."""
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

    args = parser.parse_args()

    # Load YAML file
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


if __name__ == "__main__":
    import sys

    sys.exit(main())
