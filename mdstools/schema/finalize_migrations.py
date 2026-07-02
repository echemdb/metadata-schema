"""Finalize unreleased migrations at release time.

Migration steps for an upcoming breaking release are registered with
``to_version=UNRELEASED`` (see :mod:`mdstools.schema.migrations`), because the
concrete version is not known until the release is cut. This helper rewrites
that placeholder to the actual release version.

It is invoked by ``rever`` during a release (after ``version_bump``), mirroring
how the example ``echemdbSchemaVersion`` values are stamped. If no placeholder
is present — e.g. a patch-only release — it is a no-op.

Usage::

    python -m mdstools.schema.finalize_migrations <version> [<previous_version>]

If *previous_version* is given, a guardrail refuses a patch-only bump while an
unreleased breaking migration is present (breaking changes require at least a
minor bump).
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

import sys
from pathlib import Path

from packaging.version import Version

#: Source line fragment marking an unreleased migration target.
PLACEHOLDER = "to_version=UNRELEASED"

#: The registry module whose placeholders get rewritten.
MIGRATIONS_FILE = Path(__file__).with_name("migrations.py")


def _is_breaking_bump(previous: str, new: str) -> bool:
    """True if *new* is at least a minor bump over *previous*.

    EXAMPLES::

        >>> from mdstools.schema.finalize_migrations import _is_breaking_bump
        >>> _is_breaking_bump("0.7.1", "0.8.0")
        True
        >>> _is_breaking_bump("0.7.1", "0.7.2")
        False
        >>> _is_breaking_bump("0.7.1", "1.0.0")
        True

    """
    old, current = Version(previous), Version(new)
    return (current.major, current.minor) > (old.major, old.minor)


def finalize_migrations(
    version: str,
    migrations_path: Path = MIGRATIONS_FILE,
    previous_version: str = None,
) -> int:
    """Rewrite ``to_version=UNRELEASED`` placeholders to *version*.

    :param version: The concrete release version to stamp in.
    :param migrations_path: The registry module to rewrite.
    :param previous_version: If given, refuse a patch-only bump while an
        unreleased breaking migration is present.
    :returns: The number of placeholders rewritten (0 if none — a no-op).
    :raises ValueError: if the guardrail is enabled and *version* is only a
        patch bump over *previous_version* while a placeholder is present.
    """
    migrations_path = Path(migrations_path)
    text = migrations_path.read_text(encoding="utf-8")
    count = text.count(PLACEHOLDER)
    if count == 0:
        return 0

    if previous_version is not None and not _is_breaking_bump(
        previous_version, version
    ):
        raise ValueError(
            f"{count} unreleased breaking migration(s) present, but {version} is "
            f"only a patch bump over {previous_version}; breaking changes require "
            f"at least a minor version bump."
        )

    migrations_path.write_text(
        text.replace(PLACEHOLDER, f'to_version="{version}"'), encoding="utf-8"
    )
    return count


def main():
    """Command-line entry point (called by rever with ``$VERSION``)."""
    args = sys.argv[1:]
    if not args:
        raise SystemExit(
            "usage: python -m mdstools.schema.finalize_migrations "
            "<version> [<previous_version>]"
        )
    version = args[0]
    previous_version = args[1] if len(args) > 1 else None

    count = finalize_migrations(version, previous_version=previous_version)
    if count:
        print(f"Finalized {count} migration(s) to version {version}.")
    else:
        print("No unreleased migrations to finalize.")


if __name__ == "__main__":
    main()
