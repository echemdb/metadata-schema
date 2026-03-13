#!/usr/bin/env python
"""
Test that committed schemas match expected output (snapshot/golden file testing).

This ensures that changes to LinkML definitions produce predictable changes in
committed JSON schemas.  During PRs, diffs in committed schemas can be reviewed
to catch unintended changes.

Note: This test compares the *committed* schemas in ``schemas/`` against the
expected baselines in ``schemas/expected/``.  A separate CI job
(``check-schemas``) validates that the committed schemas are up-to-date with
the LinkML definitions by running ``gen-json-schema`` and diffing the output.
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

import json
from pathlib import Path

from mdstools.schema import RESOLVED_SCHEMA_FILES


def _ensure_expected_dir(expected_dir, schemas_dir):
    """Create expected directory and seed baseline files if missing. Returns True if seeded."""
    if expected_dir.exists():
        return False

    print(f"\n⚠ Expected directory not found: {expected_dir}")
    print("Creating expected files from current resolved schemas...")
    expected_dir.mkdir(parents=True, exist_ok=True)

    for schema_name in RESOLVED_SCHEMA_FILES:
        source = schemas_dir / schema_name
        dest = expected_dir / schema_name
        if source.exists():
            dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  Created {dest}")

    print("\n✓ Expected files created. Commit them to establish baseline.")
    return True


def _compare_schemas(schemas_dir, expected_dir):
    """Compare resolved schemas against expected baselines. Returns list of mismatches."""
    mismatches = []

    for schema_name in RESOLVED_SCHEMA_FILES:
        generated_file = schemas_dir / schema_name
        expected_file = expected_dir / schema_name

        if not generated_file.exists():
            mismatches.append(f"Generated schema not found: {generated_file}")
            continue

        if not expected_file.exists():
            mismatches.append(f"Expected schema not found: {expected_file}")
            continue

        with open(generated_file, "r", encoding="utf-8") as f:
            generated_data = json.load(f)

        with open(expected_file, "r", encoding="utf-8") as f:
            expected_data = json.load(f)

        if generated_data != expected_data:
            mismatches.append(
                f"\n{schema_name} differs from expected.\n"
                "Run 'pixi run update-expected-schemas' if changes are intentional."
            )
            print(f"✗ {schema_name} differs from expected")
        else:
            print(f"✓ {schema_name} matches expected")

    return mismatches


def test_resolved_schemas_match_expected():
    """Test that committed resolved schemas match the expected versions."""
    print("\n" + "=" * 80)
    print("TEST: Committed Schema Snapshot Testing")
    print("=" * 80)

    schemas_dir = Path("schemas")
    expected_dir = Path("schemas/expected")

    if _ensure_expected_dir(expected_dir, schemas_dir):
        return  # Don't fail on first run

    mismatches = _compare_schemas(schemas_dir, expected_dir)

    if mismatches:
        error_msg = "\n" + "=" * 80 + "\n"
        error_msg += "RESOLVED SCHEMAS DO NOT MATCH EXPECTED FILES\n"
        error_msg += "=" * 80 + "\n"
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
