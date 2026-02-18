"""Generate JSON Schemas and Pydantic models from LinkML YAML models.

All metadata schemas are defined as LinkML YAML files under linkml/.
This module generates JSON Schema files and Pydantic models from those
definitions.

Usage:
    python mdstools/schema/generate_from_linkml.py [--json-schema] [--pydantic] [--all]
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
import subprocess
import sys
import urllib.request
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LINKML_DIR = REPO_ROOT / "linkml"
SCHEMAS_DIR = REPO_ROOT / "schemas"
MODELS_DIR = REPO_ROOT / "mdstools" / "models"

# Frictionless schemas to download on demand
FRICTIONLESS_SCHEMAS = {
    "datapackage.json": "https://datapackage.org/profiles/2.0/datapackage.json",
    "dataresource.json": "https://datapackage.org/profiles/2.0/dataresource.json",
}


def ensure_frictionless_schemas(schemas_dir: Path = None):
    """Download Frictionless Data Package schemas if not already present.

    The schemas are stored in ``schemas/frictionless/`` and are gitignored.
    They are only downloaded when missing, so subsequent runs are offline.
    """
    if schemas_dir is None:
        schemas_dir = SCHEMAS_DIR
    frictionless_dir = schemas_dir / "frictionless"
    frictionless_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in FRICTIONLESS_SCHEMAS.items():
        dest = frictionless_dir / filename
        if dest.exists():
            continue
        print(f"  Downloading {url} -> {dest} ...")
        req = urllib.request.Request(url, headers={"User-Agent": "mdstools"})
        with urllib.request.urlopen(req) as resp:
            dest.write_bytes(resp.read())
        # Validate it's proper JSON
        with open(dest, "r", encoding="utf-8") as f:
            json.load(f)
        print(f"  OK {filename}")


# Main models to generate
MAIN_MODELS = [
    "minimum_echemdb",
    "autotag",
    "source_data",
    "svgdigitizer",
    "echemdb_package",
    "svgdigitizer_package",
]


# Package schemas that need Frictionless Data Package composition
PACKAGE_SCHEMAS = {
    "echemdb_package": {
        "package_class": "EchemdbPackage",
        "resource_class": "EchemdbResource",
    },
    "svgdigitizer_package": {
        "package_class": "SvgdigitizerPackage",
        "resource_class": "SvgdigitizerResource",
    },
}

# Relative path from schemas/ to the local Frictionless dataresource schema
FRICTIONLESS_RESOURCE_REF = "https://datapackage.org/profiles/2.0/dataresource.json"


def _postprocess_package_schema(schema: dict, defs: dict, model_name: str):
    """Compose package schemas with Frictionless Data Package standard.

    For package schemas (echemdb_package, svgdigitizer_package), modify the
    resource items to use ``allOf`` combining the local Frictionless data
    resource schema with the LinkML-generated resource definition.  This
    allows Frictionless properties (name, path, format, encoding, …) to pass
    validation alongside our custom ``metadata`` property.
    """
    if model_name not in PACKAGE_SCHEMAS:
        return

    info = PACKAGE_SCHEMAS[model_name]
    resource_class = info["resource_class"]
    package_class = info["package_class"]

    # Allow additional (Frictionless) properties on Package and Resource defs
    if package_class in defs:
        defs[package_class]["additionalProperties"] = True
    if resource_class in defs:
        defs[resource_class]["additionalProperties"] = True

    # Wrap resource items with allOf: [Frictionless, ours]
    def _wrap_resource_items(props: dict):
        res = props.get("resources", {})
        items = res.get("items")
        if isinstance(items, dict) and "$ref" in items:
            res["items"] = {
                "allOf": [
                    {"$ref": FRICTIONLESS_RESOURCE_REF},
                    items,
                ]
            }

    # Update both root-level properties and $defs entry
    _wrap_resource_items(schema.get("properties", {}))
    if package_class in defs:
        _wrap_resource_items(defs[package_class].get("properties", {}))


def generate_json_schemas():
    """Generate JSON Schema files from LinkML models."""
    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    ensure_frictionless_schemas(SCHEMAS_DIR)

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
            check=False,
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

        # Post-process: compose package schemas with Frictionless Data Package
        # schemas so that standard resource properties (name, path, format, etc.)
        # are accepted during validation.
        _postprocess_package_schema(schema, defs, model_name)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"  OK {output_file.name}")

    print(f"\nGenerated {len(MAIN_MODELS)} JSON Schema files in {SCHEMAS_DIR}")


def _postprocess_pydantic(code: str) -> str:
    """Apply fixes to generated Pydantic code for compatibility.

    - Prepend GPL license header
    - Add coerce_numbers_to_str=True so Quantity.value accepts numeric YAML values
    - Change extra="forbid" to extra="allow" so top-level models accept additional fields
    """
    # Prepend license header
    license_header = (
        "# ********************************************************************\n"
        "#  This file is part of mdstools.\n"
        "#\n"
        "#        Copyright (C) 2026 Albert Engstfeld\n"
        "#\n"
        "#  mdstools is free software: you can redistribute it and/or modify\n"
        "#  it under the terms of the GNU General Public License as published by\n"
        "#  the Free Software Foundation, either version 3 of the License, or\n"
        "#  (at your option) any later version.\n"
        "#\n"
        "#  mdstools is distributed in the hope that it will be useful,\n"
        "#  but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
        "#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
        "#  GNU General Public License for more details.\n"
        "#\n"
        "#  You should have received a copy of the GNU General Public License\n"
        "#  along with mdstools. If not, see <https://www.gnu.org/licenses/>.\n"
        "# ********************************************************************\n"
    )
    code = license_header + code

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
            check=False,
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
