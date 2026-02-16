#!/usr/bin/env python
r"""
Validate example YAML files against YAML schema pieces.

Loads YAML schema pieces, wraps them into proper JSON Schema structures,
and validates example data against them.

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

import sys
from pathlib import Path

import jsonschema
import yaml


def load_yaml_schema(schema_path: Path) -> dict:
    """Load a YAML schema piece and wrap it into a valid JSON Schema."""
    with open(schema_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    schema_stem = schema_path.stem
    # Convert snake_case to PascalCase for the main definition
    main_def = "".join(part.capitalize() for part in schema_stem.split("_"))

    if "definitions" in raw:
        # Already has definitions (e.g., package schemas)
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            **raw,
        }
    elif "type" in raw or "properties" in raw:
        # Standard schema (e.g., schema.yaml) — wrap as single definition
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": {main_def: raw},
            "allOf": [{"$ref": f"#/definitions/{main_def}"}],
        }
    else:
        # Flat YAML format — top-level keys are definitions
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "definitions": raw,
        }
        if main_def in raw:
            schema["allOf"] = [{"$ref": f"#/definitions/{main_def}"}]

    return schema


def build_registry(schema_dir: Path):
    """Build a referencing registry with all schema pieces for $ref resolution.

    Schemas are registered under multiple URI variants so that relative ``$ref``
    strings (``./``, ``../``) resolve correctly regardless of the referencing
    schema's location.
    """
    import posixpath

    from referencing import Registry, Resource

    registry = Registry()
    all_schemas = {}

    for schema_file in schema_dir.rglob("*.yaml"):
        schema = load_yaml_schema(schema_file)
        rel_path = str(schema_file.relative_to(schema_dir)).replace("\\", "/")
        all_schemas[rel_path] = schema

    for rel_path, schema in all_schemas.items():
        resource = Resource.from_contents(schema)
        # Register under multiple URI forms to support relative $ref resolution:
        # ./general/url.yaml, general/url.yaml, ../general/url.yaml (from system/)
        variants = set()
        variants.add("./" + rel_path)
        variants.add(rel_path)
        variants.add("./" + rel_path.replace(".yaml", ".json"))
        variants.add(rel_path.replace(".yaml", ".json"))
        # Also register from parent-relative paths (e.g., ../general/x.yaml from system/)
        for other_path in all_schemas:
            other_dir = posixpath.dirname(other_path)
            if other_dir:
                # Path from other_dir to rel_path
                relative = posixpath.relpath(rel_path, other_dir)
                variants.add(relative)
                variants.add(relative.replace(".yaml", ".json"))
        for uri in variants:
            registry = registry.with_resource(uri, resource)

    return registry


def validate_data(data: dict, schema: dict, registry=None) -> list:
    """Validate data against a schema, return list of error messages."""
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, registry=registry)
    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    return errors


def validate_objects():
    """Validate individual YAML examples against their schema pieces."""
    schema_dir = Path("schemas/schema_pieces")
    examples_dir = Path("examples/objects")
    registry = build_registry(schema_dir)

    objects = [
        "curation",
        "eln",
        "experimental",
        "figure_description",
        "projects",
        "source",
        "system",
    ]

    ok = True
    for obj in objects:
        schema_path = schema_dir / f"{obj}.yaml"
        example_path = examples_dir / f"{obj}.yaml"

        if not schema_path.exists():
            print(f"  SKIP {obj} (schema not found)")
            continue
        if not example_path.exists():
            print(f"  SKIP {obj} (example not found)")
            continue

        schema = load_yaml_schema(schema_path)
        with open(example_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        errors = validate_data(data, schema, registry=registry)
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
    """Validate file-level YAML examples against their schema pieces."""
    schema_dir = Path("schemas/schema_pieces")
    examples_dir = Path("examples/file_schemas")
    registry = build_registry(schema_dir)

    # Map schema names to their example files.
    # Package schemas (echemdb_package, svgdigitizer_package) are excluded here
    # because they reference external $refs (datapackage.org) that require network
    # access. They are validated separately via the validate-package-schemas task.
    files = {
        "autotag": "autotag.yaml",
        "minimum_echemdb": "minimum_echemdb.yaml",
        "source_data": "source_data.yaml",
        "svgdigitizer": "svgdigitizer.yaml",
    }

    ok = True
    for name, example_file in files.items():
        schema_path = schema_dir / f"{name}.yaml"
        example_path = examples_dir / example_file

        if not schema_path.exists():
            print(f"  SKIP {name} (schema not found)")
            continue
        if not example_path.exists():
            print(f"  SKIP {name} (example not found)")
            continue

        schema = load_yaml_schema(schema_path)
        with open(example_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

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

    all_ok = True

    if run_objects:
        print("Validating object examples:")
        if not validate_objects():
            all_ok = False

    if run_file_schemas:
        print("Validating file schema examples:")
        if not validate_file_schemas():
            all_ok = False

    if all_ok:
        print("\nAll validations passed.")
    else:
        print("\nSome validations failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
