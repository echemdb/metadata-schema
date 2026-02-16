"""Schema validation utilities for checking metadata against JSON Schema files
or Pydantic models generated from LinkML.

Two validation approaches are available:

1. **JSON Schema validation** via ``validate_metadata()`` – uses jsonschema
   library against resolved JSON Schema files.  Works with any schema.
2. **Pydantic validation** via ``validate_with_pydantic()`` – uses
   auto-generated Pydantic models from LinkML.  Provides richer error
   messages and type coercion.
"""

import importlib
import json
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource

# Map schema names to their (module, class) for Pydantic validation
PYDANTIC_MODELS = {
    "minimum_echemdb": ("mdstools.models.minimum_echemdb", "MinimumEchemdb"),
    "autotag": ("mdstools.models.autotag", "Autotag"),
    "source_data": ("mdstools.models.source_data", "SourceData"),
    "svgdigitizer": ("mdstools.models.svgdigitizer", "Svgdigitizer"),
    "echemdb_package": ("mdstools.models.echemdb_package", "EchemdbPackage"),
    "svgdigitizer_package": ("mdstools.models.svgdigitizer_package", "SvgdigitizerPackage"),
}


def _load_schema(schema_file: Path) -> dict:
    """Load a schema from a JSON or YAML file.

    YAML schema pieces that use the flat definition format (no ``definitions``
    key) are wrapped into a standard JSON Schema structure automatically.
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        if schema_file.suffix in (".yaml", ".yml"):
            raw = yaml.safe_load(f)
            if "definitions" in raw:
                return {"$schema": "http://json-schema.org/draft-07/schema#", **raw}
            # Flat YAML: wrap with definitions and infer entry point
            main_def = "".join(
                part.capitalize() for part in schema_file.stem.split("_")
            )
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "definitions": raw,
            }
            if main_def in raw:
                schema["allOf"] = [{"$ref": f"#/definitions/{main_def}"}]
            return schema
        return json.load(f)


def validate_metadata(data: Any, schema_path: str) -> None:
    r"""
    Validate metadata against a JSON or YAML schema.

    Loads the schema at *schema_path*, resolves ``$ref`` references relative
    to the file, and validates *data* against it.  Raises on the first batch
    of errors (up to 10 are reported).

    :param data: Metadata object to validate
    :param schema_path: Path to JSON or YAML schema file
    :raises FileNotFoundError: If the schema file does not exist
    :raises ValueError: If validation fails

    EXAMPLES::

        Validating correct metadata passes silently::

            >>> from mdstools.schema.validator import validate_metadata
            >>> from mdstools.metadata.metadata import Metadata
            >>> data = Metadata.from_yaml('examples/file_schemas/autotag.yaml').data
            >>> validate_metadata(data, 'schemas/autotag.json')

        Validation errors raise ``ValueError`` with details::

            >>> invalid_data = {'curation': 'not a dict'}
            >>> try:
            ...     validate_metadata(invalid_data, 'schemas/autotag.json')
            ... except ValueError as e:
            ...     'validation failed' in str(e).lower()
            True

        Missing schema file raises ``FileNotFoundError``::

            >>> try:
            ...     validate_metadata({}, 'nonexistent_schema.json')
            ... except FileNotFoundError:
            ...     print('Schema file not found')
            Schema file not found

    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    schema = _load_schema(schema_file)

    base_uri = schema_file.resolve().as_uri()
    resource = Resource.from_contents(schema)
    registry = Registry().with_resource(base_uri, resource)

    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, registry=registry)

    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    if errors:
        details = []
        for error in errors[:10]:
            path = "/".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"- {error.message} (at {path})")
        detail_text = "\n".join(details)
        raise ValueError(
            "Schema validation failed with " f"{len(errors)} error(s):\n{detail_text}"
        )


def validate_with_pydantic(data: Any, schema_name: str) -> Any:
    r"""
    Validate metadata using auto-generated Pydantic models from LinkML.

    Returns the validated Pydantic model instance on success.  Raises
    ``ValueError`` on validation failure with detailed error messages.

    :param data: Metadata dict to validate
    :param schema_name: Schema name (e.g. 'minimum_echemdb', 'autotag')
    :returns: Validated Pydantic model instance
    :raises ValueError: If validation fails or schema_name is unknown

    EXAMPLES::

        Validating correct metadata returns a Pydantic model::

            >>> import yaml
            >>> from mdstools.schema.validator import validate_with_pydantic
            >>> with open('examples/file_schemas/minimum_echemebd.yaml') as f:
            ...     data = yaml.safe_load(f)
            >>> model = validate_with_pydantic(data, 'minimum_echemdb')
            >>> model.source.citationKey
            'engstfeld_2018_polycrystalline_17743'

        Validation errors raise ``ValueError``::

            >>> try:
            ...     validate_with_pydantic({'curation': 'not a dict'}, 'minimum_echemdb')
            ... except ValueError as e:
            ...     'validation failed' in str(e).lower()
            True

        Unknown schema name raises ``ValueError``::

            >>> try:
            ...     validate_with_pydantic({}, 'nonexistent')
            ... except ValueError as e:
            ...     print('Unknown schema')
            Unknown schema

    """
    if schema_name not in PYDANTIC_MODELS:
        raise ValueError(
            f"Unknown schema '{schema_name}'. "
            f"Available: {', '.join(sorted(PYDANTIC_MODELS.keys()))}"
        )

    module_path, class_name = PYDANTIC_MODELS[schema_name]
    mod = importlib.import_module(module_path)
    model_cls = getattr(mod, class_name)

    try:
        return model_cls.model_validate(data)
    except Exception as exc:
        raise ValueError(f"Pydantic validation failed: {exc}") from exc
