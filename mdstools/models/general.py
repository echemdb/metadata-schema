r"""
Pydantic models for general reusable types: Quantity, Uncertainty, Value, Unit.

These correspond to ``schemas/schema_pieces/general/quantity.json``.

EXAMPLES::

    Create a Quantity from camelCase input (as it appears in YAML)::

        >>> from mdstools.models.general import Quantity
        >>> q = Quantity(value=0.5, unit="mol / l")
        >>> q.value
        0.5
        >>> q.unit
        'mol / l'

    With uncertainty::

        >>> q = Quantity(
        ...     value=1.23,
        ...     unit="V",
        ...     uncertainty={"value": 0.01, "unit": "V", "type": "absolute"},
        ... )
        >>> q.uncertainty.value
        0.01
        >>> q.uncertainty.type
        'absolute'

    Serialize back to camelCase dict::

        >>> d = q.model_dump(by_alias=True, exclude_none=True)
        >>> d['unit']
        'V'

    Generate JSON Schema::

        >>> schema = Quantity.model_json_schema(mode='serialization')
        >>> 'Uncertainty' in schema.get('$defs', {})
        True

"""

from enum import Enum
from typing import Optional, Union

from pydantic import Field

from mdstools.models.base import EchemdbModel


class UncertaintyType(str, Enum):
    """Type of uncertainty measurement."""

    ABSOLUTE = "absolute"
    RELATIVE = "relative"


class Uncertainty(EchemdbModel):
    """Uncertainty information for a measured quantity.

    EXAMPLES::

        >>> u = Uncertainty(value=0.01, unit="V", type="absolute")
        >>> u.type
        'absolute'
        >>> u.model_dump(by_alias=True, exclude_none=True)
        {'value': 0.01, 'unit': 'V', 'type': 'absolute'}

    """

    value: Optional[float] = Field(
        default=None,
        description="Symmetric uncertainty value (±).",
        json_schema_extra={"example": 0.01},
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of the uncertainty value.",
        json_schema_extra={"example": "mol / l"},
    )
    positive_value: Optional[float] = Field(
        default=None,
        description="Upper bound (+) for asymmetric uncertainties.",
        json_schema_extra={"example": 0.02},
    )
    negative_value: Optional[float] = Field(
        default=None,
        description="Lower bound (-) for asymmetric uncertainties.",
        json_schema_extra={"example": 0.01},
    )
    comment: Optional[str] = Field(
        default=None,
        description="Additional information about the uncertainty estimation.",
        json_schema_extra={
            "example": "Standard deviation from 3 replicate measurements"
        },
    )
    type: Optional[UncertaintyType] = Field(
        default=None,
        description="Type of uncertainty (absolute or relative).",
        json_schema_extra={"example": "absolute"},
    )


class Quantity(EchemdbModel):
    """A physical quantity with a value, unit, and optional uncertainty.

    EXAMPLES::

        >>> q = Quantity(value=50, unit="mV / s")
        >>> q.model_dump(by_alias=True, exclude_none=True)
        {'value': 50, 'unit': 'mV / s'}

    """

    value: Optional[Union[float, int, str]] = Field(
        default=None,
        description="Numerical value (can be a number, string, or null).",
        json_schema_extra={"example": 0.5},
    )
    uncertainty: Optional[Uncertainty] = Field(
        default=None,
        description="Uncertainty information for this quantity.",
    )
    unit: Optional[Union[str, int]] = Field(
        default=None,
        description="Unit of measurement as a string (e.g., 'mol / l', 'V', 'mA / cm2').",
        json_schema_extra={"example": "mol / l"},
    )
    comment: Optional[str] = Field(
        default=None,
        description="Additional notes about the measurement or quantity.",
        json_schema_extra={"example": "Measured at room temperature"},
    )
    calculation: Optional[str] = Field(
        default=None,
        description="Method or formula used to calculate this quantity.",
        json_schema_extra={"example": "Obtained by multiplying U and I"},
    )
