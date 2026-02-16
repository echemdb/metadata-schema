r"""
Demo: Pydantic models as single source of truth for echemdb metadata.

This script demonstrates how Pydantic models can replace hand-written JSON
Schema files while providing validation and enrichment capabilities.

Run via::

    pixi run -e dev python mdstools/models/demo_pydantic.py

EXAMPLES::

    >>> main()  # doctest: +SKIP

"""

import json

import yaml

from mdstools.models.curation import Curation
from mdstools.models.figure_description import FigureDescription
from mdstools.models.general import Quantity


def separator(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_schema_generation():
    """Show JSON Schema generated from Pydantic models."""
    separator("1. JSON Schema Generation (from Python models)")

    print("--- Quantity ---")
    schema = Quantity.model_json_schema(mode="serialization")
    print(json.dumps(schema, indent=2))

    print("\n--- Curation ---")
    schema = Curation.model_json_schema(mode="serialization")
    print(json.dumps(schema, indent=2))

    print("\n--- FigureDescription ---")
    schema = FigureDescription.model_json_schema(mode="serialization")
    print(json.dumps(schema, indent=2))

    # Show that property names are consistently camelCase
    print("\n--- Property names are always camelCase ---")
    for model_name, model_cls in [
        ("Quantity", Quantity),
        ("Curation", Curation),
        ("FigureDescription", FigureDescription),
    ]:
        schema = model_cls.model_json_schema(mode="serialization")
        props = list(schema.get("properties", {}).keys())
        print(f"  {model_name}: {props}")


def demo_validation():
    """Show validation using Pydantic models."""
    separator("2. Validation (type-safe, with clear error messages)")

    # Valid data
    print("--- Valid YAML data ---")
    yaml_data = {
        "type": "digitized",
        "measurementType": "CV",
        "fields": [
            {"name": "E", "unit": "V", "orientation": "horizontal"},
            {"name": "j", "unit": "uA / cm2", "orientation": "vertical"},
        ],
        "scanRate": {"value": 50, "unit": "mV / s"},
    }
    fd = FigureDescription.model_validate(yaml_data)
    print(f"  type: {fd.type}")
    print(f"  measurement_type: {fd.measurement_type}")
    print(f"  fields: {len(fd.fields)} fields")
    print(f"  scan_rate: {fd.scan_rate.value} {fd.scan_rate.unit}")
    print("  OK - Valid!")

    # Invalid type
    print("\n--- Invalid type value ---")
    try:
        FigureDescription.model_validate({"type": "invalid_type"})
    except Exception as e:
        # Print just the first line for readability
        print(f"  Error: {str(e).splitlines()[0]}")

    # Invalid role in curation
    print("\n--- Invalid role in curation ---")
    try:
        Curation.model_validate(
            {
                "process": [
                    {
                        "role": "janitor",
                        "name": "Jane",
                        "orcid": "https://orcid.org/0",
                    }
                ]
            }
        )
    except Exception as e:
        print(f"  Error: {str(e).splitlines()[0]}")

    # Missing required field
    print("\n--- Missing required field ---")
    try:
        Curation.model_validate({"process": [{"role": "curator"}]})
    except Exception as e:
        print(f"  Error: {str(e).splitlines()[0]}")

    # Extra field (forbidden by EchemdbModel)
    print("\n--- Extra/unknown field ---")
    try:
        FigureDescription.model_validate(
            {"type": "raw", "unknownField": "something"}
        )
    except Exception as e:
        print(f"  Error: {str(e).splitlines()[0]}")


def demo_roundtrip():
    """Show YAML → Model → dict → YAML roundtrip."""
    separator("3. Roundtrip: YAML → Model → YAML")

    yaml_text = """\
type: digitized
measurementType: CV
simultaneousMeasurements:
  - ring current
comment: Data below 0 V was cut off by the x-axis.
fields:
  - name: E
    unit: V
    orientation: horizontal
    reference: RHE
  - name: j
    unit: uA / cm2
    orientation: vertical
  - name: t
    unit: s
scanRate:
  value: 50
  unit: mV / s
"""

    print("--- Input YAML ---")
    print(yaml_text)

    data = yaml.safe_load(yaml_text)
    fd = FigureDescription.model_validate(data)

    print("--- Python object (snake_case access) ---")
    print(f"  fd.type = {fd.type!r}")
    print(f"  fd.measurement_type = {fd.measurement_type!r}")
    print(f"  fd.scan_rate.value = {fd.scan_rate.value}")
    print(f"  fd.scan_rate.unit = {fd.scan_rate.unit!r}")
    print(f"  fd.fields[0].name = {fd.fields[0].name!r}")
    print(f"  fd.fields[0].reference = {fd.fields[0].reference!r}")

    output = fd.model_dump(by_alias=True, exclude_none=True)
    print("\n--- Output dict (camelCase, ready for YAML) ---")
    print(yaml.dump(output, default_flow_style=False))


def demo_enrichment_from_schema():
    """Show how descriptions/examples can be extracted from model schema."""
    separator("4. Enrichment: descriptions & examples from model schema")

    schema = FigureDescription.model_json_schema(mode="serialization")

    print("--- Field descriptions and examples from FigureDescription ---")
    for prop_name, prop_schema in schema.get("properties", {}).items():
        desc = prop_schema.get("description", "")
        example = prop_schema.get("example", "")
        print(f"  {prop_name}:")
        if desc:
            print(f"    description: {desc[:80]}...")
        if example:
            print(f"    example: {example}")

    # Also show nested model descriptions
    print("\n--- Nested $defs have full descriptions too ---")
    for def_name, def_schema in schema.get("$defs", {}).items():
        props = def_schema.get("properties", {})
        if props:
            described = sum(1 for p in props.values() if "description" in p)
            print(f"  {def_name}: {described}/{len(props)} properties have descriptions")


def main():
    demo_schema_generation()
    demo_validation()
    demo_roundtrip()
    demo_enrichment_from_schema()

    separator("Summary")
    print("  Pydantic models provide:")
    print("  1. JSON Schema generation  (replaces hand-written schema_pieces/)")
    print("  2. Validation              (replaces jsonschema + validator.py)")
    print("  3. Naming enforcement      (replaces check_naming.py)")
    print("  4. Enrichment data         (descriptions/examples in one place)")
    print("  5. Type-safe Python API    (IDE autocomplete, refactoring)")
    print()


if __name__ == "__main__":
    main()
