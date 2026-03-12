# Schema Reference

All metadata schemas are defined as [LinkML](https://linkml.io/) YAML files and serve as the single source of truth. From these definitions, JSON Schema files and Pydantic models are generated automatically.

## Available schemas

The following schema types are available:

::::{grid} 2
:gutter: 3

:::{grid-item-card} Autotag
:link: schema/autotag/index
:link-type: doc
Complete metadata for YAML templates used by [autotag-metadata](https://echemdb.github.io/autotag-metadata/).
:::

:::{grid-item-card} Minimum echemdb
:link: schema/minimum_echemdb/index
:link-type: doc
Minimum set of metadata required for the echemdb database.
:::

:::{grid-item-card} Source Data
:link: schema/source_data/index
:link-type: doc
Source data with data description (dialect, field mapping, field units).
:::

:::{grid-item-card} SVG Digitizer
:link: schema/svgdigitizer/index
:link-type: doc
Metadata for digitized data from SVG figures.
:::

:::{grid-item-card} echemdb Package
:link: schema/echemdb_package/index
:link-type: doc
Data package schema for echemdb, composing with the Frictionless Data Package standard.
:::

:::{grid-item-card} SVG Digitizer Package
:link: schema/svgdigitizer_package/index
:link-type: doc
Data package schema for SVG Digitizer output.
:::

::::

## Schema generation

Schemas are generated from LinkML YAML definitions:

```bash
# Generate JSON Schemas
pixi run generate-schemas

# Generate Pydantic models
pixi run generate-models

# Generate both
pixi run generate-all
```

## Validation

Validate example files against the schemas:

```bash
pixi run validate
```

## Schema details

```{toctree}
:maxdepth: 2

schema/autotag/index
schema/minimum_echemdb/index
schema/source_data/index
schema/svgdigitizer/index
schema/echemdb_package/index
schema/svgdigitizer_package/index
```

```bash
pixi run validate
```
