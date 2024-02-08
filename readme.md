# Metadata Schema

Development of a metadata schema for experimental data, sepcifically electrochemical and electrocatalytic data.

## Development

The metadata files (e.g. of type JSON or YAML) can be validated against the schemas locally using, for example, the Python package [`check-jsonschema`](https://github.com/python-jsonschema/check-jsonschema).
In that case, the `$id` tag in the schemas pointing to this repository must be bypassed by setting an absolute URL to the respective local files.

- validate a single file

```sh
check-jsonschema --base-uri <path to schemas> --schemafile <path to schema>/<some schema>.json <file to validate>
```

- validate all files in a directory (including subdirectories)

```sh
find <path to metadata files> -name "*.<file extension>" -exec echo {} \; -exec check-jsonschema --base-uri <path to schemas> --schemafile <path to schema>/<some schema>.json {} \;`
```
