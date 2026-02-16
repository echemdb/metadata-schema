**Added:**

* Added LinkML YAML schemas under ``linkml/`` as single source of truth for all metadata definitions.
* Added ``mdstools/schema/generate_from_linkml.py`` to generate JSON Schema and Pydantic models from LinkML.
* Added ``ensure_frictionless_schemas()`` to auto-download Frictionless Data Package schemas on demand into ``schemas/frictionless/`` (gitignored).
* Added Frictionless Data Package composition for package schemas (``echemdb_package.json``, ``svgdigitizer_package.json``): resource items use ``allOf`` with local ``frictionless/dataresource.json``.
* Added ``validate_package_schemas()`` in ``mdstools/schema/validate_examples.py`` for Python-based package schema validation with local Frictionless registry.
* Added auto-generated Pydantic models under ``mdstools/models/`` with permissive validation (``extra="allow"``, ``coerce_numbers_to_str=True``).
* Added ``validate_with_pydantic()`` in ``mdstools/schema/validator.py`` for Pydantic-based metadata validation.
* Added snapshot testing for generated schemas via ``mdstools/test/test_resolved_schemas.py``.
* Added ``bibdata`` attribute to ``SvgdigitizerSource`` in LinkML.
* Added pixi tasks: ``generate-schemas``, ``generate-models``, ``generate-all``.
* Added ``linkml`` and ``linkml-runtime`` as dependencies.

**Changed:**

* Changed ``Quantity.value`` range from ``string`` to ``float`` in LinkML.
* Changed ``Purity.value`` range from ``string`` to ``float`` in LinkML.
* Updated ``Quantity.unit`` and ``Uncertainty.unit`` descriptions to reference astropy string notation; dimensionless quantities use an empty string.
* ``SchemaEnricher`` updated to handle both ``$defs`` (LinkML) and ``definitions`` (legacy) JSON Schema formats.
* ``check_naming.py`` refactored and updated to validate YAML schema pieces.
* Schema pieces (``schemas/schema_pieces/``) converted from JSON to YAML.
* All 6 resolved JSON schemas regenerated from LinkML definitions.
* ``schemas/README.md`` updated with LinkML-based workflow and Frictionless documentation.
* ``validate-package-schemas`` pixi task switched from ``check-jsonschema`` CLI to Python-based validation.
* Fixed swapped ``value``/``unit`` in ``partialPressure`` quantities across example files (``autotag.yaml``, ``svgdigitizer.yaml``, ``system.yaml``).

**Removed:**

* Removed ``mdstools/schema/resolver.py`` legacy schema resolver (replaced by ``generate_from_linkml.py``).
* Removed JSON schema pieces (replaced by YAML versions and LinkML definitions).
* Remove support for Python 3.10 in CI testing (minimum supported version is now Python 3.11).
