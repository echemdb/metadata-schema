This section contains example descriptors that are used to describe an electrochemical resource in a tabular-data-package.

All metadata schemas are defined as LinkML YAML files in `linkml/` and generated into JSON Schema files in `schemas/`.

## Object Examples (`objects/`)

Individual metadata sections:

* [curation](objects/curation.yaml): Details on the curation process
* [eln](objects/eln.yaml): URL to an electronic lab notebook
* [experimental](objects/experimental.yaml): Descriptor supporting `system.yaml`, e.g., contains a list of instruments
* [figure_description](objects/figure_description.yaml): Contains mainly axis properties
* [projects](objects/projects.yaml): List of projects related to the source data
* [source](objects/source.yaml): Source of published data
* [system](objects/system.yaml): Details describing the experimental vessel

## File Schema Examples (`file_schemas/`)

Complete metadata files matching the generated schemas:

* [autotag.yaml](file_schemas/autotag.yaml): Complete metadata for YAML templates used by [autotag-metadata](https://echemdb.github.io/autotag-metadata/)
* [minimum_echemdb.yaml](file_schemas/minimum_echemdb.yaml): Minimum metadata set for echemdb
* [source_data.yaml](file_schemas/source_data.yaml): Source data with data description
* [svgdigitizer.yaml](file_schemas/svgdigitizer.yaml): Digitizer output metadata
* [echemdb_package.json](file_schemas/echemdb_package.json): Data package for echemdb
* [svgdigitizer_package.json](file_schemas/svgdigitizer_package.json): Data package for svgdigitizer

## Recording raw data

The experimentalist is encouraged to record the following descriptors along with raw data:

* curation
* eln
* experimental
* figureDescription
* project
* system

## Submission to echemdb/website

Data for the [echemdb/website]() can be submitted as a datapackage (JSON) and CSV, YAML and SVG or YAML and CSV.
In any case the files should be named:
`Author_YYYY_FirstTitleWord_Page_fignr_identifier` such as `mustermann_2022_electrochemical_1345_1b_solid`. The name should be lower case.

**Submitting a YAML with an SVG**
The YAML must contain the following descriptors:

* curation
* experimental
* source
* system

**Submitting a YAML with a CSV**

* curation
* experimental
* figureDescription
* source
* system

## Validation

Validate all examples against the generated schemas:

```bash
pixi run validate
```
