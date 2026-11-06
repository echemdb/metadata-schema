# echemdb metadata-schema

Metadata schemas to describe electrochemical systems and the collected data, developed within
the [echemdb](https://www.echemdb.org) community project.

**Documentation: <https://echemdb.github.io/metadata-schema/>**

## Schemas

The schemas cover the electrochemical system (electrodes, electrolyte, cell), the experimental
setup, the source of the data and its curation. They are defined in [LinkML](https://linkml.io)
(`linkml/`), the single source of truth, from which we generate

- JSON Schemas (`schemas/`), to validate metadata with any tool that supports JSON Schema, and
- Pydantic models (`mdstools/models/`).

The schema reference, example files and JSON Schema downloads are on the
[documentation website](https://echemdb.github.io/metadata-schema/metadata.html).

## mdstools

The `mdstools` Python package works with metadata files: it flattens them to Excel or CSV,
enriches them with descriptions and examples from the schemas, validates them, and migrates
them to newer schema versions.

### Installation

Install [pixi](https://pixi.sh), then

```sh
git clone https://github.com/echemdb/metadata-schema.git
cd metadata-schema
pixi install
```

### Usage

```sh
# Flatten a YAML file to enriched Excel and CSV files in generated/
mdstools flatten tests/example_metadata.yaml

# Convert an Excel or CSV file back to YAML
mdstools unflatten generated/example_metadata.xlsx --schema-file schemas/minimum_echemdb.json

# Migrate a metadata file to the current schema version (dry run without --in-place)
mdstools update metadata.yaml --in-place
```

Run `mdstools <command> --help` for all options, or prefix the commands with `pixi run` to use
the pixi environment. The CLI, the Python API and the schema generation are described in the
[documentation](https://echemdb.github.io/metadata-schema/tools.html).

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the setup, the workflow
for schema changes and migrations, and the checks:

```sh
pixi install -e dev
pixi run test
pixi run validate
pixi run lint
pixi run check-news
pixi run doc-fast    # build the documentation in doc/generated/html
```

## License

[GPL-3.0-or-later](LICENSE)
