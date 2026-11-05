# Schema Reference

The schemas describe electrochemical data: the electrochemical system (electrodes, electrolyte, cell, atmosphere), the experimental setup and instrumentation, the source of the data, its curation, and the description of digitized figures. They are combined into the schema types below, each made for a specific use.

How the schemas are built and generated is described in [Schema Generation](generation.md).

## Available schemas

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
