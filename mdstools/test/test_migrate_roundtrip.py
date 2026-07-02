"""Tests for in-place migration and comment-preserving YAML round-trips.

Writing a migrated YAML file back in place must keep curator comments (header,
inline, and on list items); JSON is rewritten plainly.
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

from mdstools.schema.migrate import migrate_file
from mdstools.schema.migrations import (
    Migration,
    _move_temperature_to_operation_parameters,
)

PRE_MOVE_YAML = """\
# curated by hand - keep these notes
echemdbSchemaVersion: 0.7.1
system:
  electrolyte:
    type: aqueous  # aqueous electrolyte
    ph:
      value: 13
    temperature:
      value: 298.15
      unit: K
experimental:
  tags:
    - BCV  # base cyclic voltammetry
"""


@pytest.fixture
def temperature_registry(monkeypatch):
    monkeypatch.setattr(
        "mdstools.schema.migrate.MIGRATIONS",
        [Migration("0.8.0", "temp", _move_temperature_to_operation_parameters)],
    )


def test_in_place_yaml_preserves_comments_and_migrates(temperature_registry, tmp_path):
    path = tmp_path / "meta.yaml"
    path.write_text(PRE_MOVE_YAML, encoding="utf-8")

    result = migrate_file(path, "0.8.0", in_place=True)

    text = path.read_text(encoding="utf-8")
    # Comments survived the round-trip.
    assert "# curated by hand - keep these notes" in text
    assert "# aqueous electrolyte" in text
    assert "# base cyclic voltammetry" in text

    # And the structure was migrated on disk.
    reloaded = yaml.safe_load(text)
    assert "temperature" not in reloaded["system"]["electrolyte"]
    assert reloaded["experimental"]["operationParameters"]["temperature"] == {
        "value": 298.15,
        "unit": "K",
    }
    assert reloaded["echemdbSchemaVersion"] == "0.8.0"
    # Return value matches what was written.
    assert result["echemdbSchemaVersion"] == "0.8.0"


def test_non_in_place_does_not_touch_file(temperature_registry, tmp_path):
    path = tmp_path / "meta.yaml"
    path.write_text(PRE_MOVE_YAML, encoding="utf-8")

    migrate_file(path, "0.8.0", in_place=False)

    # File is unchanged; only the returned dict is migrated.
    assert path.read_text(encoding="utf-8") == PRE_MOVE_YAML


def test_in_place_json_round_trip(temperature_registry, tmp_path):
    path = tmp_path / "meta.json"
    path.write_text(
        json.dumps(
            {
                "echemdbSchemaVersion": "0.7.1",
                "system": {"electrolyte": {"temperature": {"value": 298, "unit": "K"}}},
            }
        ),
        encoding="utf-8",
    )

    migrate_file(path, "0.8.0", in_place=True)

    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert "temperature" not in reloaded["system"]["electrolyte"]
    assert reloaded["experimental"]["operationParameters"]["temperature"] == {
        "value": 298,
        "unit": "K",
    }
    assert reloaded["echemdbSchemaVersion"] == "0.8.0"
