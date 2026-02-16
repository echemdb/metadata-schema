# Metadata Schema

Development of a metadata schema for experimental data, specifically electrochemical and electrocatalytic data.

## Install

Install [pixi](https://pixi.sh) and get a copy of the metadata-schema:

```sh
git clone https://github.com/echemdb/metadata-schema.git
cd metadata-schema
```

## CLI

### Flatten metadata to Excel/CSV

The `mdstools` package provides tools to flatten nested YAML metadata into tabular Excel/CSV formats with optional schema-based enrichment (descriptions and examples from JSON schemas).

Flatten a YAML file to enriched Excel and CSV:

```sh
mdstools flatten tests/example_metadata.yaml
```

This creates three files in `generated/`:
- `example_metadata.csv` - Flat CSV with all metadata
- `example_metadata.xlsx` - Single-sheet Excel file
- `example_metadata_sheets.xlsx` - Multi-sheet Excel (one sheet per top-level key)

All exported files include `Description` and `Example` columns populated from the JSON schemas, making it easier for users to understand and fill out the metadata templates.

#### Options

```sh
mdstools flatten <yaml_file> [--schema-dir DIR] [--output-dir DIR] [--no-enrichment]
```

- `--schema-dir` - Directory with JSON schemas (default: `schemas`)
- `--output-dir` - Output directory (default: `generated`)
- `--no-enrichment` - Disable enrichment (no Description/Example columns)

### Unflatten Excel/CSV back to YAML

```sh
mdstools unflatten generated/example_metadata.xlsx --schema-file schemas/schema_pieces/minimum_echemdb.json
```

> **Note**: All CLI commands can also be run via pixi, e.g., `pixi run flatten ...` and `pixi run unflatten ...`.

## Python API

The `mdstools` package can also be used programmatically:

```python
from mdstools.metadata.metadata import Metadata
from mdstools.metadata.enriched_metadata import EnrichedFlattenedMetadata

# Load YAML metadata
metadata = Metadata.from_yaml('metadata.yaml')

# Flatten to tabular format
flattened = metadata.flatten()

# Add schema enrichment (descriptions and examples)
enriched = EnrichedFlattenedMetadata(flattened.rows, schema_dir='schemas')

# Get enriched DataFrame
df = enriched.to_pandas()

# Export to various formats
enriched.to_csv('output.csv')
enriched.to_excel('output.xlsx')
enriched.to_excel('output_multi.xlsx', separate_sheets=True)  # One sheet per top-level key
enriched.to_markdown('output.md')
```

You can also load a flat Excel/CSV file, reconstruct the nested dict, and
optionally write YAML. This workflow expects columns named `Number`, `Key`,
and `Value` and is intended for unflattening back to dict/YAML.
An enriched Excel can also be loaded.

```python
from mdstools.metadata.flattened_metadata import FlattenedMetadata

flattened = FlattenedMetadata.from_excel("generated/example_metadata.xlsx")
metadata = flattened.unflatten()

data = metadata.data  # Nested dict
metadata.to_yaml("generated/example_metadata.yaml")
```

## Developer

### Run tests

```sh
pixi run test              # Run all tests
pixi run doctest           # Run doctests only
pixi run test-comprehensive # Run integration tests only
```

or all

```sh
pixi run -e dev test-all
```

### Generate schemas from LinkML

Generate JSON schemas and Pydantic models from the LinkML definitions in `linkml/`:

```sh
pixi run generate-schemas        # JSON Schema only
pixi run generate-models          # Pydantic models only
pixi run generate-all             # Both
```

The generated JSON schemas are written to `schemas/`.

After intentional changes to LinkML files, update the expected baseline files:

```sh
pixi run update-expected-schemas
```

### Validate schema files

To validate the example files against the JSON schemas:

```sh
pixi run validate
```
