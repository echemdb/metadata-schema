"""Tests for registered migration steps (mdstools.schema.migrations).

Covers the 0.8.0 temperature move directly (transform correctness,
idempotency, conflict) and end-to-end through the engine against the current
JSON schema.
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

from mdstools.schema.migrate import MetadataMigrator
from mdstools.schema.migrations import (
    MIGRATIONS,
    UNRELEASED,
    Migration,
    _move_temperature_to_operation_parameters,
)
from mdstools.schema.validator import validate_metadata

FIXTURE = "tests/migrations/minimum_echemdb_pre_0_8_0.yaml"
SCHEMA = "schemas/minimum_echemdb.json"


def test_registry_registers_temperature_step_as_unreleased():
    steps = [m for m in MIGRATIONS if "temperature" in m.description.lower()]
    assert len(steps) == 1
    assert steps[0].to_version == UNRELEASED
    assert steps[0].apply is _move_temperature_to_operation_parameters


def test_transform_moves_temperature():
    before = {
        "system": {"electrolyte": {"type": "aqueous", "temperature": {"value": 298}}},
    }
    after = _move_temperature_to_operation_parameters(before)
    assert after["experimental"]["operationParameters"]["temperature"] == {"value": 298}
    assert "temperature" not in after["system"]["electrolyte"]
    # electrolyte otherwise preserved
    assert after["system"]["electrolyte"]["type"] == "aqueous"


def test_transform_is_idempotent():
    before = {"system": {"electrolyte": {"temperature": {"value": 298}}}}
    once = _move_temperature_to_operation_parameters(before)
    twice = _move_temperature_to_operation_parameters(once)
    assert twice == once


def test_transform_noop_without_temperature():
    doc = {"system": {"electrolyte": {"type": "aqueous"}}}
    assert _move_temperature_to_operation_parameters(doc) == doc


def test_transform_does_not_mutate_input():
    before = {"system": {"electrolyte": {"temperature": {"value": 298}}}}
    _move_temperature_to_operation_parameters(before)
    assert before == {"system": {"electrolyte": {"temperature": {"value": 298}}}}


def test_transform_conflict_raises():
    before = {
        "system": {"electrolyte": {"temperature": {"value": 298}}},
        "experimental": {"operationParameters": {"temperature": {"value": 300}}},
    }
    with pytest.raises(ValueError, match="both"):
        _move_temperature_to_operation_parameters(before)


def test_transform_conflict_same_value_is_noop():
    same = {"value": 298}
    before = {
        "system": {"electrolyte": {"temperature": same}},
        "experimental": {"operationParameters": {"temperature": same}},
    }
    after = _move_temperature_to_operation_parameters(before)
    assert after["experimental"]["operationParameters"]["temperature"] == same
    assert "temperature" not in after["system"]["electrolyte"]


def test_fixture_fails_current_schema_but_validates_after_migration(monkeypatch):
    with open(FIXTURE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    # As-is (pre-0.8.0 layout) it violates the current schema.
    with pytest.raises(ValueError):
        validate_metadata(data, SCHEMA)

    # Register the step under a concrete version so the engine applies it
    # (UNRELEASED steps are skipped for concrete targets until a release stamps
    # them). This mirrors what finalize_migrations does at release time.
    monkeypatch.setattr(
        "mdstools.schema.migrate.MIGRATIONS",
        [Migration("0.8.0", "temp", _move_temperature_to_operation_parameters)],
    )
    migrated = MetadataMigrator(data, "0.8.0").migrated()

    assert "temperature" not in migrated["system"]["electrolyte"]
    assert migrated["experimental"]["operationParameters"]["temperature"] == {
        "value": 298.15,
        "unit": "K",
    }
    assert migrated["echemdbSchemaVersion"] == "0.8.0"
    # Now it validates against the current schema.
    validate_metadata(migrated, SCHEMA)
