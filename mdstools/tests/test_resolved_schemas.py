#!/usr/bin/env python
"""
Test that resolved schemas match expected output (snapshot/golden file testing).

This ensures that changes to schema_pieces produce predictable changes in resolved schemas.
During PRs, diffs in resolved schemas can be reviewed to catch unintended changes.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_resolved_schemas_match_expected():
    """Test that generated resolved schemas match the expected versions."""
    print("\n" + "="*80)
    print("TEST: Resolved Schema Snapshot Testing")
    print("="*80)
    
    # Generate fresh resolved schemas
    print("Generating resolved schemas from schema_pieces...")
    result = subprocess.run(
        [sys.executable, "mdstools/resolve_schemas.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"✗ Schema resolution failed:")
        print(result.stderr)
        assert False, "Failed to generate resolved schemas"
    
    print(result.stdout)
    
    # List of schemas to check
    schemas_to_check = [
        "autotag.json",
        "svgdigitizer.json",
        "echemdb_package.json",
        "svgdigitizer_package.json"
    ]
    
    schemas_dir = Path("schemas")
    expected_dir = Path("schemas/expected")
    
    # Ensure expected directory exists
    if not expected_dir.exists():
        print(f"\n⚠ Expected directory not found: {expected_dir}")
        print("Creating expected files from current resolved schemas...")
        expected_dir.mkdir(parents=True, exist_ok=True)
        
        for schema_name in schemas_to_check:
            source = schemas_dir / schema_name
            dest = expected_dir / schema_name
            if source.exists():
                dest.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
                print(f"  Created {dest}")
        
        print("\n✓ Expected files created. Commit them to establish baseline.")
        return  # Don't fail on first run
    
    # Compare each resolved schema with expected (following svgdigitizer pattern)
    mismatches = []
    
    for schema_name in schemas_to_check:
        generated_file = schemas_dir / schema_name
        expected_file = expected_dir / schema_name
        
        if not generated_file.exists():
            mismatches.append(f"Generated schema not found: {generated_file}")
            continue
        
        if not expected_file.exists():
            mismatches.append(f"Expected schema not found: {expected_file}")
            continue
        
        # Load and compare JSON (normalized by json.load, like svgdigitizer does)
        with open(generated_file, 'r', encoding='utf-8') as f:
            generated_data = json.load(f)
        
        with open(expected_file, 'r', encoding='utf-8') as f:
            expected_data = json.load(f)
        
        # Direct comparison
        if generated_data != expected_data:
            mismatches.append(
                f"\n{schema_name} differs from expected.\n"
                f"Run 'pixi run update-expected-schemas' if changes are intentional."
            )
            print(f"✗ {schema_name} differs from expected")
        else:
            print(f"✓ {schema_name} matches expected")
    
    if mismatches:
        error_msg = "\n" + "="*80 + "\n"
        error_msg += "RESOLVED SCHEMAS DO NOT MATCH EXPECTED FILES\n"
        error_msg += "="*80 + "\n"
        error_msg += "\n".join(mismatches)
        error_msg += "\n\nTo see differences:\n"
        error_msg += "  git diff schemas/expected/\n"
        error_msg += "\nIf changes are intentional, update expected files:\n"
        error_msg += "  pixi run update-expected-schemas\n"
        error_msg += "  git add schemas/expected/\n"
        assert False, error_msg
    
    print("\n✓ All resolved schemas match expected versions")


if __name__ == "__main__":
    test_resolved_schemas_match_expected()
