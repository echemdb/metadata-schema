"""Registry of metadata schema migrations.

Each :class:`Migration` upgrades a metadata dict across one *breaking* schema
release. Only breaking changes (minor-version bumps) need an entry — additive
changes are backward-compatible and require none.

A step for an upcoming breaking change is registered with
``to_version=UNRELEASED``; the concrete version is stamped in when the release
is cut (see the ``finalize_migrations`` release helper). Released steps keep
their concrete ``to_version`` permanently as the migration history grows.
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


def _move_temperature_to_operation_parameters(data: dict) -> dict:
    r"""Breaking change for 0.8.0: relocate the electrolyte temperature.

    Move ``system.electrolyte.temperature`` to
    ``experimental.operationParameters.temperature``. The old value is a
    ``Quantity`` and the new slot is a ``ControlledQuantity`` (a superset), so
    the value carries over unchanged.

    Pure ``dict -> dict``: the input is not mutated. Idempotent — if there is no
    ``temperature`` under ``system.electrolyte`` (already migrated, or never
    present) the document is returned unchanged.

    :raises ValueError: if ``temperature`` is present in *both* the old and new
        locations with different values (ambiguous — needs manual resolution).

    EXAMPLES::

        >>> from mdstools.schema.migrations import (
        ...     _move_temperature_to_operation_parameters as move)
        >>> before = {"system": {"electrolyte": {"temperature": {"value": 298}}}}
        >>> after = move(before)
        >>> after["experimental"]["operationParameters"]["temperature"]
        {'value': 298}
        >>> "temperature" in after["system"]["electrolyte"]
        False
        >>> move(after) == after      # idempotent
        True

    """
    result = deepcopy(data)

    electrolyte = result.get("system", {}).get("electrolyte", {})
    if not isinstance(electrolyte, dict) or "temperature" not in electrolyte:
        return result
    temperature = electrolyte.pop("temperature")

    experimental = result.setdefault("experimental", {})
    operation = experimental.setdefault("operationParameters", {})
    existing = operation.get("temperature")
    if existing is not None and existing != temperature:
        raise ValueError(
            "cannot migrate temperature: it is present under both "
            "system.electrolyte and experimental.operationParameters with "
            "different values; resolve this manually before migrating."
        )
    operation.setdefault("temperature", temperature)
    return result


#: Registered migrations, in ascending ``to_version`` order.
#: The temperature move is unreleased; its concrete version is stamped in when
#: the release is cut (see the ``finalize_migrations`` helper, added later).
MIGRATIONS: list[Migration] = [
    Migration(
        to_version="0.8.0",
        description=(
            "Move system.electrolyte.temperature to "
            "experimental.operationParameters.temperature"
        ),
        apply=_move_temperature_to_operation_parameters,
    ),
]
