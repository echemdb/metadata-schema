**Changed:**

* Replaced custom ``$ref`` resolution in the schema enricher with the ``jsonref`` library.
  The ``SchemaEnricher`` now resolves all ``$ref`` at load time via ``jsonref.replace_refs()``,
  removing ~95 lines of hand-written ref-walking code (``_resolve_ref``, ``_follow_refs``).
  External Frictionless URLs are mapped to locally cached schema files.
