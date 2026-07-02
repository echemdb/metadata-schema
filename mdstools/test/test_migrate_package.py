"""Tests for migrating data packages (mdstools.schema.migrate).

A package embeds metadata under ``resources[].metadata.<key>`` with a
per-resource version; the same migration steps are mapped over each resource.
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

import contextlib
import io
import json
from pathlib import Path

from mdstools.schema.migrate import _is_package, migrate_document, migrate_file
from mdstools.schema.migrations import (
    Migration,
    _move_temperature_to_operation_parameters,
)
from mdstools.schema.validate_examples import build_package_registry, validate_data

FIXTURE = "tests/migrations/echemdb_package_pre_0_8_0.json"
PACKAGE_SCHEMA = "schemas/echemdb_package.json"


def _register_temperature_step(monkeypatch):
    """Register the temperature step under a concrete 0.8.0 version."""
    monkeypatch.setattr(
        "mdstools.schema.migrate.MIGRATIONS",
        [Migration("0.8.0", "temp", _move_temperature_to_operation_parameters)],
    )


def _load(path):
    """Load a JSON file."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def test_is_package_detection():
    """A dict with a resources list is a package; other shapes are not."""
    assert _is_package({"resources": [{"name": "r"}]}) is True
    assert _is_package({"resources": []}) is True
    assert _is_package({"system": {}, "experimental": {}}) is False
    assert _is_package({"resources": {"not": "a list"}}) is False
    assert _is_package("not a dict") is False


def test_migrate_document_migrates_each_resource(monkeypatch):
    """Each resource's embedded metadata is migrated; the envelope is kept."""
    _register_temperature_step(monkeypatch)
    package = _load(FIXTURE)
    migrated = migrate_document(package, "0.8.0")

    echemdb = migrated["resources"][0]["metadata"]["echemdb"]
    assert "temperature" not in echemdb["system"]["electrolyte"]
    assert echemdb["experimental"]["operationParameters"]["temperature"] == {
        "unit": "K",
        "value": 298.15,
    }
    assert echemdb["echemdbSchemaVersion"] == "0.8.0"

    # Frictionless envelope is untouched.
    assert migrated["resources"][0]["name"] == package["resources"][0]["name"]
    assert migrated["resources"][0]["path"] == package["resources"][0]["path"]


def test_input_package_not_mutated(monkeypatch):
    """Migrating a package does not mutate the input."""
    _register_temperature_step(monkeypatch)
    package = _load(FIXTURE)
    migrate_document(package, "0.8.0")
    electrolyte = package["resources"][0]["metadata"]["echemdb"]["system"][
        "electrolyte"
    ]
    assert "temperature" in electrolyte  # original still in the old location


def test_plain_document_not_treated_as_package(monkeypatch):
    """A document without a resources list is migrated directly."""
    _register_temperature_step(monkeypatch)
    doc = {
        "echemdbSchemaVersion": "0.7.1",
        "system": {"electrolyte": {"temperature": {"value": 298}}},
    }
    migrated = migrate_document(doc, "0.8.0")
    assert "temperature" not in migrated["system"]["electrolyte"]
    assert migrated["experimental"]["operationParameters"]["temperature"] == {
        "value": 298
    }


def test_package_fails_current_schema_then_validates_after_migration(monkeypatch):
    """The pre-move package fails the package schema but validates once migrated."""
    _register_temperature_step(monkeypatch)
    package = _load(FIXTURE)
    schema = _load(PACKAGE_SCHEMA)
    with contextlib.redirect_stdout(io.StringIO()):
        registry = build_package_registry(Path("schemas"))

    # As-is (old temperature location) it fails package validation.
    assert validate_data(package, schema, registry=registry)

    migrated = migrate_document(package, "0.8.0")
    assert not validate_data(migrated, schema, registry=registry)


def test_migrate_file_handles_json_package(monkeypatch):
    """migrate_file migrates a JSON data package."""
    _register_temperature_step(monkeypatch)
    migrated = migrate_file(FIXTURE, "0.8.0")
    echemdb = migrated["resources"][0]["metadata"]["echemdb"]
    assert echemdb["experimental"]["operationParameters"]["temperature"]["unit"] == "K"
