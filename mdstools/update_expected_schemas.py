#!/usr/bin/env python
"""
Update expected resolved schemas after intentional changes to schema_pieces.

Run this after reviewing diffs in resolved schemas to accept the changes.
"""

import shutil
from pathlib import Path


def main():
    schemas_dir = Path("schemas")
    expected_dir = Path("schemas/expected")
    
    # Create expected directory if it doesn't exist
    expected_dir.mkdir(parents=True, exist_ok=True)
    
    # List of schemas to update
    schemas_to_update = [
        "autotag.json",
        "svgdigitizer.json",
        "echemdb_package.json",
        "svgdigitizer_package.json"
    ]
    
    print("Updating expected resolved schemas...")
    print("="*60)
    
    for schema_name in schemas_to_update:
        source = schemas_dir / schema_name
        dest = expected_dir / schema_name
        
        if not source.exists():
            print(f"⚠ Skipping {schema_name} (not found)")
            continue
        
        # Copy resolved schema to expected
        shutil.copy2(source, dest)
        print(f"✓ Updated {dest}")
    
    print("="*60)
    print("✓ Expected schemas updated successfully")
    print("\nCommit these changes with your schema updates:")
    print("  git add schemas/expected/")
    print("  git commit -m 'Update expected resolved schemas'")


if __name__ == "__main__":
    main()
