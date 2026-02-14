**Added:**

* Added the ``mdstools`` Python package with CLI, metadata flattening/unflattening,
  schema enrichment, schema resolution, and validation utilities.
* Added ``minimum_echemdb`` schema for a minimum set of metadata required by
  the echemdb database.
* Added ``source_data`` schema for source data files including ``data_description``
  schema piece (CSV dialect, field mapping, and field units).
* Added CI workflows for linting, testing, and example validation.
* Added resolved single-file schemas with all ``$ref`` references inlined for
  distribution and snapshot testing against expected baselines.
* Added YAML example files for ``minimum_echemdb`` and ``source_data`` schemas.

**Changed:**

* Updated ``pyproject.toml`` with ``mdstools`` package dependencies and pixi task
  definitions for development, testing, linting, and validation.
* Updated README with usage documentation for the CLI and Python API.
