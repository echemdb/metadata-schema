# Usage

## Command-line interface

The `mdstools` CLI provides commands for converting between YAML and tabular formats.

### Flatten YAML to Excel/CSV

Convert a nested YAML metadata file to a tabular format:

```bash
mdstools flatten tests/example_metadata.yaml --output-dir generated
```

Or via pixi:

```bash
pixi run flatten tests/example_metadata.yaml --output-dir generated
```

Options:

- `--output-dir` — Output directory (default: `generated/`)
- `--schema` — Schema name for enrichment (adds descriptions and examples)
- `--format` — Output format: `xlsx`, `csv`, or `md`

### Unflatten Excel/CSV to YAML

Convert a tabular file back to nested YAML:

```bash
mdstools unflatten generated/output.xlsx
```

Or via pixi:

```bash
pixi run unflatten generated/output.xlsx
```

## Python API

### Basic flattening

```python
from mdstools.metadata.metadata import Metadata

data = {"curation": {"process": [{"role": "curator", "name": "Jane Doe"}]}}
metadata = Metadata(data)
flattened = metadata.flatten()
flattened.to_excel("output.xlsx")
```

### With schema enrichment

```python
from mdstools.metadata.metadata import Metadata
from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata

metadata = Metadata(data)
flattened = metadata.flatten()
enriched = EnrichedFlattenedMetadata(flattened.rows, schema_dir="schemas")
enriched.to_excel("output.xlsx")
```

### Multi-sheet Excel export

```python
enriched.to_excel("output.xlsx", separate_sheets=True)
```

### Schema validation

```python
from mdstools.schema.validator import validate_with_json_schema, validate_with_pydantic

# JSON Schema validation
validate_with_json_schema(data, schema_name="minimum_echemdb")

# Pydantic validation
validate_with_pydantic(data, schema_name="minimum_echemdb")
```
