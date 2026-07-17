"""Verify that committed generated artifacts match a fresh regeneration.

The JSON Schemas in ``schemas/`` and the Pydantic models in
``mdstools/models/`` are generated from the LinkML sources in ``linkml/``.
These tests regenerate both into a temporary directory and compare them with
the committed files, so that stale artifacts are caught locally instead of by
the ``git diff --exit-code -- schemas mdstools/models`` check in CI.

If a test fails, run ``pixi run generate-all`` and commit the result.
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

import difflib

import pytest

from mdstools.schema.generate_from_linkml import (
    MAIN_MODELS,
    MODELS_DIR,
    SCHEMAS_DIR,
    generate_json_schemas,
    generate_pydantic_models,
)

REGENERATE_HINT = "Run `pixi run generate-all` and commit the changes."


def _diff(expected: str, actual: str, name: str) -> str:
    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=f"committed/{name}",
            tofile=f"regenerated/{name}",
        )
    )


def test_json_schemas_up_to_date(tmp_path):
    """Committed JSON Schemas match a fresh regeneration from LinkML."""
    generate_json_schemas(output_dir=tmp_path, ensure_frictionless=False)

    for model_name in MAIN_MODELS:
        name = f"{model_name}.json"
        committed = (SCHEMAS_DIR / name).read_text(encoding="utf-8")
        regenerated = (tmp_path / name).read_text(encoding="utf-8")
        message = f"schemas/{name} is stale. {REGENERATE_HINT}\n" + _diff(
            committed, regenerated, name
        )
        assert committed == regenerated, message


def test_pydantic_models_up_to_date(tmp_path):
    """Committed Pydantic models match a fresh regeneration from LinkML."""
    # Committed models are black-formatted (see the generate-models pixi
    # task), so the raw gen-pydantic output must be formatted before
    # comparison. black is only available in the dev environment.
    black = pytest.importorskip("black")

    generate_pydantic_models(output_dir=tmp_path)

    for model_name in MAIN_MODELS:
        name = f"{model_name}.py"
        committed = (MODELS_DIR / name).read_text(encoding="utf-8")
        regenerated = (tmp_path / name).read_text(encoding="utf-8")
        regenerated = black.format_str(regenerated, mode=black.Mode())
        message = f"mdstools/models/{name} is stale. {REGENERATE_HINT}\n" + _diff(
            committed, regenerated, name
        )
        assert committed == regenerated, message
