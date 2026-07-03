"""Regression tests for YAML metadata loading (issue #123).

Unquoted YAML dates (``date: 2021-07-09``) must load as plain strings so that
string-typed schema fields validate; ``yaml.safe_load`` would turn them into
``datetime.date`` objects and fail validation.
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
import textwrap

from mdstools.schema.validator import _load_data, validate_metadata

UNQUOTED_DATE_YAML = textwrap.dedent("""
    curation:
      process:
        - role: curator
          name: Jane Doe
          date: 2021-07-09
    """)


def test_unquoted_dates_load_as_strings(tmp_path):
    """Unquoted YAML dates are loaded as plain strings, not datetime.date."""
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text(UNQUOTED_DATE_YAML, encoding="utf-8")

    data = _load_data(metadata_file)

    assert data["curation"]["process"][0]["date"] == "2021-07-09"


def test_unquoted_dates_validate_as_strings(tmp_path):
    """A document with an unquoted date validates against a string-typed field."""
    metadata_file = tmp_path / "metadata.yaml"
    metadata_file.write_text(UNQUOTED_DATE_YAML, encoding="utf-8")

    schema_file = tmp_path / "schema.json"
    schema_file.write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "curation": {
                        "type": "object",
                        "properties": {
                            "process": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": ["string", "null"]}
                                    },
                                },
                            }
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    validate_metadata(_load_data(metadata_file), str(schema_file))
