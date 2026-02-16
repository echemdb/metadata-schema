r"""
Pydantic models for curation metadata.

Corresponds to ``schemas/schema_pieces/curation.json``.

EXAMPLES::

    Create curation data from YAML-like dicts::

        >>> from mdstools.models.curation import Curation
        >>> c = Curation(process=[{
        ...     "role": "experimentalist",
        ...     "name": "Jane Doe",
        ...     "orcid": "https://orcid.org/0000-0000-0000-0001",
        ... }])
        >>> c.process[0].role
        'experimentalist'
        >>> c.process[0].name
        'Jane Doe'

    Validation rejects invalid roles::

        >>> try:
        ...     Curation(process=[{"role": "invalid", "name": "X", "orcid": "https://orcid.org/0"}])
        ... except Exception as e:
        ...     "Input should be" in str(e)
        True

    Serialize to camelCase dict::

        >>> d = c.model_dump(by_alias=True, exclude_none=True)
        >>> d['process'][0]['name']
        'Jane Doe'

"""

from enum import Enum
from typing import Optional

from pydantic import Field, HttpUrl

from mdstools.models.base import EchemdbModel


class Role(str, Enum):
    """Role of a person in the curation process."""

    EXPERIMENTALIST = "experimentalist"
    CURATOR = "curator"
    REVIEWER = "reviewer"
    SUPERVISOR = "supervisor"


class Process(EchemdbModel):
    """A person involved in data creation or curation.

    EXAMPLES::

        >>> p = Process(role="curator", name="John Smith", orcid="https://orcid.org/0000-0000-0000-0001")
        >>> p.role
        'curator'

    """

    role: Role = Field(
        description="Role of the person in the data lifecycle.",
        json_schema_extra={"example": "experimentalist"},
    )
    name: str = Field(
        description="Full name of the person.",
        json_schema_extra={"example": "Jane Doe"},
    )
    orcid: str = Field(
        description="A valid HTTP or HTTPS URL containing the ORCID.",
        json_schema_extra={"example": "https://orcid.org/0000-0000-0000-0001"},
    )
    date: Optional[str] = Field(
        default=None,
        description="Date when the person performed their role (ISO 8601 format: YYYY-MM-DD).",
        json_schema_extra={"example": "2024-01-15"},
    )


class Curation(EchemdbModel):
    """Details on the curation process of the data.

    EXAMPLES::

        >>> c = Curation(process=[{
        ...     "role": "curator",
        ...     "name": "Jane Doe",
        ...     "orcid": "https://orcid.org/0000-0000-0000-0001",
        ... }])
        >>> len(c.process)
        1

    """

    process: list[Process] = Field(
        min_length=1,
        description="List of people involved in creating, recording, or curating this data.",
    )
