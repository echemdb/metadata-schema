"""Tests for registered migration steps (mdstools.schema.migrations).

Covers the 0.8.0 temperature move directly (transform correctness,
idempotency, conflict) and end-to-end through the engine against the current
JSON schema, plus MetadataMigrator.validate.
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
from packaging.version import Version

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


def test_registry_registers_temperature_step():
    """The temperature step is registered exactly once with the right transform.

    Its ``to_version`` is the :data:`UNRELEASED` placeholder while the change is
    in development and the stamped concrete version (>= 0.8.0) once a release
    finalizes it, so we accept either rather than pinning to one — otherwise the
    test would fail on every release commit and on ``main`` thereafter.
    """
    steps = [m for m in MIGRATIONS if "temperature" in m.description.lower()]
    assert len(steps) == 1
    assert steps[0].apply is _move_temperature_to_operation_parameters
    to_version = steps[0].to_version
    assert to_version == UNRELEASED or Version(to_version) >= Version("0.8.0")


def test_transform_moves_temperature():
    """Temperature is moved from electrolyte to operationParameters."""
    before = {
        "system": {"electrolyte": {"type": "aqueous", "temperature": {"value": 298}}},
    }
    after = _move_temperature_to_operation_parameters(before)
    assert after["experimental"]["operationParameters"]["temperature"] == {"value": 298}
    assert "temperature" not in after["system"]["electrolyte"]
    assert after["system"]["electrolyte"]["type"] == "aqueous"


def test_transform_is_idempotent():
    """Applying the transform twice is a no-op."""
    before = {"system": {"electrolyte": {"temperature": {"value": 298}}}}
    once = _move_temperature_to_operation_parameters(before)
    twice = _move_temperature_to_operation_parameters(once)
    assert twice == once


def test_transform_noop_without_temperature():
    """A document without a temperature is returned unchanged."""
    doc = {"system": {"electrolyte": {"type": "aqueous"}}}
    assert _move_temperature_to_operation_parameters(doc) == doc


def test_transform_does_not_mutate_input():
    """The transform does not mutate its input document."""
    before = {"system": {"electrolyte": {"temperature": {"value": 298}}}}
    _move_temperature_to_operation_parameters(before)
    assert before == {"system": {"electrolyte": {"temperature": {"value": 298}}}}


def test_transform_conflict_raises():
    """Temperature in both locations with different values raises."""
    before = {
        "system": {"electrolyte": {"temperature": {"value": 298}}},
        "experimental": {"operationParameters": {"temperature": {"value": 300}}},
    }
    with pytest.raises(ValueError, match="both"):
        _move_temperature_to_operation_parameters(before)


def test_transform_conflict_same_value_is_noop():
    """Temperature in both locations with the same value is not a conflict."""
    same = {"value": 298}
    before = {
        "system": {"electrolyte": {"temperature": same}},
        "experimental": {"operationParameters": {"temperature": same}},
    }
    after = _move_temperature_to_operation_parameters(before)
    assert after["experimental"]["operationParameters"]["temperature"] == same
    assert "temperature" not in after["system"]["electrolyte"]


def test_fixture_fails_current_schema_but_validates_after_migration(monkeypatch):
    """The pre-move fixture fails the current schema but validates once migrated."""
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
    validate_metadata(migrated, SCHEMA)


def test_validate_passes_on_valid_document():
    """MetadataMigrator.validate returns the validated document."""
    with open(AUTOTAG_EXAMPLE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    result = MetadataMigrator(data).validate("autotag")
    assert result["experimental"]["operationParameters"]["temperature"]["unit"] == "K"


def test_validate_raises_on_invalid_document():
    """An invalid document fails schema validation."""
    with pytest.raises(ValueError, match="validation failed"):
        MetadataMigrator({}, "0.8.0").validate("minimum_echemdb")


def test_validate_unknown_schema_name_raises():
    """An unknown schema name is rejected."""
    with pytest.raises(ValueError, match="Unknown schema"):
        MetadataMigrator({}).validate("does_not_exist")


def test_validate_detects_dangling_instrument_reference():
    """A control.instrument that names no listed instrument is caught."""
    with open(AUTOTAG_EXAMPLE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    broken = deepcopy(data)
    broken["experimental"]["operationParameters"]["massTransport"]["rotation"][
        "control"
    ]["instrument"] = "NotInList"
    with pytest.raises(ValueError, match="Instrument reference"):
        MetadataMigrator(data).validate("autotag", data=broken)


def test_rate_without_instrument_passes_reference_check():
    """A controlled parameter without a named instrument does not fail."""
    no_control = {
        "experimental": {
            "instrumentation": [],
            "operationParameters": {
                "massTransport": {
                    "rotation": {"rate": {"value": 1600, "unit": "1 / min"}}
                }
            },
        }
    }
    assert not validate_instrument_references(no_control)

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
    assert not validate_instrument_references(control_without_instrument)
