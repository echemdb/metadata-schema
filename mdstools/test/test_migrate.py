"""Unit tests for the metadata migration engine (mdstools.schema.migrate).

The engine is exercised with **dummy** migrations injected into the registry,
so these tests do not depend on any real schema change.
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

import pytest
import yaml

from mdstools.schema.migrate import MetadataMigrator, migrate_file
from mdstools.schema.migrations import UNRELEASED, Migration


def _tagging_step(to_version, tag):
    """A dummy migration that appends *tag* to a ``_steps`` list (non-mutating)."""

    def apply(data):
        result = dict(data)
        result["_steps"] = result.get("_steps", []) + [tag]
        return result

    return Migration(to_version, f"step {tag}", apply)


@pytest.fixture
def registry(monkeypatch):
    """Replace the migration registry; returns a setter for per-test steps."""

    def _set(migrations):
        monkeypatch.setattr("mdstools.schema.migrate.MIGRATIONS", migrations)

    _set([])
    return _set


def test_current_version_defaults_when_absent():
    assert MetadataMigrator({}).current_version == "0.0.0"


def test_no_migrations_restamps_and_preserves(registry):
    result = MetadataMigrator(
        {"echemdbSchemaVersion": "0.7.1", "x": 1}, "0.8.0"
    ).migrated()
    assert result["echemdbSchemaVersion"] == "0.8.0"
    assert result["x"] == 1


def test_patch_only_bump_restamps_without_steps(registry):
    # A step to 0.8.0 exists but the target is only a patch bump, so it is not
    # selected; the version is still restamped to the target.
    registry([_tagging_step("0.8.0", "a")])
    result = MetadataMigrator({"echemdbSchemaVersion": "0.7.1"}, "0.7.2").migrated()
    assert result["echemdbSchemaVersion"] == "0.7.2"
    assert "_steps" not in result


def test_selection_ordering_and_chaining(registry):
    # Register out of order to prove pending() sorts ascending.
    registry([_tagging_step("0.9.0", "b"), _tagging_step("0.8.0", "a")])
    m = MetadataMigrator({"echemdbSchemaVersion": "0.7.1"}, "0.9.0")
    assert [s.to_version for s in m.pending()] == ["0.8.0", "0.9.0"]
    result = m.migrated()
    assert result["_steps"] == ["a", "b"]
    assert result["echemdbSchemaVersion"] == "0.9.0"


def test_partial_target_applies_subset(registry):
    registry([_tagging_step("0.8.0", "a"), _tagging_step("0.9.0", "b")])
    result = MetadataMigrator({"echemdbSchemaVersion": "0.7.1"}, "0.8.0").migrated()
    assert result["_steps"] == ["a"]
    assert result["echemdbSchemaVersion"] == "0.8.0"


def test_unreleased_step_is_skipped_for_concrete_target(registry):
    registry([_tagging_step(UNRELEASED, "pending")])
    result = MetadataMigrator({"echemdbSchemaVersion": "0.7.1"}, "0.8.0").migrated()
    assert "_steps" not in result
    assert result["echemdbSchemaVersion"] == "0.8.0"


def test_input_is_not_mutated(registry):
    registry([_tagging_step("0.8.0", "a")])
    original = {"echemdbSchemaVersion": "0.7.1", "nested": {"k": 1}}
    MetadataMigrator(original, "0.8.0").migrated()
    assert original == {"echemdbSchemaVersion": "0.7.1", "nested": {"k": 1}}


def test_too_new_file_raises(registry):
    with pytest.raises(ValueError, match="newer than the target"):
        MetadataMigrator({"echemdbSchemaVersion": "9.9.9"}, "0.8.0").migrated()


def test_version_ordering_is_numeric_not_lexical(registry):
    # 0.7.10 must be newer than 0.7.2 (lexical string compare would disagree).
    registry([_tagging_step("0.7.10", "a")])
    result = MetadataMigrator({"echemdbSchemaVersion": "0.7.2"}, "0.7.10").migrated()
    assert result["_steps"] == ["a"]


def test_migrate_file_yaml_and_json(registry, tmp_path):
    registry([_tagging_step("0.8.0", "a")])

    yaml_path = tmp_path / "meta.yaml"
    yaml_path.write_text("echemdbSchemaVersion: 0.7.1\nx: 1\n", encoding="utf-8")
    result = migrate_file(yaml_path, "0.8.0")
    assert result["echemdbSchemaVersion"] == "0.8.0"
    assert result["_steps"] == ["a"]

    json_path = tmp_path / "meta.json"
    json_path.write_text(
        json.dumps({"echemdbSchemaVersion": "0.7.1", "x": 1}), encoding="utf-8"
    )
    result = migrate_file(json_path, "0.8.0")
    assert result["echemdbSchemaVersion"] == "0.8.0"
