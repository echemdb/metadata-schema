"""Tests for the release-time migration finalizer (finalize_migrations)."""

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
from packaging.version import Version

from mdstools.schema.finalize_migrations import (
    PLACEHOLDER,
    finalize_migrations,
)
from mdstools.schema.migrations import MIGRATIONS, UNRELEASED

UNRELEASED_SNIPPET = """\
UNRELEASED = "UNRELEASED"

MIGRATIONS = [
    Migration(
        to_version=UNRELEASED,
        description="move something",
        apply=_step,
    ),
]
"""


def _write(tmp_path, text):
    """Write *text* to a temporary migrations module and return its path."""
    path = tmp_path / "migrations.py"
    path.write_text(text, encoding="utf-8")
    return path


def test_finalize_rewrites_placeholder(tmp_path):
    """A single placeholder is rewritten; the constant is left intact."""
    path = _write(tmp_path, UNRELEASED_SNIPPET)
    count = finalize_migrations("0.8.0", migrations_path=path)
    assert count == 1

    text = path.read_text(encoding="utf-8")
    assert 'to_version="0.8.0"' in text
    assert PLACEHOLDER not in text
    assert 'UNRELEASED = "UNRELEASED"' in text


def test_finalize_rewrites_multiple_placeholders(tmp_path):
    """All placeholders present are rewritten."""
    text = UNRELEASED_SNIPPET + "\n" + UNRELEASED_SNIPPET
    path = _write(tmp_path, text)
    assert finalize_migrations("0.8.0", migrations_path=path) == 2
    assert PLACEHOLDER not in path.read_text(encoding="utf-8")


def test_finalize_no_placeholder_is_noop(tmp_path):
    """Without a placeholder the file is left unchanged."""
    original = 'MIGRATIONS = [\n    Migration(to_version="0.8.0", ...),\n]\n'
    path = _write(tmp_path, original)
    assert finalize_migrations("0.9.0", migrations_path=path) == 0
    assert path.read_text(encoding="utf-8") == original


def test_guardrail_rejects_patch_bump_with_placeholder(tmp_path):
    """A patch bump with a pending breaking migration is refused."""
    path = _write(tmp_path, UNRELEASED_SNIPPET)
    with pytest.raises(ValueError, match="patch bump"):
        finalize_migrations("0.7.2", migrations_path=path, previous_version="0.7.1")
    assert PLACEHOLDER in path.read_text(encoding="utf-8")


def test_guardrail_allows_minor_bump_with_placeholder(tmp_path):
    """A minor bump with a pending breaking migration is allowed."""
    path = _write(tmp_path, UNRELEASED_SNIPPET)
    assert (
        finalize_migrations("0.8.0", migrations_path=path, previous_version="0.7.1")
        == 1
    )


def test_registry_targets_are_placeholder_or_valid_versions():
    """Every registered migration targets UNRELEASED or a valid release version.

    While a breaking change is in development its step carries the UNRELEASED
    placeholder; at release time :func:`finalize_migrations` stamps it to a
    concrete version. Both are acceptable — anything else (a malformed or
    half-finalized target) is a bug. This replaces the old "placeholder must be
    present" check, which could not hold on a release commit or on ``main``
    between breaking releases.
    """
    for step in MIGRATIONS:
        if step.to_version == UNRELEASED:
            continue
        Version(step.to_version)  # raises InvalidVersion if malformed
