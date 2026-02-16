#!/usr/bin/env python
r"""
Validate example YAML/JSON files against generated JSON schemas.

All validation uses the generated JSON schemas in ``schemas/`` (produced from
LinkML sources).  Object examples (``examples/objects/``) are validated by
extracting the matching ``$defs`` entry from a generated schema.

Usage::

    python mdstools/schema/validate_examples.py

Or via pixi::

    pixi run validate-objects
    pixi run validate-file-schemas

EXAMPLES::

    >>> import io, contextlib
    >>> from mdstools.schema.validate_examples import validate_objects
    >>> buf = io.StringIO()
    >>> with contextlib.redirect_stdout(buf):
    ...     result = validate_objects()
    >>> result
    True

"""

import json
import sys
from pathlib import Path

import jsonschema
import yaml


def _load_generated_schema(schema_path: Path) -> dict:
    """Load a generated JSON schema file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_object_schema(parent_schema: dict, def_name: str) -> dict:
    r"""Build a standalone schema for a single ``$defs`` entry.

    The returned schema keeps the full ``$defs`` block from *parent_schema*
    (so nested ``$ref`` links still resolve) and sets the root to point at
    *def_name*.

    EXAMPLES::

        >>> from mdstools.schema.validate_examples import _build_object_schema
        >>> parent = {"$defs": {"Foo": {"type": "object", "properties": {"x": {"type": "string"}}}}}
        >>> sub = _build_object_schema(parent, "Foo")
        >>> sub["$ref"]
        '#/$defs/Foo'
        >>> "Foo" in sub["$defs"]
        True

    """
    return {
        "$schema": parent_schema.get(
            "$schema", "https://json-schema.org/draft/2020-12/schema"
        ),
        "$defs": parent_schema.get("$defs", {}),
        "$ref": f"#/$defs/{def_name}",
    }


def validate_data(data: dict, schema: dict, registry=None) -> list:
    """Validate data against a schema, return list of error messages."""
    from referencing import Registry

    if registry is None:
        registry = Registry()
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    return errors


# Mapping of object example names to:
#   (generated_schema_file, PascalCase_def_name, is_array)
_OBJECT_MAP = {
    "curation": ("autotag.json", "Curation", False),
    "eln": ("autotag.json", "Eln", False),
    "experimental": ("autotag.json", "Experimental", False),
    "figure_description": ("autotag.json", "FigureDescription", False),
    "projects": ("autotag.json", "Project", True),
    "source": ("minimum_echemdb.json", "Source", False),
    "system": ("autotag.json", "System", False),
}


def validate_objects():
    """Validate individual YAML examples against generated JSON schema definitions."""
    schemas_dir = Path("schemas")
    examples_dir = Path("examples/objects")

    ok = True
    for obj, (schema_file, def_name, is_array) in _OBJECT_MAP.items():
        example_path = examples_dir / f"{obj}.yaml"
        schema_path = schemas_dir / schema_file

        if not schema_path.exists():
            print(f"  SKIP {obj} (schema {schema_file} not found)")
            continue
        if not example_path.exists():
            print(f"  SKIP {obj} (example not found)")
            continue

        parent = _load_generated_schema(schema_path)

        if is_array:
            # The example file contains a bare array of items
            schema = {
                "$schema": parent.get(
                    "$schema", "https://json-schema.org/draft/2020-12/schema"
                ),
                "$defs": parent.get("$defs", {}),
                "type": "array",
                "items": {"$ref": f"#/$defs/{def_name}"},
            }
        else:
            schema = _build_object_schema(parent, def_name)

        with open(example_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        errors = validate_data(data, schema)
        if errors:
            print(f"  FAIL {obj}: {len(errors)} error(s)")
            for err in errors[:5]:
                path = "/".join(str(p) for p in err.absolute_path) or "<root>"
                print(f"       - {err.message} (at {path})")
            ok = False
        else:
            print(f"  ok   {obj}")

    return ok


def validate_file_schemas():
    """Validate file-level YAML examples against generated JSON schemas."""
    schemas_dir = Path("schemas")
    examples_dir = Path("examples/file_schemas")

    files = {
        "autotag": "autotag.yaml",
        "minimum_echemdb": "minimum_echemdb.yaml",
        "source_data": "source_data.yaml",
        "svgdigitizer": "svgdigitizer.yaml",
    }

    ok = True
    for name, example_file in files.items():
        schema_path = schemas_dir / f"{name}.json"
        example_path = examples_dir / example_file

        if not schema_path.exists():
            print(f"  SKIP {name} (schema not found)")
            continue
        if not example_path.exists():
            print(f"  SKIP {name} (example not found)")
            continue

        schema = _load_generated_schema(schema_path)
        with open(example_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        errors = validate_data(data, schema)
        if errors:
            print(f"  FAIL {name}: {len(errors)} error(s)")
            for err in errors[:5]:
                path = "/".join(str(p) for p in err.absolute_path) or "<root>"
                print(f"       - {err.message} (at {path})")
            ok = False
        else:
            print(f"  ok   {name}")

    return ok


def build_package_registry(schemas_dir: Path):
    """Build a referencing registry that includes local Frictionless schemas.

    The generated package JSON schemas use ``$ref: frictionless/dataresource.json``
    to compose with the Frictionless Data Resource standard.  This function
    registers the locally-downloaded Frictionless schemas so that those ``$ref``
    values resolve without network access.

    Downloads the Frictionless schemas on first use if they are not present.

    Schemas are registered under both their raw relative path and the fully
    resolved URI (relative to the package schema's ``$id``) so the
    ``referencing`` library can look them up regardless of base URI.
    """
    from referencing import Registry, Resource

    from mdstools.schema.generate_from_linkml import ensure_frictionless_schemas

    ensure_frictionless_schemas(schemas_dir)

    base_uri = "https://echemdb.github.io/metadata-schema/"
    registry = Registry()
    frictionless_dir = schemas_dir / "frictionless"

    for schema_file in frictionless_dir.glob("*.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            schema = json.load(f)
        resource = Resource.from_contents(schema)
        rel_path = str(schema_file.relative_to(schemas_dir)).replace("\\", "/")
        # Register under both raw relative path and fully resolved URI
        registry = registry.with_resource(rel_path, resource)
        registry = registry.with_resource(base_uri + rel_path, resource)

    return registry


def validate_package_schemas():
    r"""Validate package JSON examples against their generated JSON schemas.

    Uses a local referencing registry to resolve ``$ref`` to the Frictionless
    Data Resource schema stored in ``schemas/frictionless/``.

    EXAMPLES::

        >>> import io, contextlib
        >>> from mdstools.schema.validate_examples import validate_package_schemas
        >>> buf = io.StringIO()
        >>> with contextlib.redirect_stdout(buf):
        ...     result = validate_package_schemas()
        >>> result
        True

    """
    schemas_dir = Path("schemas")
    examples_dir = Path("examples/file_schemas")
    registry = build_package_registry(schemas_dir)

    packages = {
        "echemdb_package": "echemdb_package.json",
        "svgdigitizer_package": "svgdigitizer_package.json",
    }

    ok = True
    for name, example_file in packages.items():
        schema_path = schemas_dir / f"{name}.json"
        example_path = examples_dir / example_file

        if not schema_path.exists():
            print(f"  SKIP {name} (schema not found)")
            continue
        if not example_path.exists():
            print(f"  SKIP {name} (example not found)")
            continue

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        with open(example_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        errors = validate_data(data, schema, registry=registry)
        if errors:
            print(f"  FAIL {name}: {len(errors)} error(s)")
            for err in errors[:5]:
                path = "/".join(str(p) for p in err.absolute_path) or "<root>"
                print(f"       - {err.message} (at {path})")
            ok = False
        else:
            print(f"  ok   {name}")

    return ok


def main():
    """Run validation based on command-line arguments."""
    run_objects = "--objects" in sys.argv or len(sys.argv) == 1
    run_file_schemas = "--file-schemas" in sys.argv or len(sys.argv) == 1
    run_package_schemas = "--package-schemas" in sys.argv or len(sys.argv) == 1

    all_ok = True

    if run_objects:
        print("Validating object examples:")
        if not validate_objects():
            all_ok = False

    if run_file_schemas:
        print("Validating file schema examples:")
        if not validate_file_schemas():
            all_ok = False

    if run_package_schemas:
        print("Validating package schemas:")
        if not validate_package_schemas():
            all_ok = False

    if all_ok:
        print("\nAll validations passed.")
    else:
        print("\nSome validations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
