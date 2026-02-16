r"""
Check naming conventions across all JSON Schema files.

Ensures consistent naming:

- **Property keys** (YAML dict keys): ``camelCase`` — lowercase first letter,
  no underscores, no spaces (e.g., ``figureDescription``, ``scanRate``).
- **Definition names** (``definitions`` / ``$defs``): ``PascalCase`` — uppercase
  first letter, no underscores, no spaces (e.g., ``FigureDescription``, ``ScanRate``).
- **File names**: ``snake_case`` with ``.json`` extension — lowercase with
  underscores (e.g., ``figure_description.json``).

Run directly::

    python mdstools/schema/check_naming.py

Or via pixi::

    pixi run check-naming

EXAMPLES::

    >>> import subprocess, sys
    >>> result = subprocess.run(
    ...     [sys.executable, 'mdstools/schema/check_naming.py'],
    ...     capture_output=True, text=True)
    >>> result.returncode
    0

"""

import json
import re
import sys
from pathlib import Path

import yaml

# Patterns
CAMEL_CASE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
SNAKE_CASE_FILE = re.compile(r"^[a-z][a-z0-9_]*\.yaml$")

# Known exceptions: keys that come from external standards (e.g., JSON Schema
# itself or Frictionless Data) and are not under our control.
PROPERTY_EXCEPTIONS = {
    "additionalProperties",  # JSON Schema keyword used as a property value
}

# Definition name exceptions: names imported from or matching external
# conventions that intentionally deviate from PascalCase.
DEFINITION_EXCEPTIONS = set()

SCHEMA_DIR = Path("schemas/schema_pieces")


def collect_property_names(obj, path=""):
    r"""
    Recursively yield ``(dotted_path, key_name)`` for every property key.

    Descends into ``properties``, ``items``, ``oneOf``, ``anyOf``, ``allOf``,
    and ``definitions`` blocks.

    EXAMPLES::

        >>> schema = {"properties": {"fooBar": {"type": "string"}}}
        >>> list(collect_property_names(schema))
        [('fooBar', 'fooBar')]

    """
    if not isinstance(obj, dict):
        return
    if "properties" in obj:
        for key in obj["properties"]:
            full = f"{path}.{key}" if path else key
            yield (full, key)
            yield from collect_property_names(obj["properties"][key], full)
    for keyword in ("items", "oneOf", "anyOf", "allOf"):
        if keyword in obj:
            val = obj[keyword]
            if isinstance(val, list):
                for item in val:
                    yield from collect_property_names(item, path)
            elif isinstance(val, dict):
                yield from collect_property_names(val, path)


def collect_definition_names(schema):
    r"""
    Yield ``(definition_name,)`` for every key in ``definitions`` or ``$defs``.

    EXAMPLES::

        >>> schema = {"definitions": {"FooBar": {"type": "object"}}}
        >>> list(collect_definition_names(schema))
        [('FooBar',)]

    """
    for block_name in ("definitions", "$defs"):
        if block_name in schema:
            for def_name in schema[block_name]:
                yield (def_name,)


def check_file(filepath):
    r"""
    Check a single schema file for naming violations.

    Returns a list of ``(filepath, violation_description)`` tuples.

    EXAMPLES::

        >>> import tempfile, json, os
        >>> schema = {"properties": {"bad_key": {"type": "string"}},
        ...           "definitions": {"bad_def": {"type": "object"}}}
        >>> with tempfile.NamedTemporaryFile(
        ...     mode='w', suffix='.yaml', delete=False) as f:
        ...     import yaml as _yaml
        ...     _yaml.dump(schema, f)
        ...     tmppath = f.name
        >>> violations = check_file(Path(tmppath))
        >>> any('bad_key' in v for _, v in violations)
        True
        >>> any('bad_def' in v for _, v in violations)
        True
        >>> os.unlink(tmppath)

    """
    violations = []
    path = Path(filepath)

    # Check file name
    if not SNAKE_CASE_FILE.match(path.name):
        violations.append(
            (str(path), f"File name '{path.name}' is not snake_case.yaml")
        )

    with open(path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # For YAML schema pieces without a 'definitions' wrapper,
    # top-level keys are definition names (PascalCase) that also contain
    # property definitions. We need to check both levels.
    if "definitions" not in schema and "properties" not in schema:
        # Flat YAML format: top-level keys are definitions
        for def_name, def_value in schema.items():
            if def_name in DEFINITION_EXCEPTIONS:
                continue
            if not PASCAL_CASE.match(def_name):
                violations.append((str(path), f"Definition '{def_name}' is not PascalCase"))
            # Check property names within each definition
            if isinstance(def_value, dict):
                for dotted_path, key in collect_property_names(def_value):
                    if key in PROPERTY_EXCEPTIONS:
                        continue
                    if not CAMEL_CASE.match(key):
                        violations.append(
                            (
                                str(path),
                                f"Property '{key}' (at {def_name}.{dotted_path}) is not camelCase",
                            )
                        )
    else:
        # Standard JSON Schema structure with 'definitions' or 'properties'
        # Check property names (should be camelCase or single lowercase word)
        for dotted_path, key in collect_property_names(schema):
            if key in PROPERTY_EXCEPTIONS:
                continue
            if not CAMEL_CASE.match(key):
                violations.append(
                    (
                        str(path),
                        f"Property '{key}' (at {dotted_path}) is not camelCase",
                    )
                )

        # Check definition names (should be PascalCase)
        for (def_name,) in collect_definition_names(schema):
            if def_name in DEFINITION_EXCEPTIONS:
                continue
            if not PASCAL_CASE.match(def_name):
                violations.append((str(path), f"Definition '{def_name}' is not PascalCase"))

    return violations


def main():
    """Check all schema pieces for naming convention violations."""
    if not SCHEMA_DIR.exists():
        print(f"Error: {SCHEMA_DIR} not found", file=sys.stderr)
        sys.exit(1)

    all_violations = []
    files = sorted(SCHEMA_DIR.rglob("*.yaml"))

    for filepath in files:
        all_violations.extend(check_file(filepath))

    if all_violations:
        print(f"Found {len(all_violations)} naming convention violation(s):\n")
        for filepath, msg in all_violations:
            rel = (
                Path(filepath).relative_to(Path.cwd())
                if Path(filepath).is_absolute()
                else filepath
            )
            print(f"  {rel}: {msg}")
        print(
            "\nConventions: property keys = camelCase, "
            "definitions = PascalCase, file names = snake_case.yaml"
        )
        sys.exit(1)
    else:
        print(f"All {len(files)} schema files pass naming convention checks.")
        sys.exit(0)


if __name__ == "__main__":
    main()
