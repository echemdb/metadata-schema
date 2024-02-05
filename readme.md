# Metadata Schema

Development of a metadata schema for experimental data, sepcifically electrochemical and electrocatalytic data.

## Development
It it possible to validate metadata files (e.g. of type json or yaml) against the schemas locally. You can use the python package `check-jsonschema` for example.
This is achieved by omitting the `$id` tag in this repository. It is set to a absolute url upon release.
- check a single file

  `check-jsonschema --base-uri <path to schemas> --schemafile <path to schema>/<some schema>.json <file to validate>`
- validate all files in a directory (inlcuding subdirectories)

  `find <path to metadata files> -name "*.<file extension>" -exec echo {} \; -exec check-jsonschema --base-uri <path to schemas> --schemafile <path to schema>/<some schema>.json {} \;`
