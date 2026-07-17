# Welcome to metadata-schema's documentation!

The [metadata-schema](https://github.com/echemdb/metadata-schema) repository provides standardized metadata schemas for the [echemdb](https://www.echemdb.org) project. Schemas are defined in [LinkML](https://linkml.io/) and used to validate and describe electrochemical data packages.

The `mdstools` Python package provides tools for working with these schemas:

- Flatten nested YAML metadata into tabular (Excel/CSV) format
- Enrich flattened metadata with descriptions and examples from the schemas
- Validate metadata against the schemas
- Convert between YAML, Excel, and CSV formats

## JSON Schemas (v0.5.1)

The following JSON Schema files can be used to validate metadata in any language or tool that supports JSON Schema:

| Schema | Download |
| --- | --- |
| Autotag | [autotag.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/autotag.json) |
| Minimum echemdb | [minimum_echemdb.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/minimum_echemdb.json) |
| Source Data | [source_data.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/source_data.json) |
| SVG Digitizer | [svgdigitizer.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/svgdigitizer.json) |
| echemdb Package | [echemdb_package.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/echemdb_package.json) |
| SVG Digitizer Package | [svgdigitizer_package.json](https://raw.githubusercontent.com/echemdb/metadata-schema/0.5.1/schemas/svgdigitizer_package.json) |

## Getting started

See the [installation guide](installation.md) for setup instructions.

## Contents

```{toctree}
:maxdepth: 2

installation
usage
schemas
examples
api
```
