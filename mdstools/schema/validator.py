"""Schema validation utilities for checking metadata against JSON Schema files
or Pydantic models generated from LinkML.

Three validation approaches are available:

1. **Remote validation** via ``validate()`` – fetches the JSON Schema from
   the `metadata-schema repository <https://github.com/echemdb/metadata-schema>`_
   on GitHub and validates a dict or file against it.  Convenience wrappers
   such as ``validate_svgdigitizer()`` are provided for each schema.
2. **Local JSON Schema validation** via ``validate_metadata()`` – uses
   jsonschema library against a local JSON Schema file.
3. **Pydantic validation** via ``validate_with_pydantic()`` – uses
   auto-generated Pydantic models from LinkML.  Provides richer error
   messages and type coercion.
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

import importlib
import json
import urllib.request
from pathlib import Path
from typing import Any

import jsonschema
import yaml
from referencing import Registry, Resource

# Known schema names and their filenames in the repository
KNOWN_SCHEMAS = {
    "autotag": "autotag.json",
    "minimum_echemdb": "minimum_echemdb.json",
    "source_data": "source_data.json",
    "svgdigitizer": "svgdigitizer.json",
    "echemdb_package": "echemdb_package.json",
    "svgdigitizer_package": "svgdigitizer_package.json",
}

# Package schemas that reference Frictionless Data Resource via $ref
_PACKAGE_SCHEMAS = {"echemdb_package", "svgdigitizer_package"}

_SCHEMA_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "echemdb/metadata-schema/{version}/schemas/{filename}"
)

# Frictionless schemas referenced by package schemas
_FRICTIONLESS_URLS = {
    "https://datapackage.org/profiles/2.0/datapackage.json",
    "https://datapackage.org/profiles/2.0/dataresource.json",
}

# Map schema names to their (module, class) for Pydantic validation
PYDANTIC_MODELS = {
    "minimum_echemdb": ("mdstools.models.minimum_echemdb", "MinimumEchemdb"),
    "autotag": ("mdstools.models.autotag", "Autotag"),
    "source_data": ("mdstools.models.source_data", "SourceData"),
    "svgdigitizer": ("mdstools.models.svgdigitizer", "Svgdigitizer"),
    "echemdb_package": ("mdstools.models.echemdb_package", "EchemdbPackage"),
    "svgdigitizer_package": (
        "mdstools.models.svgdigitizer_package",
        "SvgdigitizerPackage",
    ),
}


def _load_schema(schema_file: Path) -> dict:
    r"""
    Load a JSON schema file.

    EXAMPLES::

        >>> from pathlib import Path
        >>> from mdstools.schema.validator import _load_schema
        >>> schema = _load_schema(Path('schemas/autotag.json'))
        >>> '$schema' in schema
        True
    """
    with open(schema_file, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_metadata(data: Any, schema_path: str) -> None:
    r"""
    Validate metadata against a JSON Schema.

    Loads the schema at *schema_path*, resolves ``$ref`` references relative
    to the file, and validates *data* against it.  Raises on the first batch
    of errors (up to 10 are reported).

    :param data: Metadata object to validate
    :param schema_path: Path to JSON Schema file
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
            >>> with open('examples/file_schemas/minimum_echemdb.yaml') as f:
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


# ---------------------------------------------------------------------------
# Public remote-validation API
# ---------------------------------------------------------------------------


def _load_data(data: Any) -> dict:
    r"""Load metadata from a file path (YAML/JSON) or return a dict as-is.

    EXAMPLES::

        >>> from mdstools.schema.validator import _load_data
        >>> d = _load_data('examples/file_schemas/autotag.yaml')
        >>> isinstance(d, dict)
        True

        >>> _load_data({'key': 'value'})
        {'key': 'value'}

    """
    if isinstance(data, (str, Path)):
        path = Path(data)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(f)
            if path.suffix == ".json":
                return json.load(f)
            raise ValueError(f"Unsupported file extension: {path.suffix}")
    if isinstance(data, dict):
        return data
    raise TypeError(f"Expected dict, str, or Path, got {type(data).__name__}")


def _fetch_remote_schema(schema_name: str, version: str = None) -> dict:
    r"""Download a JSON schema from the metadata-schema GitHub repository.

    :param schema_name: One of the keys in :data:`KNOWN_SCHEMAS`.
    :param version: Git tag or branch (default ``"main"``).
    :returns: Parsed JSON schema dict.

    EXAMPLES::

        >>> from mdstools.schema.validator import _fetch_remote_schema  # doctest: +REMOTE_DATA
        >>> schema = _fetch_remote_schema('autotag')  # doctest: +REMOTE_DATA
        >>> '$defs' in schema  # doctest: +REMOTE_DATA
        True

    """
    if schema_name not in KNOWN_SCHEMAS:
        raise ValueError(
            f"Unknown schema '{schema_name}'. "
            f"Available: {', '.join(sorted(KNOWN_SCHEMAS))}"
        )
    if version is None:
        from mdstools import __version__

        version = __version__
    filename = KNOWN_SCHEMAS[schema_name]
    url = _SCHEMA_BASE_URL.format(version=version, filename=filename)
    req = urllib.request.Request(url, headers={"User-Agent": "mdstools"})
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


def _build_remote_registry(schema_name: str) -> Registry:
    """Build a ``referencing.Registry`` for remote validation.

    For package schemas the Frictionless Data Resource schema is downloaded
    and registered so that ``$ref`` links resolve correctly.
    """
    registry = Registry()
    if schema_name not in _PACKAGE_SCHEMAS:
        return registry

    for url in _FRICTIONLESS_URLS:
        req = urllib.request.Request(url, headers={"User-Agent": "mdstools"})
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            schema = json.loads(resp.read().decode("utf-8"))
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(url, resource)
    return registry


def validate(data: Any, schema: str = "echemdb_package", version: str = None) -> None:
    r"""Validate metadata against a schema from the metadata-schema repository.

    Fetches the JSON schema from
    ``https://raw.githubusercontent.com/echemdb/metadata-schema/<version>/schemas/``
    and validates *data* against it.

    :param data: Metadata dict, or path to a YAML/JSON file.
    :param schema: Schema name — one of ``'autotag'``, ``'minimum_echemdb'``,
        ``'source_data'``, ``'svgdigitizer'``, ``'echemdb_package'``,
        ``'svgdigitizer_package'``.
    :param version: Git tag or branch name.  Defaults to the installed
        package version (i.e. the matching release tag).  Pass ``'main'``
        to validate against the latest development schemas.
    :raises FileNotFoundError: If *data* is a path that does not exist.
    :raises ValueError: If validation fails or *schema* is unknown.

    EXAMPLES::

        Validate a local YAML file against the remote autotag schema::

            >>> from mdstools.schema.validator import validate  # doctest: +REMOTE_DATA
            >>> validate('examples/file_schemas/autotag.yaml', schema='autotag')  # doctest: +REMOTE_DATA

        Validate a dict::

            >>> import yaml  # doctest: +REMOTE_DATA
            >>> with open('examples/file_schemas/minimum_echemdb.yaml') as f:  # doctest: +REMOTE_DATA
            ...     data = yaml.safe_load(f)
            >>> validate(data, schema='minimum_echemdb')  # doctest: +REMOTE_DATA

        Validate against a specific version (git tag)::

            >>> validate('examples/file_schemas/autotag.yaml', schema='autotag', version='0.5.1')  # doctest: +REMOTE_DATA

        Invalid data raises ``ValueError``::

            >>> try:  # doctest: +REMOTE_DATA
            ...     validate({'curation': 'not a dict'}, schema='autotag')
            ... except ValueError as e:
            ...     'validation failed' in str(e).lower()
            True

    """
    loaded = _load_data(data)
    schema_dict = _fetch_remote_schema(schema, version=version)
    registry = _build_remote_registry(schema)

    validator_cls = jsonschema.validators.validator_for(schema_dict)
    validator = validator_cls(schema_dict, registry=registry)

    errors = sorted(validator.iter_errors(loaded), key=lambda err: err.path)
    if errors:
        details = []
        for error in errors[:10]:
            path = "/".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"- {error.message} (at {path})")
        detail_text = "\n".join(details)
        raise ValueError(
            f"Schema validation failed with {len(errors)} error(s):\n{detail_text}"
        )


def validate_autotag(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``autotag`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_autotag  # doctest: +REMOTE_DATA
        >>> validate_autotag('examples/file_schemas/autotag.yaml')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="autotag", version=version)


def validate_minimum_echemdb(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``minimum_echemdb`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_minimum_echemdb  # doctest: +REMOTE_DATA
        >>> validate_minimum_echemdb('examples/file_schemas/minimum_echemdb.yaml')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="minimum_echemdb", version=version)


def validate_source_data(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``source_data`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_source_data  # doctest: +REMOTE_DATA
        >>> validate_source_data('examples/file_schemas/source_data.yaml')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="source_data", version=version)


def validate_svgdigitizer(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``svgdigitizer`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_svgdigitizer  # doctest: +REMOTE_DATA
        >>> validate_svgdigitizer('examples/file_schemas/svgdigitizer.yaml')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="svgdigitizer", version=version)


def validate_echemdb_package(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``echemdb_package`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_echemdb_package  # doctest: +REMOTE_DATA
        >>> validate_echemdb_package('examples/file_schemas/echemdb_package.json')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="echemdb_package", version=version)


def validate_svgdigitizer_package(data: Any, version: str = None) -> None:
    r"""Validate metadata against the ``svgdigitizer_package`` schema.

    See :func:`validate` for parameter details.

    EXAMPLES::

        >>> from mdstools.schema.validator import validate_svgdigitizer_package  # doctest: +REMOTE_DATA
        >>> validate_svgdigitizer_package('examples/file_schemas/svgdigitizer_package.json')  # doctest: +REMOTE_DATA

    """
    validate(data, schema="svgdigitizer_package", version=version)
