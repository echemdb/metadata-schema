# Metadata Schemas

This directory contains JSON Schema files for echemdb metadata validation.

## Directory Structure

### `schema_pieces/`

Development schemas with modular structure using `$ref` references. These schemas:

- Reference each other using relative paths (e.g., `curation.json#/definitions/Curation`)
- Reference external standards (e.g., Frictionless Data Schema)
- Are organized into subdirectories:
  - `general/` - Reusable components (quantity, url, purity, etc.)
  - `system/` - Electrochemical system components (electrode, electrolyte, atmosphere, etc.)
  - `experimental/` - Experimental setup components (instrumentation)
- Serve as the single source of truth for schema definitions

### Root Directory (this folder)

Resolved/flattened schemas ready for distribution and use. These schemas:

- Have all external `$ref` references resolved and inlined
- Contain all definitions in a single `definitions` section
- Keep only internal references (`#/definitions/...`)
- Are generated automatically from `schema_pieces/` using `pixi run resolve-schemas`
- **Work for both validation AND enrichment** (descriptions/examples are preserved)

## Main Combined Schemas

The following combined schemas are available as both development (in `schema_pieces/`) and resolved (in root) versions:

- **`autotag.json`** - Complete metadata schema for auto-generated echemdb YAML files. Combines all metadata sections (curation, eln, experimental, figureDescription, system, project).

- **`svgdigitizer.json`** - Metadata schema for digitized data from figures using svgdigitizer. Similar to autotag but includes `source` instead of `project`.

- **`echemdb_package.json`** - Data package schema following Frictionless Data Package standard with echemdb extensions for bundling metadata and data files.

- **`svgdigitizer_package.json`** - Simplified data package for svgdigitizer output with minimal metadata requirements.

## Usage

### For Development

Work with schemas in `schema_pieces/` directory:

```bash
# Validate against development schemas
pixi run validate-objects
pixi run validate-file-schemas
pixi run validate-package-schemas
```

### For Distribution

Use resolved schemas in root directory:

```bash
# Validate YAML against resolved schema
check-jsonschema --schemafile schemas/autotag.json yourfile.yaml
```

### Regenerating Resolved Schemas

After making changes to schemas in `schema_pieces/`, regenerate resolved versions:

```bash
pixi run resolve-schemas
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

1. Edit schemas in `schema_pieces/` directory only
2. Add descriptions and examples to all new fields
3. Follow the [naming conventions](#naming-conventions) above
4. Run `pixi run check-naming` to verify naming rules
5. Run `pixi run resolve-schemas` to update resolved versions
6. Run `pixi run validate` to ensure all validations pass
7. Run `pixi run test-comprehensive` to verify enrichment still works
