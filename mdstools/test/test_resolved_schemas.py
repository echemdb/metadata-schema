#!/usr/bin/env python
"""
Test that generated schemas match expected output (snapshot/golden file testing).

This ensures that changes to LinkML definitions produce predictable changes in
generated JSON schemas.  During PRs, diffs in generated schemas can be reviewed
to catch unintended changes.
"""

import json
import subprocess
import sys
from pathlib import Path

from mdstools.schema import RESOLVED_SCHEMA_FILES


def _generate_schemas():
    """Run the LinkML JSON Schema generator and return True on success."""
    result = subprocess.run(
        [sys.executable, "mdstools/schema/generate_from_linkml.py", "--json-schema"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print("✗ Schema generation failed:")
        print(result.stderr)
        return False

    print(result.stdout)
    return True


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
    """Test that generated resolved schemas match the expected versions."""
    print("\n" + "=" * 80)
    print("TEST: Generated Schema Snapshot Testing")
    print("=" * 80)

    print("Generating schemas from LinkML definitions...")
    assert _generate_schemas(), "Failed to generate schemas from LinkML"

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
