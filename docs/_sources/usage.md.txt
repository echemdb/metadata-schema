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

### Update metadata to a newer schema version

Migrate a metadata file (or data package) from an older schema version to a
newer one. Without `--in-place` this is a dry run that reports the migration
steps per document:

```bash
mdstools update path/to/metadata.yaml
```

Apply the migration, rewriting the file in place (YAML comments and layout are
preserved):

```bash
mdstools update path/to/metadata.yaml --in-place
```

Or via pixi:

```bash
pixi run update path/to/metadata.yaml --in-place
```

Options:

- `--to-version` — Target schema version (default: the installed version).
- `--in-place` — Write the migrated file back in place. Without it, `update`
  only reports what would change.

Data packages are handled per resource: each `resources[].metadata.<key>` block
is migrated using its own `echemdbSchemaVersion`.

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

### Migrating metadata across schema versions

```python
from mdstools.schema.migrate import MetadataMigrator, migrate_file

# In memory: migrate a dict, then validate the result against a target schema
migrated = MetadataMigrator(data, target_version="latest").migrated()
MetadataMigrator(data).validate("minimum_echemdb")

# From a file (returns the migrated dict; pass in_place=True to overwrite,
# preserving YAML comments)
migrated = migrate_file("metadata.yaml", in_place=True)
```

Only breaking schema changes need a migration step; additive changes are
backward-compatible. Steps are declared in `mdstools/schema/migrations.py`.
