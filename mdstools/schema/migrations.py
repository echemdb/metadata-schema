"""Registry of metadata schema migrations.

Each :class:`Migration` upgrades a metadata dict across one *breaking* schema
release. Only breaking changes (minor-version bumps) need an entry — additive
changes are backward-compatible and require none.

The registry is intentionally empty at this stage: the engine
(:mod:`mdstools.schema.migrate`) is introduced first and exercised with test
migrations. Real steps (e.g. the 0.8.0 temperature move) are registered in
later stages.
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

from dataclasses import dataclass
from typing import Callable

#: Placeholder target used while a breaking change has not been released yet.
#: It is rewritten to the concrete release version when a tag is cut (see the
#: ``finalize_migrations`` release helper, added in a later stage).
UNRELEASED = "UNRELEASED"


@dataclass(frozen=True)
class Migration:
    """A single breaking-change upgrade step.

    :param to_version: The schema version this step produces (a breaking
        release), or :data:`UNRELEASED` while it has not been released yet.
    :param description: Human-readable summary of the change.
    :param apply: A pure ``dict -> dict`` transform that upgrades a metadata
        document. It must not mutate its input and should be idempotent
        (applying it to already-migrated data is a no-op).

    EXAMPLES::

        >>> from mdstools.schema.migrations import Migration
        >>> step = Migration("0.8.0", "example", lambda data: data)
        >>> step.to_version
        '0.8.0'

    """

    to_version: str
    description: str
    apply: Callable[[dict], dict]


#: Registered migrations, in ascending ``to_version`` order. Empty for now;
#: breaking-change steps are appended here as the schema evolves.
MIGRATIONS: list[Migration] = []
