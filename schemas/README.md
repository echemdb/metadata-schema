# Metadata Schemas

This directory contains JSON Schema files for echemdb metadata validation.

## Directory Structure

### Source of Truth: `linkml/`

All metadata schemas are defined as **LinkML YAML** files under `linkml/` (project root).
JSON Schema and Pydantic models are generated from these definitions.

### `frictionless/` (gitignored)

Frictionless Data Package standard schemas (`datapackage.json`, `dataresource.json`),
downloaded on demand from <https://datapackage.org/profiles/2.0/>.

Package schemas (`echemdb_package.json`, `svgdigitizer_package.json`) reference
the canonical Frictionless Data Resource URL so that standard resource
properties (name, path, format, encoding, …) are accepted alongside our custom
metadata.

The files are **not tracked in version control**.  They are fetched automatically
by `ensure_frictionless_schemas()` on the first schema generation or package
validation run and cached locally for all subsequent offline use.

### Root Directory (this folder)

Generated JSON schemas ready for distribution and use. These schemas:

- Are self-contained with all definitions in a `$defs` section
- Keep only internal references (`#/$defs/...`)
- Are generated automatically from LinkML using `pixi run generate-schemas`
- **Work for both validation AND enrichment** (descriptions/examples are preserved)

## Generated Schemas

The following schemas are generated from LinkML definitions:

- **`minimum_echemdb.json`** - Minimum metadata set for echemdb entries.

- **`autotag.json`** - Complete metadata schema for YAML templates used by [autotag-metadata](https://echemdb.github.io/autotag-metadata/). Combines all metadata sections (curation, eln, experimental, figureDescription, system, project).

- **`source_data.json`** - Source data with data description (CSV dialect, field mapping, field units).

- **`svgdigitizer.json`** - Metadata schema for digitized data from figures using svgdigitizer. Similar to autotag but includes `source` instead of `project`.

- **`echemdb_package.json`** - Data package schema following Frictionless Data Package standard with echemdb extensions for bundling metadata and data files. References the Frictionless data resource schema via `allOf`.

- **`svgdigitizer_package.json`** - Simplified data package for svgdigitizer output with minimal metadata requirements. References the Frictionless data resource schema via `allOf`.

## Usage

### Validate examples

```bash
pixi run validate-objects          # Individual object examples
pixi run validate-file-schemas     # File-level YAML examples
pixi run validate-package-schemas  # Package JSON examples (auto-downloads Frictionless schemas)
# or all at once:
pixi run validate
```

### Validate YAML against a schema

```bash
check-jsonschema --schemafile schemas/autotag.json yourfile.yaml
```

> **Note**: Package schemas (`echemdb_package.json`, `svgdigitizer_package.json`)
> use the Frictionless profile URL for `$ref`. `pixi run validate-package-schemas`
> remains the recommended entry point because it registers local cached copies
> for offline validation.

### Regenerating Schemas from LinkML

After editing LinkML files in `linkml/`, regenerate JSON schemas and Pydantic models:

```bash
pixi run generate-schemas        # JSON Schema only
pixi run generate-models          # Pydantic models only
pixi run generate-all             # Both
pixi run update-expected-schemas  # Update snapshot baselines
```

## Schema Enrichment

Schemas include human-readable descriptions and examples to aid in documentation and user guidance. Use the enrichment tools to add descriptions to Excel exports:

```bash
pixi run flatten
```

## Naming Conventions

| Layer | Convention | Examples |
|---|---|---|
| **File names** | `snake_case.json` | `figure_description.json`, `source_data.json` |
| **Definition names** (`definitions`) | `PascalCase` | `FigureDescription`, `ElectrochemicalCell`, `ScanRate` |
| **Property keys** (YAML dict keys) | `camelCase` | `figureDescription`, `scanRate`, `measurementType` |

**Rules:**

- **Property keys**: Start lowercase, no underscores, no spaces → `^[a-z][a-zA-Z0-9]*$`
- **Definition names**: Start uppercase, no underscores, no spaces → `^[A-Z][a-zA-Z0-9]*$`
- **File names**: All lowercase with underscores → `^[a-z][a-z0-9_]*\.json$`
- Single-word names (e.g., `curation`, `source`) satisfy all conventions naturally

Enforced by `pixi run check-naming` (runs as part of `pixi run validate`).

## Contributing

When modifying schemas:

1. Edit LinkML YAML files in `linkml/` directory
2. Add descriptions and examples to all new fields
3. Follow the [naming conventions](#naming-conventions) above
4. Run `pixi run generate-all` to regenerate JSON schemas and Pydantic models
5. Run `pixi run check-naming` to verify naming rules
6. Run `pixi run validate` to ensure all validations pass
7. Run `pixi run update-expected-schemas` to update snapshot baselines
8. Run `pixi run test` to verify everything works
