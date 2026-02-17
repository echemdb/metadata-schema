#!/usr/bin/env python
"""
Update expected schemas after intentional changes to LinkML definitions.

Run this after reviewing diffs in generated schemas to accept the changes.
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

import shutil
from pathlib import Path

from mdstools.schema import RESOLVED_SCHEMA_FILES


def main():
    """Update expected baseline schemas from current resolved schemas."""
    schemas_dir = Path("schemas")
    expected_dir = Path("schemas/expected")

    # Create expected directory if it doesn't exist
    expected_dir.mkdir(parents=True, exist_ok=True)

    # List of schemas to update
    schemas_to_update = RESOLVED_SCHEMA_FILES

    print("Updating expected resolved schemas...")
    print("=" * 60)

    for schema_name in schemas_to_update:
        source = schemas_dir / schema_name
        dest = expected_dir / schema_name

        if not source.exists():
            print(f"⚠ Skipping {schema_name} (not found)")
            continue

        # Copy resolved schema to expected
        shutil.copy2(source, dest)
        print(f"✓ Updated {dest}")

    print("=" * 60)
    print("✓ Expected schemas updated successfully")
    print("\nCommit these changes with your schema updates:")
    print("  git add schemas/expected/")
    print("  git commit -m 'Update expected resolved schemas'")


if __name__ == "__main__":
    main()
