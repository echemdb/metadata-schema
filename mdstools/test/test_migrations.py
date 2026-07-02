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

from copy import deepcopy

import pytest
import yaml

from mdstools.schema.migrate import MetadataMigrator
from mdstools.schema.migrations import (
    MIGRATIONS,
    UNRELEASED,
    Migration,
    _move_temperature_to_operation_parameters,
)
from mdstools.schema.validator import validate_instrument_references, validate_metadata

FIXTURE = "tests/migrations/minimum_echemdb_pre_0_8_0.yaml"
SCHEMA = "schemas/minimum_echemdb.json"
AUTOTAG_EXAMPLE = "examples/file_schemas/autotag.yaml"


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


# --- MetadataMigrator.validate() -------------------------------------------


def test_validate_passes_on_valid_document():
    with open(AUTOTAG_EXAMPLE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    # Returns the validated (migrated) document without raising.
    result = MetadataMigrator(data).validate("autotag")
    assert result["experimental"]["operationParameters"]["temperature"]["unit"] == "K"


def test_validate_raises_on_invalid_document():
    with pytest.raises(ValueError, match="validation failed"):
        MetadataMigrator({}, "0.8.0").validate("minimum_echemdb")


def test_validate_unknown_schema_name_raises():
    with pytest.raises(ValueError, match="Unknown schema"):
        MetadataMigrator({}).validate("does_not_exist")


def test_validate_detects_dangling_instrument_reference():
    with open(AUTOTAG_EXAMPLE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    broken = deepcopy(data)
    broken["experimental"]["operationParameters"]["massTransport"]["rotation"][
        "control"
    ]["instrument"] = "NotInList"
    with pytest.raises(ValueError, match="Instrument reference"):
        MetadataMigrator(data).validate("autotag", data=broken)


def test_rate_without_instrument_passes_reference_check():
    # A rotation rate reported without the controlling instrument (e.g. taken
    # from a manuscript) must not fail: the check only fires when an instrument
    # is actually named.
    no_control = {
        "experimental": {
            "instrumentation": [],
            "operationParameters": {
                "massTransport": {"rotation": {"rate": {"value": 1600, "unit": "1 / min"}}}
            },
        }
    }
    assert validate_instrument_references(no_control) == []

    control_without_instrument = {
        "experimental": {
            "instrumentation": [],
            "operationParameters": {
                "massTransport": {
                    "rotation": {
                        "rate": {"value": 1600},
                        "control": {"description": "rotator not reported"},
                    }
                }
            },
        }
    }
    assert validate_instrument_references(control_without_instrument) == []
