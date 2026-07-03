"""Upgrade echemdb metadata across schema versions.

The engine is **format-agnostic**: it operates on plain dicts. Reading a file
into a dict is handled at the boundary (:func:`migrate_file`); writing back in
place — which must preserve YAML comments — is added in a later stage.

Migrations are declared in :mod:`mdstools.schema.migrations`. Only *breaking*
changes need a step; additive changes are backward-compatible. See
``schema_update.md`` for the design rationale.
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
from copy import deepcopy
from pathlib import Path
from typing import Any

from packaging.version import Version

from mdstools.schema.migrations import MIGRATIONS, UNRELEASED
from mdstools.schema.validator import (
    KNOWN_SCHEMAS,
    _load_data,
    validate_instrument_references,
    validate_metadata,
)

#: Field carrying the schema version inside a metadata document.
VERSION_FIELD = "echemdbSchemaVersion"

#: Directory holding the generated local JSON schemas.
SCHEMAS_DIR = Path("schemas")


def _resolve_schema_path(schema: str) -> Path:
    """Resolve a schema *name* or path to a local JSON Schema file.

    Accepts a known schema name (e.g. ``"minimum_echemdb"``) or a path to a
    ``.json`` schema file.

    EXAMPLES::

        >>> from mdstools.schema.migrate import _resolve_schema_path
        >>> _resolve_schema_path("minimum_echemdb").as_posix()
        'schemas/minimum_echemdb.json'

    """
    path = Path(schema)
    if path.suffix == ".json":
        return path
    if schema not in KNOWN_SCHEMAS:
        raise ValueError(
            f"Unknown schema '{schema}'. "
            f"Available: {', '.join(sorted(KNOWN_SCHEMAS))}"
        )
    return SCHEMAS_DIR / KNOWN_SCHEMAS[schema]


def _resolve_latest(target_version: str) -> str:
    """Resolve ``"latest"`` to the installed package version.

    EXAMPLES::

        >>> from mdstools.schema.migrate import _resolve_latest
        >>> _resolve_latest("0.8.0")
        '0.8.0'
        >>> from mdstools import __version__
        >>> _resolve_latest("latest") == __version__
        True

    """
    if target_version == "latest":
        from mdstools import __version__

        return __version__
    return target_version


class MetadataMigrator:
    r"""Upgrade a single echemdb metadata dict across schema versions.

    :param data: The metadata document. Copied on construction; the input is
        never mutated.
    :param target_version: Version to migrate to, or ``"latest"`` (the installed
        package version).

    EXAMPLES:

        With no migrations registered the version is simply restamped and the
        payload is preserved::

            >>> from mdstools.schema.migrate import MetadataMigrator
            >>> m = MetadataMigrator({"echemdbSchemaVersion": "0.7.1", "x": 1},
            ...                      target_version="0.8.0")
            >>> m.current_version
            '0.7.1'
            >>> result = m.migrated()
            >>> result["echemdbSchemaVersion"]
            '0.8.0'
            >>> result["x"]
            1

        A file newer than the target is refused rather than silently
        downgraded::

            >>> MetadataMigrator({"echemdbSchemaVersion": "9.9.9"},
            ...                  target_version="0.8.0").migrated()
            Traceback (most recent call last):
                ...
            ValueError: metadata version 9.9.9 is newer than the target 0.8.0; upgrade mdstools to migrate this file.

    """

    def __init__(self, data: dict, target_version: str = "latest"):
        self.data = deepcopy(data)
        self.target_version = _resolve_latest(target_version)

    @property
    def current_version(self) -> str:
        """Version declared in the document (``"0.0.0"`` if absent)."""
        return self.data.get(VERSION_FIELD, "0.0.0")

    def pending(self) -> list:
        """Migrations to apply, in ascending target-version order.

        A migration is selected when its ``to_version`` lies in
        ``(current_version, target_version]``.

        Migrations still marked :data:`UNRELEASED` are skipped here: their real
        version is unknown until a release is cut, so they are not part of any
        concrete target yet. The release helper (a later stage) rewrites the
        placeholder to the concrete version before it can be selected.
        """
        low = Version(self.current_version)
        high = Version(self.target_version)
        selected = [
            migration
            for migration in MIGRATIONS
            if migration.to_version != UNRELEASED
            and low < Version(migration.to_version) <= high
        ]
        return sorted(selected, key=lambda migration: Version(migration.to_version))

    def migrated(self) -> dict:
        """Return a new dict upgraded to the target version.

        The input is never mutated. Each step stamps its own ``to_version``;
        the final value is the target (covering patch-only bumps with no steps).
        """
        current = Version(self.current_version)
        target = Version(self.target_version)
        if current > target:
            raise ValueError(
                f"metadata version {self.current_version} is newer than the "
                f"target {self.target_version}; upgrade mdstools to migrate "
                f"this file."
            )

        data = deepcopy(self.data)
        for migration in self.pending():
            data = migration.apply(data)
            data[VERSION_FIELD] = migration.to_version
        data[VERSION_FIELD] = self.target_version
        return data

    def validate(self, schema: str, data: dict = None) -> dict:
        r"""Validate a document against a local target schema.

        Runs both the JSON Schema check and the instrument-reference check
        (which JSON Schema cannot express). Validates :meth:`migrated` by
        default, i.e. the *result* of the migration.

        The instrument-reference check only fires when an instrument is actually
        named: a controlled parameter given without a ``control`` block (or with
        a ``control`` that omits ``instrument``) is fine — e.g. a rotation rate
        taken from a manuscript where the rotator was not reported.

        :param schema: Schema name (e.g. ``"svgdigitizer"``) or path to a
            ``.json`` schema file.
        :param data: Document to validate; defaults to :meth:`migrated`.
        :returns: The validated document.
        :raises ValueError: if schema or instrument-reference validation fails.
        """
        if data is None:
            data = self.migrated()

        validate_metadata(data, str(_resolve_schema_path(schema)))

        reference_errors = validate_instrument_references(data)
        if reference_errors:
            details = "\n".join(f"- {message}" for message in reference_errors)
            raise ValueError(
                "Instrument reference validation failed with "
                f"{len(reference_errors)} error(s):\n{details}"
            )
        return data

    def validate_input(self, schema: str) -> None:
        r"""Validate the *source* document against its declared version's schema.

        Fetches the schema for :attr:`current_version` from the metadata-schema
        repository (by git tag) and validates the original, un-migrated input
        against it. Useful as a pre-flight check that the input is a
        well-formed document of the version it claims to be.

        Requires network access.

        :param schema: Schema name (e.g. ``"svgdigitizer"``).
        :raises ValueError: if the input does not validate against its declared
            version's schema.

        EXAMPLES::

            >>> from mdstools.schema.migrate import MetadataMigrator  # doctest: +REMOTE_DATA
            >>> import yaml  # doctest: +REMOTE_DATA
            >>> data = yaml.safe_load(open("examples/file_schemas/autotag.yaml"))  # doctest: +REMOTE_DATA
            >>> MetadataMigrator(data).validate_input("autotag")  # doctest: +REMOTE_DATA, +SKIP

        """
        from mdstools.schema.validator import validate as _remote_validate

        _remote_validate(self.data, schema=schema, version=self.current_version)


def _is_package(data: Any) -> bool:
    """True if *data* looks like a (Frictionless) data package.

    Detection is intentionally **structural**, not a Frictionless schema
    validation: routing must work offline and must recognise *old or invalid*
    packages (the very inputs the migrator exists to fix). A data package is
    defined by its ``resources`` array — the required top-level property of the
    pinned datapackage profile — so that is what we key on. Full Frictionless
    validation happens in the validation step, not here.
    """
    return (
        isinstance(data, dict)
        and isinstance(data.get("resources"), list)
        and all(isinstance(resource, dict) for resource in data["resources"])
    )


def _migrate_package(package: dict, target_version: str) -> dict:
    """Migrate the embedded metadata of every resource in a data package.

    In a package the metadata is nested under ``resources[].metadata.<key>``
    (e.g. ``metadata.echemdb``) and each resource carries its own
    ``echemdbSchemaVersion``. Every metadata sub-document that declares a
    version is migrated with :class:`MetadataMigrator`, reusing the exact same
    steps as loose files. The Frictionless envelope is left untouched.
    """
    result = deepcopy(package)
    for resource in result.get("resources", []):
        if not isinstance(resource, dict):
            continue
        metadata = resource.get("metadata")
        if not isinstance(metadata, dict):
            continue
        for key, document in metadata.items():
            if isinstance(document, dict) and VERSION_FIELD in document:
                metadata[key] = MetadataMigrator(document, target_version).migrated()
    return result


def migrate_document(data: Any, target_version: str = "latest") -> dict:
    """Migrate a metadata document *or* a data package.

    A data package (a dict with a ``resources`` list) is migrated per resource;
    any other document is migrated directly. Returns a new dict; the input is
    not mutated.

    :param data: A metadata dict or a data-package dict.
    :param target_version: Version to migrate to, or ``"latest"``.
    """
    if _is_package(data):
        return _migrate_package(data, target_version)
    return MetadataMigrator(data, target_version).migrated()


def _roundtrip_yaml():
    """A ruamel YAML instance configured for comment-preserving round-trips."""
    from ruamel.yaml import YAML

    yaml = YAML()  # round-trip mode by default
    yaml.preserve_quotes = True
    yaml.width = 4096  # do not wrap long scalars (URLs, bibdata, ...)
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def _load_roundtrip(path: Path) -> Any:
    """Load a file for in-place writing.

    YAML is loaded with the ruamel round-trip loader so comments and layout
    survive; JSON is loaded plainly (JSON has no comments).
    """
    path = Path(path)
    if path.suffix in (".yaml", ".yml"):
        with open(path, encoding="utf-8") as handle:
            return _roundtrip_yaml().load(handle)
    return _load_data(path)


def _dump_data(data: Any, path: Path) -> None:
    """Write *data* back to *path* as YAML or JSON, chosen by extension.

    YAML is written with the ruamel round-trip dumper, so comments carried on a
    :class:`ruamel.yaml.comments.CommentedMap` are preserved.
    """
    path = Path(path)
    if path.suffix in (".yaml", ".yml"):
        with open(path, "w", encoding="utf-8") as handle:
            _roundtrip_yaml().dump(data, handle)
    elif path.suffix == ".json":
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    else:
        raise ValueError(f"Unsupported file extension: {path.suffix}")


def migrate_file(
    path: Any, target_version: str = "latest", in_place: bool = False
) -> dict:
    """Load a metadata file, migrate it, and optionally overwrite it.

    Handles both loose metadata files and data packages (via
    :func:`migrate_document`). When *in_place* is true the file is rewritten in
    its original format; YAML is round-tripped through ruamel so curator
    comments and layout are preserved.

    :param path: Path to a YAML or JSON metadata file.
    :param target_version: Version to migrate to, or ``"latest"``.
    :param in_place: When true, write the migrated document back to *path*.
    :returns: The migrated metadata (or package) dict.
    """
    if in_place:
        data = _load_roundtrip(path)
        result = migrate_document(data, target_version)
        _dump_data(result, Path(path))
        return result
    return migrate_document(_load_data(path), target_version)
