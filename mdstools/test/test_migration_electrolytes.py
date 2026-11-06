"""Tests for the electrolyte -> electrolytes migration step (#129).

Covers the transform directly (correctness, key order, idempotency, conflicts)
and end-to-end through the engine against the current JSON schema using the
fixture under ``tests/migrations/``, including an in-place YAML migration that
keeps comments.
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

import shutil

import pytest
import yaml
from packaging.version import Version

from mdstools.schema.migrate import MetadataMigrator, migrate_file
from mdstools.schema.migrations import (
    DEFAULT_ELECTROLYTE_NAME,
    MIGRATIONS,
    UNRELEASED,
    Migration,
    _electrolyte_to_electrolytes,
)
from mdstools.schema.validator import validate_metadata

FIXTURE = "tests/migrations/minimum_echemdb_single_electrolyte.yaml"
SCHEMA = "schemas/minimum_echemdb.json"


def _register(monkeypatch):
    """Register the step under a concrete version so the engine applies it.

    UNRELEASED steps are skipped for concrete targets until a release stamps
    them; this mirrors what finalize_migrations does at release time.
    """
    monkeypatch.setattr(
        "mdstools.schema.migrate.MIGRATIONS",
        [Migration("0.9.0", "electrolytes", _electrolyte_to_electrolytes)],
    )


def test_registry_registers_step():
    """The step is registered once, unreleased or stamped to a version > 0.8.4."""
    steps = [m for m in MIGRATIONS if m.apply is _electrolyte_to_electrolytes]
    assert len(steps) == 1
    to_version = steps[0].to_version
    assert to_version == UNRELEASED or Version(to_version) > Version("0.8.4")


def test_transform_wraps_electrolyte_into_named_list():
    """The single electrolyte becomes the only, named entry of the list."""
    before = {"system": {"electrolyte": {"type": "aqueous", "ph": {"value": 1}}}}
    after = _electrolyte_to_electrolytes(before)
    assert after["system"] == {
        "electrolytes": [
            {"name": DEFAULT_ELECTROLYTE_NAME, "type": "aqueous", "ph": {"value": 1}}
        ]
    }


def test_transform_keeps_key_order():
    """``electrolytes`` takes the position of ``electrolyte``; ``name`` comes first."""
    before = {
        "system": {
            "type": "electrochemical",
            "electrolyte": {"type": "aqueous"},
            "electrodes": [],
        }
    }
    after = _electrolyte_to_electrolytes(before)
    assert list(after["system"]) == ["type", "electrolytes", "electrodes"]
    assert list(after["system"]["electrolytes"][0]) == ["name", "type"]


def test_transform_keeps_existing_name():
    """An electrolyte that already has a name keeps it."""
    before = {"system": {"electrolyte": {"name": "catholyte", "type": "aqueous"}}}
    after = _electrolyte_to_electrolytes(before)
    assert after["system"]["electrolytes"] == [{"name": "catholyte", "type": "aqueous"}]


def test_transform_is_idempotent():
    """Applying the transform twice is a no-op."""
    once = _electrolyte_to_electrolytes(
        {"system": {"electrolyte": {"type": "aqueous"}}}
    )
    assert _electrolyte_to_electrolytes(once) == once


def test_transform_noop_without_electrolyte():
    """Documents without the old field are returned unchanged."""
    for doc in ({}, {"system": {}}, {"system": {"electrolytes": []}}):
        assert _electrolyte_to_electrolytes(doc) == doc


def test_transform_drops_null_electrolyte():
    """A null electrolyte is removed without creating an empty list."""
    after = _electrolyte_to_electrolytes({"system": {"electrolyte": None}})
    assert after == {"system": {}}


def test_transform_conflict_raises():
    """Both ``electrolyte`` and ``electrolytes`` present is ambiguous."""
    before = {
        "system": {
            "electrolyte": {"type": "aqueous"},
            "electrolytes": [{"name": "anolyte", "type": "aqueous"}],
        }
    }
    with pytest.raises(ValueError, match="both"):
        _electrolyte_to_electrolytes(before)


def test_transform_rejects_non_mapping():
    """A list or scalar under ``electrolyte`` is not silently converted."""
    with pytest.raises(ValueError, match="not a mapping"):
        _electrolyte_to_electrolytes({"system": {"electrolyte": [{"type": "aqueous"}]}})


def test_transform_does_not_mutate_input():
    """The transform does not mutate its input document."""
    before = {"system": {"electrolyte": {"type": "aqueous"}}}
    _electrolyte_to_electrolytes(before)
    assert before == {"system": {"electrolyte": {"type": "aqueous"}}}


def test_fixture_fails_current_schema_but_validates_after_migration(monkeypatch):
    """The old-layout fixture fails the current schema but validates once migrated."""
    with open(FIXTURE, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    with pytest.raises(ValueError):
        validate_metadata(data, SCHEMA)

    _register(monkeypatch)
    migrated = MetadataMigrator(data, "0.9.0").migrated()

    system = migrated["system"]
    assert "electrolyte" not in system
    assert len(system["electrolytes"]) == 1
    entry = system["electrolytes"][0]
    assert entry["name"] == DEFAULT_ELECTROLYTE_NAME
    assert {k: v for k, v in entry.items() if k != "name"} == data["system"][
        "electrolyte"
    ]
    assert migrated["echemdbSchemaVersion"] == "0.9.0"
    validate_metadata(migrated, SCHEMA)


def test_in_place_yaml_migration_keeps_comments(monkeypatch, tmp_path):
    """Migrating the fixture in place keeps its comments and validates."""
    target = tmp_path / "metadata.yaml"
    shutil.copy(FIXTURE, target)
    _register(monkeypatch)

    migrate_file(str(target), target_version="0.9.0", in_place=True)

    text = target.read_text(encoding="utf-8")
    assert "# required: aqueous = aq, non-aqueous=naq, solid=s, gas=g" in text
    reloaded = yaml.safe_load(text)
    assert reloaded["system"]["electrolytes"][0]["name"] == DEFAULT_ELECTROLYTE_NAME
    validate_metadata(reloaded, SCHEMA)
