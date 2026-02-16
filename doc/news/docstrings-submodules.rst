**Added:**

* Added ``mdstools/schema/check_naming.py`` to validate naming conventions across all JSON Schema files (camelCase properties, PascalCase definitions, snake_case file names).
* Added ``check-naming`` pixi task, included in ``pixi run validate``.
* Added naming conventions section to ``schemas/README.md``.
* Added ``referencing`` as an explicit dependency.

**Changed:**

* Simplified ``SchemaEnricher._register_definitions`` to register under PascalCase name directly instead of lowercase aliasing.
* Simplified ``SchemaEnricher.enrich_row`` definition lookup from a 3-step fallback to a deterministic camelCase-to-PascalCase mapping.
* Migrated ``validate_metadata`` from deprecated ``jsonschema.RefResolver`` to ``referencing.Registry`` / ``referencing.Resource``.

**Fixed:**

* Fixed ``"title": "scan rate"`` (with space) in ``figure_description.json`` to ``"scanRate"`` (camelCase).
* Fixed ``svgdigitizer_resource`` definition name in ``svgdigitizer_package.json`` to ``SvgdigitizerResource`` (PascalCase).
* Fixed ``DeprecationWarning`` for ``jsonschema.RefResolver`` in ``validator.py``.
