# Welcome to metadata-schema's documentation!

The [metadata-schema](https://github.com/echemdb/metadata-schema) repository provides standardized metadata schemas for the [echemdb](https://www.echemdb.org) project. Schemas are defined in [LinkML](https://linkml.io/) and used to validate and describe electrochemical data packages.

The `mdstools` Python package provides tools for working with these schemas:

- Flatten nested YAML metadata into tabular (Excel/CSV) format
- Enrich flattened metadata with descriptions and examples from the schemas
- Validate metadata against the schemas
- Convert between YAML, Excel, and CSV formats

## Getting started

See the [installation guide](installation.md) for setup instructions.

## Contents

```{toctree}
:maxdepth: 2

installation
usage
schemas
api
```
