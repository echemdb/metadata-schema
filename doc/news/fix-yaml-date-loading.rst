**Fixed:**

* Fixed validation of YAML metadata containing unquoted dates (e.g.
  ``date: 2021-07-09``): YAML files are now loaded with
  ``MetadataYamlLoader``, which keeps dates and timestamps as plain strings
  instead of ``datetime.date`` objects that fail validation of string-typed
  schema fields (`#123 <https://github.com/echemdb/metadata-schema/issues/123>`_).
