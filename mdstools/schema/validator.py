"""Schema validation utilities."""

import json
from pathlib import Path
from typing import Any

import jsonschema


def validate_metadata(data: Any, schema_path: str) -> None:
    """
    Validate metadata against a JSON schema.

    :param data: Metadata object to validate
    :param schema_path: Path to JSON schema file
    :raises FileNotFoundError: If the schema file does not exist
    :raises ValueError: If validation fails
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    base_uri = schema_file.resolve().as_uri()
    resolver = jsonschema.RefResolver(base_uri=base_uri, referrer=schema)
    validator_cls = jsonschema.validators.validator_for(schema)
    validator = validator_cls(schema, resolver=resolver)

    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    if errors:
        details = []
        for error in errors[:10]:
            path = "/".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"- {error.message} (at {path})")
        detail_text = "\n".join(details)
        raise ValueError(
            "Schema validation failed with "
            f"{len(errors)} error(s):\n{detail_text}"
        )
