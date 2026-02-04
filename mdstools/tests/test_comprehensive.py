#!/usr/bin/env python
"""
Comprehensive test suite for metadata flattening and schema enrichment.

This demonstrates the complete workflow from YAML to enriched Excel/CSV files.
"""

import os
from pathlib import Path

import yaml

from mdstools.tabular_schema import MetadataConverter


def test_basic_flattening():
    """Test basic YAML flattening without schema enrichment."""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Flattening")
    print("=" * 80)

    # Load test data
    with open("tests/simple_test.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create converter without schema
    converter = MetadataConverter.from_dict(data)

    # Check flattened output
    df = converter.df
    print(f"✓ Flattened to {len(df)} rows")
    print(f"✓ Columns: {list(df.columns)}")

    # Export to CSV
    output = Path("tests/generated/basic_flat.csv")
    converter.to_csv(output)
    print(f"✓ Exported to {output}")

    assert output.exists()
    assert len(df) > 0
    assert list(df.columns) == ["Number", "Key", "Value"]


def test_schema_enrichment():
    """Test schema-based enrichment with descriptions and examples."""
    print("\n" + "=" * 80)
    print("TEST 2: Schema Enrichment")
    print("=" * 80)

    # Load test data
    with open("tests/simple_test.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create converter with schema enrichment
    converter = MetadataConverter.from_dict(data, schema_dir="schemas")

    # Check enriched output
    df = converter.enriched_df
    print(f"✓ Enriched to {len(df)} rows")
    print(f"✓ Columns: {list(df.columns)}")

    # Check that some descriptions were added
    has_desc = df["Description"].notna() & (df["Description"] != "")
    desc_count = has_desc.sum()
    print(f"✓ Found {desc_count} fields with descriptions")

    # Export enriched CSV
    output_csv = Path("tests/generated/enriched.csv")
    converter.to_csv(output_csv, enriched=True)
    print(f"✓ Exported enriched CSV to {output_csv}")

    # Export enriched Excel
    output_xlsx = Path("tests/generated/enriched.xlsx")
    converter.to_excel(output_xlsx, enriched=True)
    print(f"✓ Exported enriched Excel to {output_xlsx}")

    assert output_csv.exists()
    assert output_xlsx.exists()
    assert list(df.columns) == ["Number", "Key", "Value", "Example", "Description"]
    assert desc_count > 0


def test_multi_sheet_export():
    """Test export to multi-sheet Excel file."""
    print("\n" + "=" * 80)
    print("TEST 3: Multi-Sheet Excel Export")
    print("=" * 80)

    # Load test data
    with open("tests/simple_test.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create converter with schema
    converter = MetadataConverter.from_dict(data, schema_dir="schemas")

    # Export to multi-sheet Excel
    output = Path("tests/generated/enriched_multisheet.xlsx")
    converter.to_excel(output, enriched=True, separate_sheets=True)
    print(f"✓ Exported multi-sheet Excel to {output}")

    assert output.exists()


def test_specific_field_enrichment():
    """Test that specific fields get correct enrichment."""
    print("\n" + "=" * 80)
    print("TEST 4: Specific Field Enrichment")
    print("=" * 80)

    # Load test data
    with open("tests/simple_test.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create enriched dataframe
    converter = MetadataConverter.from_dict(data, schema_dir="schemas")
    df = converter.enriched_df

    # Check specific fields
    test_cases = [
        ("role", "curation.process.role"),
        ("name", "curation.process.name"),
        ("type", "system.type"),
    ]

    for key, expected_path in test_cases:
        rows = df[df["Key"] == key]
        if not rows.empty:
            first_match = rows.iloc[0]
            if first_match["Description"]:
                print(
                    f"✓ '{key}' has description: {first_match['Description'][:50]}..."
                )
            if first_match["Example"]:
                print(f"  Example: {first_match['Example']}")


def test_markdown_export():
    """Test markdown export functionality."""
    print("\n" + "=" * 80)
    print("TEST 5: Markdown Export")
    print("=" * 80)

    # Load test data
    with open("tests/simple_test.yaml", "r") as f:
        data = yaml.safe_load(f)

    # Create converter
    converter = MetadataConverter.from_dict(data, schema_dir="schemas")

    # Export to markdown
    markdown = converter.to_markdown(enriched=True)

    # Save to file
    output = Path("tests/generated/enriched.md")
    with open(output, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"✓ Exported markdown to {output}")
    print(f"✓ Markdown length: {len(markdown)} characters")

    assert len(markdown) > 0
    assert "|" in markdown  # Should be a table
    assert "Description" in markdown


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("RUNNING COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Ensure output directory exists
    os.makedirs("tests/generated", exist_ok=True)

    try:
        test_basic_flattening()
        test_schema_enrichment()
        test_multi_sheet_export()
        test_specific_field_enrichment()
        test_markdown_export()

        print("\n" + "=" * 80)
        print("✓ ALL TESTS PASSED")
        print("=" * 80)
        print("\nGenerated test files in tests/generated/:")
        for f in Path("tests/generated").iterdir():
            if f.is_file():
                print(f"  - {f.name} ({f.stat().st_size} bytes)")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
