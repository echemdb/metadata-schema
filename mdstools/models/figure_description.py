r"""
Pydantic models for figure description metadata.

Corresponds to ``schemas/schema_pieces/figure_description.json``.

EXAMPLES::

    Create a figure description from YAML-like data::

        >>> from mdstools.models.figure_description import FigureDescription
        >>> fd = FigureDescription(
        ...     type="digitized",
        ...     measurementType="CV",
        ...     fields=[{"name": "E", "unit": "V", "orientation": "horizontal"}],
        ...     scanRate={"value": 50, "unit": "mV / s"},
        ... )
        >>> fd.type
        'digitized'
        >>> fd.measurement_type
        'CV'
        >>> fd.scan_rate.value
        50

    Also works with snake_case (Python-native)::

        >>> fd2 = FigureDescription(
        ...     type="raw",
        ...     measurement_type="EIS",
        ... )
        >>> fd2.measurement_type
        'EIS'

    Serialize to camelCase::

        >>> d = fd.model_dump(by_alias=True, exclude_none=True)
        >>> 'measurementType' in d
        True
        >>> 'scanRate' in d
        True

    Validation rejects invalid types::

        >>> try:
        ...     FigureDescription(type="invalid_type")
        ... except Exception as e:
        ...     "Input should be" in str(e)
        True

"""

from enum import Enum
from typing import Optional

from pydantic import Field

from mdstools.models.base import EchemdbModel
from mdstools.models.general import Quantity


class DataType(str, Enum):
    """Source or origin of the data."""

    DIGITIZED = "digitized"
    RAW = "raw"
    SIMULATED = "simulated"
    PROCESSED = "processed"


class Orientation(str, Enum):
    """Axis orientation in plots."""

    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class FieldDescriptor(EchemdbModel):
    """Description of a data field (column) in frictionless table-schema format.

    Extended with echemdb-specific properties for physical quantities.

    EXAMPLES::

        >>> f = FieldDescriptor(name="E_WE", unit="V", orientation="horizontal")
        >>> f.name
        'E_WE'
        >>> f.orientation
        'horizontal'

    """

    name: str = Field(
        description="Name of the data field. Use single letters for specific systems. "
        "Otherwise use descriptive names like 't_rel', 'E_WE', or 'j_WE'.",
        json_schema_extra={"example": "E_WE"},
    )
    type: Optional[str] = Field(
        default=None,
        description="Data type of the field (string, number, integer, boolean, object, "
        "array, date, time, datetime, year, duration, geopoint, geojson, any).",
        json_schema_extra={"example": "number"},
    )
    format: Optional[str] = Field(
        default=None,
        description="Format specification for the field type.",
        json_schema_extra={"example": "default"},
    )
    title: Optional[str] = Field(
        default=None,
        description="A human-readable title for this field.",
    )
    description: Optional[str] = Field(
        default=None,
        description="A description of that field.",
        json_schema_extra={
            "example": "The potential measured between the working electrode and reference electrode."
        },
    )
    dimension: Optional[str] = Field(
        default=None,
        description="Physical dimension of the field (e.g., 'time', 'potential', 'current density').",
        json_schema_extra={"example": "potential"},
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement for this field, following astropy's string unit notation.",
        json_schema_extra={"example": "V"},
    )
    reference: Optional[str] = Field(
        default=None,
        description="Reference electrode or reference point for this measurement.",
        json_schema_extra={"example": "RHE"},
    )
    orientation: Optional[Orientation] = Field(
        default=None,
        description="Axis orientation in plots (horizontal for x-axis, vertical for y-axis).",
        json_schema_extra={"example": "horizontal"},
    )


class ScanRate(Quantity):
    """The rate at which the data has been recorded.

    Inherits all fields from :class:`~mdstools.models.general.Quantity`.

    EXAMPLES::

        >>> sr = ScanRate(value=50, unit="mV / s")
        >>> sr.value
        50

    """


class FigureDescription(EchemdbModel):
    """Description of the data to a figure or plot.

    Includes data type, measurement details, field descriptions, and scan rate.

    EXAMPLES::

        >>> fd = FigureDescription(type="raw", measurementType="CV")
        >>> fd.type
        'raw'
        >>> fd.measurement_type
        'CV'

    """

    type: DataType = Field(
        description="Source or origin of the data, such as digitized, raw, simulated, or processed.",
        json_schema_extra={"example": "raw"},
    )
    measurement_type: Optional[str] = Field(
        default=None,
        description="Acronym type for the measurement performed, such as CV, EIS, XPS, etc.",
        json_schema_extra={"example": "CV"},
    )
    simultaneous_measurements: Optional[list[str]] = Field(
        default=None,
        description="Other measurements performed simultaneously, such as ring current, IR, Raman, ICP-MS.",
    )
    comment: Optional[str] = Field(
        default=None,
        description="Additional notes about the figure or data.",
        json_schema_extra={"example": "Data below 0 V was cut off by the x-axis."},
    )
    fields: Optional[list[FieldDescriptor]] = Field(
        default=None,
        description="Description of data fields/columns in the figure.",
    )
    scan_rate: Optional[ScanRate] = Field(
        default=None,
        description="Scan rate used in the measurement.",
    )
