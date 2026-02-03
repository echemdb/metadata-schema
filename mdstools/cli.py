#!/usr/bin/env python
"""
Command-line interface for mdstools metadata conversion.
"""

import argparse
import yaml
from pathlib import Path
from mdstools.tabular_schema import MetadataConverter


def main():
    """Convert YAML metadata to enriched tabular formats."""
    parser = argparse.ArgumentParser(
        description='Convert nested YAML metadata to enriched Excel/CSV formats'
    )
    parser.add_argument(
        'yaml_file',
        type=str,
        help='Path to input YAML file'
    )
    parser.add_argument(
        '--schema-dir',
        type=str,
        default='schemas',
        help='Directory containing JSON Schema files (default: schemas)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='generated',
        help='Output directory for converted files (default: generated)'
    )
    parser.add_argument(
        '--no-enrichment',
        action='store_true',
        help='Disable schema enrichment (no Description/Example columns)'
    )

    args = parser.parse_args()

    # Load YAML file
    yaml_path = Path(args.yaml_file)
    if not yaml_path.exists():
        print(f"Error: File not found: {yaml_path}")
        return 1

    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Create converter
    print(f"Loading {yaml_path}...")
    if args.no_enrichment:
        converter = MetadataConverter.from_dict(data)
    else:
        converter = MetadataConverter.from_dict(data, schema_dir=args.schema_dir)

    # Get dataframes
    enriched = not args.no_enrichment
    df = converter.enriched_df if enriched else converter.df

    print(f"Processed {len(df)} fields")

    # Show enrichment stats if enabled
    if enriched:
        has_desc = df['Description'].notna() & (df['Description'] != '')
        desc_count = has_desc.sum()
        print(f"Enrichment: {desc_count}/{len(df)} fields ({100*desc_count/len(df):.1f}%) have descriptions")

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
    converter.to_csv(csv_path, enriched=enriched)
    print(f"  ✓ {csv_path.name}")

    converter.to_excel(excel_path, enriched=enriched)
    print(f"  ✓ {excel_path.name}")

    converter.to_excel(excel_multi_path, enriched=enriched, separate_sheets=True)
    print(f"  ✓ {excel_multi_path.name}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    exit(main())
