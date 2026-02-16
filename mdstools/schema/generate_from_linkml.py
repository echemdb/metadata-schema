"""Generate JSON Schemas and Pydantic models from LinkML YAML models.

This replaces the old resolver.py approach. Instead of manually resolving
$ref references in JSON Schema files, we now generate everything from
LinkML model definitions.

Usage:
    python mdstools/schema/generate_from_linkml.py [--json-schema] [--pydantic] [--all]
"""

import json
import subprocess
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LINKML_DIR = REPO_ROOT / "linkml"
SCHEMAS_DIR = REPO_ROOT / "schemas"
MODELS_DIR = REPO_ROOT / "mdstools" / "models"

# Main models to generate
MAIN_MODELS = [
    "minimum_echemdb",
    "autotag",
    "source_data",
    "svgdigitizer",
    "echemdb_package",
    "svgdigitizer_package",
]


def generate_json_schemas():
    """Generate JSON Schema files from LinkML models."""
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)

    for model_name in MAIN_MODELS:
        linkml_file = LINKML_DIR / f"{model_name}.yaml"
        output_file = SCHEMAS_DIR / f"{model_name}.json"

        if not linkml_file.exists():
            print(f"  SKIP {model_name} (LinkML file not found: {linkml_file})")
            continue

        print(f"  Generating {output_file.name} from {linkml_file.name}...")
        result = subprocess.run(
            ["gen-json-schema", str(linkml_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ERROR generating {model_name}:")
            print(result.stderr)
            sys.exit(1)

        # Parse and re-serialize for consistent formatting
        schema = json.loads(result.stdout)

        # Add schema metadata
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"
        schema["$id"] = f"https://echemdb.github.io/metadata-schema/{model_name}"

        # Post-process: add fieldMapping to DataDescription if present
        # (fieldMapping is a free-form dict not expressible in LinkML)
        defs = schema.get("$defs", {})
        if "DataDescription" in defs:
            dd = defs["DataDescription"]
            props = dd.setdefault("properties", {})
            props["fieldMapping"] = {
                "type": "object",
                "description": (
                    "Mapping from original column headers in the data file to "
                    "standardized field names. Keys are the original headers "
                    "(use ' / ' to join multi-line headers), values are the "
                    "standardized names."
                ),
                "additionalProperties": {"type": "string"},
            }

        # Post-process: Quantity.value and Quantity.unit must accept numbers
        # because YAML parses numeric values as int/float, not string.
        if "Quantity" in defs:
            q_props = defs["Quantity"].get("properties", {})
            if "value" in q_props:
                q_props["value"]["type"] = ["string", "number", "null"]
            if "unit" in q_props:
                q_props["unit"]["type"] = ["string", "number", "null"]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"  OK {output_file.name}")

    print(f"\nGenerated {len(MAIN_MODELS)} JSON Schema files in {SCHEMAS_DIR}")


def _postprocess_pydantic(code: str) -> str:
    """Apply fixes to generated Pydantic code for compatibility.

    - Add coerce_numbers_to_str=True so Quantity.value accepts numeric YAML values
    - Change extra="forbid" to extra="allow" so top-level models accept additional fields
    """
    # Allow numeric values to be coerced to strings (Quantity.value, Quantity.unit)
    code = code.replace(
        'extra = "forbid",',
        'extra = "allow",\n        coerce_numbers_to_str = True,',
    )
    return code


def generate_pydantic_models():
    """Generate Pydantic models from LinkML models."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Create __init__.py if it doesn't exist
    init_file = MODELS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            '"""Auto-generated Pydantic models from LinkML schemas."""\n',
            encoding="utf-8",
        )

    for model_name in MAIN_MODELS:
        linkml_file = LINKML_DIR / f"{model_name}.yaml"
        output_file = MODELS_DIR / f"{model_name}.py"

        if not linkml_file.exists():
            print(f"  SKIP {model_name} (LinkML file not found: {linkml_file})")
            continue

        print(f"  Generating {output_file.name} from {linkml_file.name}...")
        result = subprocess.run(
            ["gen-pydantic", str(linkml_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"  ERROR generating {model_name}:")
            print(result.stderr)
            sys.exit(1)

        code = _postprocess_pydantic(result.stdout)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(code)

        print(f"  OK {output_file.name}")

    print(f"\nGenerated {len(MAIN_MODELS)} Pydantic model files in {MODELS_DIR}")


def main():
    """Run all generators."""
    args = sys.argv[1:]

    if not args or "--all" in args:
        do_json_schema = True
        do_pydantic = True
    else:
        do_json_schema = "--json-schema" in args
        do_pydantic = "--pydantic" in args

    if do_json_schema:
        print("=== Generating JSON Schemas from LinkML ===")
        generate_json_schemas()
        print()

    if do_pydantic:
        print("=== Generating Pydantic Models from LinkML ===")
        generate_pydantic_models()
        print()

    print("Done.")


if __name__ == "__main__":
    main()
