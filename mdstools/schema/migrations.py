"""Registry of metadata schema migrations.

Each :class:`Migration` upgrades a metadata dict across one *breaking* schema
release. Only breaking changes (minor-version bumps) need an entry — additive
changes are backward-compatible and require none.

A step for an upcoming breaking change uses the :data:`UNRELEASED` placeholder
as its target version; the concrete version is stamped in when the release is
cut (see the ``finalize_migrations`` release helper). Released steps keep their
concrete target version permanently as the migration history grows.
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


def _cleaning_procedure_to_preparation_procedure(data: dict) -> dict:
    r"""Breaking change: replace the cell's ``cleaningProcedure`` string.

    Move ``system.electrochemicalCell.cleaningProcedure`` (a free-text string)
    into ``system.electrochemicalCell.preparationProcedure.description`` (a
    list of steps), following the shared ``PreparationProcedure`` structure
    already used by electrodes. If a ``preparationProcedure.description`` exists
    already, the cleaning text is appended to it (unless already listed), so no
    information is lost.

    Pure ``dict -> dict``: the input is not mutated. Idempotent: if there is no
    ``cleaningProcedure`` (already migrated, or never present) the document is
    returned unchanged.

    EXAMPLES::

        >>> from mdstools.schema.migrations import (
        ...     _cleaning_procedure_to_preparation_procedure as move)
        >>> before = {"system": {"electrochemicalCell": {
        ...     "cleaningProcedure": "Boiled in Milli-Q water."}}}
        >>> after = move(before)
        >>> after["system"]["electrochemicalCell"]
        {'preparationProcedure': {'description': ['Boiled in Milli-Q water.']}}
        >>> move(after) == after      # idempotent
        True

    An existing preparation procedure is extended rather than overwritten::

        >>> both = {"system": {"electrochemicalCell": {
        ...     "cleaningProcedure": "Boiled.",
        ...     "preparationProcedure": {"url": "https://doi.org/x",
        ...                              "description": ["Assembled."]}}}}
        >>> move(both)["system"]["electrochemicalCell"]["preparationProcedure"]
        {'url': 'https://doi.org/x', 'description': ['Assembled.', 'Boiled.']}

    """
    result = deepcopy(data)

    system = result.get("system")
    cell = system.get("electrochemicalCell") if isinstance(system, dict) else None
    if not isinstance(cell, dict) or "cleaningProcedure" not in cell:
        return result
    cleaning = cell.pop("cleaningProcedure")

    if cleaning is None or cleaning == "" or cleaning == []:
        return result
    steps = list(cleaning) if isinstance(cleaning, list) else [str(cleaning)]

    preparation = cell.get("preparationProcedure")
    if preparation is None:
        preparation = cell["preparationProcedure"] = {}
    description = preparation.get("description")
    if description is None:
        description = []
    elif not isinstance(description, list):
        description = [description]
    description.extend(step for step in steps if step not in description)
    preparation["description"] = description
    return result


#: Name given to the electrolyte when a single ``system.electrolyte`` is
#: converted into the ``system.electrolytes`` list.
DEFAULT_ELECTROLYTE_NAME = "electrolyte1"


def _electrolyte_to_electrolytes(data: dict) -> dict:
    r"""Breaking change: allow several electrolytes (#129).

    Replace the single ``system.electrolyte`` object by the list
    ``system.electrolytes``. The old electrolyte becomes the only entry and gets
    the required ``name`` :data:`DEFAULT_ELECTROLYTE_NAME` unless it already has
    one. The list takes the position of the old key, so the order of the keys in
    ``system`` is kept.

    Pure ``dict -> dict``: the input is not mutated. Idempotent: if there is no
    ``system.electrolyte`` (already migrated, or never present) the document is
    returned unchanged.

    :raises ValueError: if both ``electrolyte`` and ``electrolytes`` are present
        (ambiguous; needs manual resolution).

    EXAMPLES::

        >>> from mdstools.schema.migrations import (
        ...     _electrolyte_to_electrolytes as move)
        >>> before = {"system": {"type": "electrochemical",
        ...                      "electrolyte": {"type": "aqueous"},
        ...                      "electrodes": []}}
        >>> after = move(before)
        >>> after["system"]
        {'type': 'electrochemical', 'electrolytes': [{'name': 'electrolyte1', 'type': 'aqueous'}], 'electrodes': []}
        >>> move(after) == after      # idempotent
        True

    """
    result = deepcopy(data)

    system = result.get("system")
    if not isinstance(system, dict) or "electrolyte" not in system:
        return result
    if "electrolytes" in system:
        raise ValueError(
            "cannot migrate electrolyte: both system.electrolyte and "
            "system.electrolytes are present; resolve this manually before "
            "migrating."
        )

    electrolyte = system["electrolyte"]
    if electrolyte is None:
        del system["electrolyte"]
        return result
    if not isinstance(electrolyte, dict):
        raise ValueError(
            "cannot migrate electrolyte: system.electrolyte is not a mapping."
        )

    if "name" not in electrolyte:
        if hasattr(electrolyte, "insert"):  # ruamel CommentedMap: keep comments
            electrolyte.insert(0, "name", DEFAULT_ELECTROLYTE_NAME)
        else:
            electrolyte = {"name": DEFAULT_ELECTROLYTE_NAME, **electrolyte}

    position = list(system).index("electrolyte")
    del system["electrolyte"]
    if hasattr(system, "insert"):  # ruamel CommentedMap: keep comments
        system.insert(position, "electrolytes", [electrolyte])
    else:
        items = list(system.items())
        items.insert(position, ("electrolytes", [electrolyte]))
        system.clear()
        system.update(items)
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
    Migration(
        to_version=UNRELEASED,
        description=(
            "Replace system.electrochemicalCell.cleaningProcedure with "
            "system.electrochemicalCell.preparationProcedure.description"
        ),
        apply=_cleaning_procedure_to_preparation_procedure,
    ),
    Migration(
        to_version=UNRELEASED,
        description=(
            "Replace system.electrolyte with the list system.electrolytes, "
            "naming the electrolyte 'electrolyte1'"
        ),
        apply=_electrolyte_to_electrolytes,
    ),
]
