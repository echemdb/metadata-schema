# Pydantic Models for echemdb Metadata (Prototype)

> **Note:** This folder is a prototype / proof-of-concept. It should be removed
> or merged into the main codebase once the approach is evaluated and the PR is
> finalized.

## Design Idea

Currently, metadata schemas are defined as **hand-written JSON Schema files** in
`schemas/schema_pieces/`. This works, but has drawbacks:

- Naming conventions (camelCase properties, PascalCase definitions) must be
  enforced by a separate CI script (`check_naming.py`).
- Validation requires a separate library (`jsonschema` + `referencing`).
- Enrichment (descriptions, examples) is extracted at runtime by walking the
  JSON Schema tree.
- There is no Python-level type safety — YAML dicts are untyped.

**Pydantic models** can serve as a **single source of truth** that replaces all
of the above:

| Concern | Current approach | With Pydantic |
|---|---|---|
| Schema definition | Hand-written `schema_pieces/*.json` | Python model classes |
| Naming convention | `check_naming.py` CI script | Automatic via `alias_generator=to_camel` |
| Validation | `jsonschema` + `referencing` | `Model.model_validate(data)` |
| Enrichment | `SchemaEnricher` walking JSON Schema | `Model.model_json_schema()` |
| Type safety | None (raw dicts) | Full IDE support, autocomplete, refactoring |

## How It Works

### Base Class

All models inherit from `EchemdbModel` (in `base.py`), which configures:

```python
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class EchemdbModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,   # snake_case → camelCase
        populate_by_name=True,      # accept both snake_case and camelCase
        extra="forbid",             # reject unknown fields
    )
```

This means:
- **Python code** uses idiomatic `snake_case` (`scan_rate`, `measurement_type`)
- **YAML/JSON** uses `camelCase` (`scanRate`, `measurementType`) — automatically
- **Naming mistakes are impossible** — derived from code, not typed by hand

### Example Model

```python
from mdstools.models.base import EchemdbModel
from mdstools.models.general import Quantity

class FigureDescription(EchemdbModel):
    type: DataType                               # required, validated enum
    measurement_type: str | None = None          # YAML key: "measurementType"
    scan_rate: ScanRate | None = None            # YAML key: "scanRate"
    fields: list[FieldDescriptor] | None = None  # nested model list
```

### Usage

```python
import yaml
from mdstools.models.figure_description import FigureDescription

# Load from YAML (camelCase input)
with open("example.yaml") as f:
    data = yaml.safe_load(f)
fd = FigureDescription.model_validate(data)

# Access in Python (snake_case)
fd.scan_rate.value   # 50
fd.measurement_type  # "CV"

# Serialize back to camelCase
output = fd.model_dump(by_alias=True, exclude_none=True, mode="json")
yaml.dump(output)

# Generate JSON Schema
schema = FigureDescription.model_json_schema(mode="serialization")

# Validate (rejects invalid data with clear errors)
FigureDescription.model_validate({"type": "invalid"})  # raises ValidationError
```

## Files

| File | Contents |
|---|---|
| `base.py` | `EchemdbModel` — shared base with camelCase alias generation |
| `general.py` | `Quantity`, `Uncertainty`, `UncertaintyType` — reusable types |
| `curation.py` | `Curation`, `Process`, `Role` — curation metadata |
| `figure_description.py` | `FigureDescription`, `FieldDescriptor`, `ScanRate`, `DataType`, `Orientation` |
| `demo_pydantic.py` | Runnable demo: `pixi run -e dev python mdstools/models/demo_pydantic.py` |

## Open Questions

1. **Scope**: Convert all ~25 schema pieces, or keep a hybrid approach?
2. **Source of truth**: Should models *replace* `schema_pieces/*.json` (generate
   JSON from Python), or coexist alongside them?
3. **Integration**: Wire into existing `SchemaEnricher` / `validator.py`, or
   build new enrichment/validation on top of the models?
4. **Schema compatibility**: The generated JSON Schema uses `$defs` (draft
   2020-12) while current schemas use `definitions` (draft-07). Need to decide
   which draft to target.
