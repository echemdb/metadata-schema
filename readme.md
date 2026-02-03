# Metadata Schema

Development of a metadata schema for experimental data, specifically electrochemical and electrocatalytic data.

## Install with pixi for development

If you want to work on the metadata-schema itself, install [pixi](https://pixi.sh)
and get a copy of the latest unreleased version of the metadata-schema:

```sh
git clone https://github.com/echemdb/metadata-schema.git
cd metadata-schema
```

## Usage

### Validate schema files

To validate the example files against the JSON schemas:

```sh
pixi run validate
```

### Convert metadata to Excel/CSV

The `mdstools` package provides tools to convert nested YAML metadata into flat Excel/CSV formats with optional schema-based enrichment (descriptions and examples from JSON schemas).

Convert a YAML file to enriched Excel and CSV:

```sh
pixi run convert tests/example_metadata.yaml
```

This creates three files in `generated/`:
- `example_metadata.csv` - Flat CSV with all metadata
- `example_metadata.xlsx` - Single-sheet Excel file
- `example_metadata_sheets.xlsx` - Multi-sheet Excel (one sheet per top-level key)

All exported files include `Description` and `Example` columns populated from the JSON schemas, making it easier for users to understand and fill out the metadata templates.

#### Options

```sh
pixi run convert <yaml_file> [--schema-dir DIR] [--output-dir DIR] [--no-enrichment]
```

- `--schema-dir` - Directory with JSON schemas (default: `schemas`)
- `--output-dir` - Output directory (default: `generated`)
- `--no-enrichment` - Disable enrichment (no Description/Example columns)

### Run tests

```sh
pixi run test              # Run all tests
pixi run doctest           # Run doctests only
pixi run test-comprehensive # Run integration tests only
```

## Python API

The `mdstools` package can also be used programmatically:

```python
import yaml
from mdstools.tabular_schema import MetadataConverter

# Load YAML metadata
with open('metadata.yaml') as f:
    data = yaml.safe_load(f)

# Create converter with schema enrichment
converter = MetadataConverter.from_dict(data, schema_dir='schemas')

# Get enriched DataFrame
df = converter.enriched_df

# Export to various formats
converter.to_csv('output.csv', enriched=True)
converter.to_excel('output.xlsx', enriched=True)
converter.to_excel('output_sheets.xlsx', enriched=True, separate_sheets=True)
```

See [mdstools/README.md](mdstools/README.md) for detailed API documentation
