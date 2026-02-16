r"""
Base configuration shared by all echemdb Pydantic models.

Defines a common base class that enforces camelCase serialization of
snake_case Python field names.

EXAMPLES::

    A minimal model using the base class::

        >>> from mdstools.models.base import EchemdbModel
        >>> class Demo(EchemdbModel):
        ...     my_field: str = ""
        >>> d = Demo(myField="hello")
        >>> d.my_field
        'hello'

    Serialization uses camelCase::

        >>> d.model_dump(by_alias=True)
        {'myField': 'hello'}

    JSON Schema uses camelCase property names::

        >>> schema = Demo.model_json_schema(mode='serialization')
        >>> 'myField' in schema['properties']
        True

"""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class EchemdbModel(BaseModel):
    """Base model with camelCase alias generation for all echemdb schemas.

    All models inherit from this class to ensure:

    - Python code uses idiomatic ``snake_case``
    - YAML/JSON serialization uses ``camelCase``
    - Generated JSON Schema has ``camelCase`` property names

    EXAMPLES::

        >>> from mdstools.models.base import EchemdbModel
        >>> class Electrode(EchemdbModel):
        ...     geometric_electrolyte_contact_area: float | None = None
        >>> e = Electrode(geometricElectrolyteContactArea=1.5)
        >>> e.geometric_electrolyte_contact_area
        1.5
        >>> e.model_dump(by_alias=True)
        {'geometricElectrolyteContactArea': 1.5}

    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )
