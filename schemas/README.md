# Metadata Schemas

This directory contains JSON Schema files for echemdb metadata validation.

## Directory Structure

### Source of Truth: `linkml/`

All metadata schemas are defined as **LinkML YAML** files under `linkml/` (project root).
JSON Schema and Pydantic models are generated from these definitions.

### `schema_pieces/`

Legacy modular YAML schema definitions (kept for reference). These are organized into:
- `general/` - Reusable components (quantity, url, purity, etc.)
- `system/` - Electrochemical system components (electrode, electrolyte, atmosphere, etc.)
- `experimental/` - Experimental setup components (instrumentation)

### Root Directory (this folder)

Generated JSON schemas ready for distribution and use. These schemas:

- Are self-contained with all definitions in a `$defs` section
- Keep only internal references (`#/$defs/...`)
- Are generated automatically from LinkML using `pixi run generate-schemas`
- **Work for both validation AND enrichment** (descriptions/examples are preserved)

## Main Combined Schemas

The following combined schemas are available as both development (in `schema_pieces/`) and resolved (in root) versions:

- **`autotag.json`** - Complete metadata schema for auto-generated echemdb YAML files. Combines all metadata sections (curation, eln, experimental, figureDescription, system, project).

- **`svgdigitizer.json`** - Metadata schema for digitized data from figures using svgdigitizer. Similar to autotag but includes `source` instead of `project`.

- **`echemdb_package.json`** - Data package schema following Frictionless Data Package standard with echemdb extensions for bundling metadata and data files.

- **`svgdigitizer_package.json`** - Simplified data package for svgdigitizer output with minimal metadata requirements.

## Usage

### Validate examples

```bash
pixi run validate-objects
pixi run validate-file-schemas
pixi run validate-package-schemas
# or all at once:
pixi run validate
```

### Validate YAML against a schema

```bash
check-jsonschema --schemafile schemas/autotag.json yourfile.yaml
```

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
