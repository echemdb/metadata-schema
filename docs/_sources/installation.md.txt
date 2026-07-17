# Installation

## Using pixi (recommended)

[pixi](https://pixi.sh/) manages all dependencies automatically:

```bash
git clone https://github.com/echemdb/metadata-schema.git
cd metadata-schema
pixi install
```

## Using pip

Install in development mode:

```bash
pip install -e .
```

### Dependencies

The following packages are required:

- `click` — CLI interface
- `pandas` — Data manipulation
- `tabulate` — Table formatting
- `xlsxwriter` — Excel export
- `jsonschema` — JSON Schema validation
- `linkml` — Schema definitions and generation
- `linkml-runtime` — LinkML runtime support
