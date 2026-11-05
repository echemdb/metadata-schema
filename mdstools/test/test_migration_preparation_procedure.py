"""Tests for the cleaningProcedure -> preparationProcedure migration step.

Covers the transform directly (correctness, idempotency, merging into an
existing preparation procedure) and end-to-end through the engine against the
current JSON schema using the fixture under ``tests/migrations/``.
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

import pytest
import yaml
from packaging.version import Version

from mdstools.schema.migrate import MetadataMigrator
from mdstools.schema.migrations import (
    MIGRATIONS,
    UNRELEASED,
    Migration,
    _cleaning_procedure_to_preparation_procedure,
)
from mdstools.schema.validator import validate_metadata

FIXTURE = "tests/migrations/minimum_echemdb_cleaning_procedure.yaml"
SCHEMA = "schemas/minimum_echemdb.json"
TEXT = "Storing in highly concentrated KOH and boiling in Milli-Q water."


def _cell(**fields):
    return {"system": {"electrochemicalCell": dict(fields)}}


def test_registry_registers_step():
    """The step is registered once, unreleased or stamped to a version > 0.8.4."""
    steps = [m for m in MIGRATIONS if "cleaningProcedure" in m.description]
    assert len(steps) == 1
    assert steps[0].apply is _cleaning_procedure_to_preparation_procedure
    to_version = steps[0].to_version
    assert to_version == UNRELEASED or Version(to_version) > Version("0.8.4")


def test_transform_moves_string_into_description_list():
    """The free-text string becomes a single-item description list."""
    after = _cleaning_procedure_to_preparation_procedure(
        _cell(type="H-cell", cleaningProcedure=TEXT)
    )
    cell = after["system"]["electrochemicalCell"]
    assert "cleaningProcedure" not in cell
    assert cell["preparationProcedure"] == {"description": [TEXT]}
    assert cell["type"] == "H-cell"


def test_transform_is_idempotent():
    """Applying the transform twice is a no-op."""
    once = _cleaning_procedure_to_preparation_procedure(_cell(cleaningProcedure=TEXT))
    assert _cleaning_procedure_to_preparation_procedure(once) == once


def test_transform_noop_without_cleaning_procedure():
    """Documents without the old field are returned unchanged."""
    for doc in ({}, {"system": {}}, _cell(type="H-cell")):
        assert _cleaning_procedure_to_preparation_procedure(doc) == doc


def test_transform_drops_empty_value():
    """An empty/null cleaningProcedure is removed without creating an empty object."""
    for empty in (None, ""):
        after = _cleaning_procedure_to_preparation_procedure(
            _cell(cleaningProcedure=empty)
        )
        assert after["system"]["electrochemicalCell"] == {}


def test_transform_appends_to_existing_preparation_procedure():
    """An existing preparationProcedure is extended, not overwritten."""
    before = _cell(
        cleaningProcedure=TEXT,
        preparationProcedure={"url": "https://doi.org/x", "description": ["Step 1"]},
    )
    prep = _cleaning_procedure_to_preparation_procedure(before)["system"][
        "electrochemicalCell"
    ]["preparationProcedure"]
    assert prep == {"url": "https://doi.org/x", "description": ["Step 1", TEXT]}


def test_transform_does_not_duplicate_existing_step():
    """The text is not appended twice if it is already listed."""
    before = _cell(cleaningProcedure=TEXT, preparationProcedure={"description": [TEXT]})
    prep = _cleaning_procedure_to_preparation_procedure(before)["system"][
        "electrochemicalCell"
    ]["preparationProcedure"]
    assert prep == {"description": [TEXT]}


def test_transform_does_not_mutate_input():
    """The transform does not mutate its input document."""
    before = _cell(cleaningProcedure=TEXT)
    _cleaning_procedure_to_preparation_procedure(before)
    assert before == _cell(cleaningProcedure=TEXT)


def test_fixture_fails_current_schema_but_validates_after_migration(monkeypatch):
    """The old-layout fixture fails the current schema but validates once migrated."""
    with open(FIXTURE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    with pytest.raises(ValueError):
        validate_metadata(data, SCHEMA)

    # Register under a concrete version so the engine applies it (UNRELEASED
    # steps are skipped for concrete targets until a release stamps them).
    monkeypatch.setattr(
        "mdstools.schema.migrate.MIGRATIONS",
        [Migration("0.9.0", "cell", _cleaning_procedure_to_preparation_procedure)],
    )
    migrated = MetadataMigrator(data, "0.9.0").migrated()

    cell = migrated["system"]["electrochemicalCell"]
    assert "cleaningProcedure" not in cell
    assert cell["preparationProcedure"] == {"description": [TEXT]}
    assert migrated["echemdbSchemaVersion"] == "0.9.0"
    validate_metadata(migrated, SCHEMA)
