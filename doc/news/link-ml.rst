**Added:**

* Added LinkML YAML schemas under ``linkml/`` as single source of truth for all metadata definitions.
* Added ``mdstools/schema/generate_from_linkml.py`` to generate JSON Schema and Pydantic models from LinkML.
* Added auto-generated Pydantic models under ``mdstools/models/`` with permissive validation (``extra="allow"``, ``coerce_numbers_to_str=True``).
* Added ``validate_with_pydantic()`` in ``mdstools/schema/validator.py`` for Pydantic-based metadata validation.
* Added snapshot testing for generated schemas via ``mdstools/test/test_resolved_schemas.py``.
* Added pixi tasks: ``generate-schemas``, ``generate-models``, ``generate-all``.
* Added ``linkml`` and ``linkml-runtime`` as dependencies.

**Changed:**

* ``SchemaEnricher`` updated to handle both ``$defs`` (LinkML) and ``definitions`` (legacy) JSON Schema formats.
* ``check_naming.py`` refactored and updated to validate YAML schema pieces.
* Schema pieces (``schemas/schema_pieces/``) converted from JSON to YAML.
* All 6 resolved JSON schemas regenerated from LinkML definitions.
* ``schemas/README.md`` updated with LinkML-based workflow.

**Removed:**

* Removed ``mdstools/schema/resolver.py`` legacy schema resolver (replaced by ``generate_from_linkml.py``).
* Removed JSON schema pieces (replaced by YAML versions and LinkML definitions).
* Remove support for Python 3.10 in CI testing (minimum supported version is now Python 3.11).
