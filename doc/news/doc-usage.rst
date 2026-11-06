**Fixed:**

* Fixed the documentation of ``mdstools flatten``: the options are ``--schema-dir``, ``--output-dir`` and ``--no-enrichment``, all output files are listed, and the enrichment with descriptions and examples from the JSON Schemas is explained.
* Fixed the validation example in the usage documentation, which imported the non-existent ``validate_with_json_schema``. It now shows ``validate_metadata``, ``validate`` and ``validate_with_pydantic``.
