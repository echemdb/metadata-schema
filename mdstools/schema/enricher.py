"""Schema enricher for adding descriptions and examples from JSON Schema to flattened data."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


class SchemaEnricher:
    """
    Enriches flattened YAML data with descriptions and examples from JSON Schema files.

    This class loads JSON Schema files and uses them to add metadata (descriptions and
    examples) to flattened data structures. It automatically prefers resolved schemas
    where all $ref references have been inlined.

    EXAMPLES::

        Basic usage with schemas::

            >>> import os
            >>> os.makedirs('tests/generated', exist_ok=True)
            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')
            >>> 'curation' in enricher.schema_cache
            True

        Enrich a single field path::

            >>> desc, example = enricher.enrich_row('curation.process.role', 'curator')
            >>> 'person' in desc.lower()
            True
            >>> example in ['experimentalist', 'curator', 'reviewer', 'supervisor']
            True

        Enrich with nested objects::

            >>> desc, example = enricher.enrich_row('system.type', 'electrochemical')
            >>> 'system' in desc.lower()
            True
            >>> example == 'electrochemical'
            True
    """

    def __init__(self, schema_dir: str):
        """
        Initialize the enricher with a directory containing JSON Schema files.

        :param schema_dir: Path to the directory containing generated JSON Schema files.
        """
        self.schema_dir = Path(schema_dir)
        self.schema_cache = {}
        self._load_schemas()

    @staticmethod
    def _normalize_defs(schema):
        r"""
        Ensure both ``definitions`` and ``$defs`` keys exist in a schema.

        Modern JSON Schema (2020-12 / LinkML output) uses ``$defs`` while
        older drafts (draft-07) use ``definitions``.  This helper bridges
        the two by making both keys available, pointing at the same dict.

        :param schema: A loaded JSON schema dict

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> s = {"$defs": {"Foo": {"type": "string"}}}
            >>> SchemaEnricher._normalize_defs(s)
            >>> "definitions" in s and "$defs" in s
            True
            >>> s["definitions"] is s["$defs"]
            True
            >>> s2 = {"definitions": {"Bar": {"type": "integer"}}}
            >>> SchemaEnricher._normalize_defs(s2)
            >>> "$defs" in s2
            True

        """
        if "$defs" in schema and "definitions" not in schema:
            schema["definitions"] = schema["$defs"]
        elif "definitions" in schema and "$defs" not in schema:
            schema["$defs"] = schema["definitions"]

    def _load_schemas(self):
        r"""
        Load all generated JSON schema files from the schema directory.

        Populates :attr:`schema_cache` with schemas keyed by file stem.
        Sub-definitions from each schema are also registered individually.

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')
            >>> len(enricher.schema_cache) > 0
            True
            >>> 'curation' in enricher.schema_cache
            True

        """
        if not self.schema_dir.exists():
            raise ValueError(f"Schema directory not found: {self.schema_dir}")

        self._load_root_schemas()
        self._register_schemas_by_title()

    def _load_root_schemas(self):
        r"""
        Load generated JSON schemas from the root directory and register sub-definitions.

        Each ``.json`` file in the schema directory (e.g. ``schemas/autotag.json``)
        is loaded and any ``$defs`` / ``definitions`` block it contains is
        registered via :meth:`_register_definitions`.

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')
            >>> # Root schemas like 'autotag' are loaded from schemas/
            >>> 'autotag' in enricher.schema_cache
            True
            >>> 'system' in enricher.schema_cache
            True
            >>> 'source' in enricher.schema_cache
            True

        """
        for schema_file in self.schema_dir.glob("*.json"):
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_name = schema_file.stem
                if schema_name not in self.schema_cache:
                    self.schema_cache[schema_name] = json.load(f)
                    self._normalize_defs(self.schema_cache[schema_name])

                    schema_data = self.schema_cache[schema_name]
                    if "definitions" in schema_data:
                        self._register_definitions(schema_data)

    def _register_definitions(self, schema_data):
        r"""
        Register sub-definitions from a schema by their definition name.

        For each entry in the ``definitions`` block, a standalone schema
        wrapper is stored in :attr:`schema_cache` under the definition name.

        :param schema_data: A loaded JSON schema dict with a ``definitions`` key

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')
            >>> # PascalCase definitions are registered directly
            >>> 'Atmosphere' in enricher.schema_cache
            True

        """
        for def_name, def_value in schema_data["definitions"].items():
            if def_name not in self.schema_cache:
                wrapper = {
                    "definitions": {def_name: def_value},
                    "$schema": schema_data.get(
                        "$schema",
                        "http://json-schema.org/draft-07/schema#",
                    ),
                }
                self._normalize_defs(wrapper)
                self.schema_cache[def_name] = wrapper

    def _register_schemas_by_title(self):
        r"""
        Register schemas by definition ``title`` for camelCase key lookup.

        Definitions use a ``title`` field matching the camelCase property key
        (e.g. ``"figureDescription"``).  This step allows the schema to be
        found directly by that property key.

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')
            >>> # The curation schema has title 'curation' on its definition
            >>> 'curation' in enricher.schema_cache
            True
            >>> # camelCase titles like 'figureDescription' are also registered
            >>> 'figureDescription' in enricher.schema_cache
            True

        """
        for schema_name in list(self.schema_cache.keys()):
            schema_data = self.schema_cache[schema_name]
            if "definitions" in schema_data:
                for _def_name, def_value in schema_data["definitions"].items():
                    if not isinstance(def_value, dict):
                        continue
                    title = def_value.get("title", "")
                    if title and title not in self.schema_cache:
                        self.schema_cache[title] = schema_data
                    # Also register a camelCase variant so that PascalCase
                    # titles (e.g. "FigureDescription") are reachable via
                    # property keys (e.g. "figureDescription").
                    if title:
                        camel = title[0].lower() + title[1:]
                        if camel != title and camel not in self.schema_cache:
                            self.schema_cache[camel] = schema_data

    def _resolve_ref(
        self, ref: str, current_schema: Dict
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        r"""
        Resolve a ``$ref`` reference to its definition.

        Handles both internal references (``#/definitions/Foo``) and relative
        external references (``./general/url.json#/definitions/Url``).

        :param ref: The $ref string (e.g., ``"#/definitions/Process"``)
        :param current_schema: The current schema dict used for internal refs
        :return: Tuple of ``(resolved_definition, root_schema)``
                 or ``(None, None)`` if the reference cannot be resolved

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Resolve an internal ``#/definitions/...`` reference::

                >>> schema = {'definitions': {'Foo': {'type': 'string'}}}
                >>> resolved, root = enricher._resolve_ref('#/definitions/Foo', schema)
                >>> resolved
                {'type': 'string'}

            Unresolvable references return ``(None, None)``::

                >>> enricher._resolve_ref('#/definitions/Missing', schema)
                (None, None)

            External relative references are resolved from the cache::

                >>> resolved, _ = enricher._resolve_ref(
                ...     './curation.yaml#/definitions/Curation',
                ...     {})
                >>> resolved is not None
                True

        """
        if ref.startswith("#/"):
            # Internal reference - resolve against current schema
            parts = ref[2:].split("/")
            result = current_schema
            for part in parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    return None, None
            return result, current_schema
        if ref.startswith("."):
            # Relative external reference (handles both ./ and ../)
            ref_path = ref.split("#")[0]
            ref_fragment = ref.split("#")[1] if "#" in ref else ""

            # Load the referenced schema by filename stem
            ref_file = ref_path.lstrip("./").replace("/", os.sep)
            ref_schema_name = Path(ref_file).stem

            if ref_schema_name in self.schema_cache:
                ref_schema = self.schema_cache[ref_schema_name]

                if ref_fragment:
                    parts = ref_fragment[1:].split("/")
                    result = ref_schema
                    for part in parts:
                        if isinstance(result, dict) and part in result:
                            result = result[part]
                        else:
                            return None, None
                    # Return resolved def + the external schema as new root
                    return result, ref_schema
                return ref_schema, ref_schema

        return None, None

    def _extract_example(self, current):
        r"""
        Extract an example value from a schema node.

        Looks for ``examples`` (list), ``example`` (scalar), ``const``,
        or ``enum`` fields in order and returns the first match.

        :param current: Schema node dict
        :return: Example value or None

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            From an ``examples`` list (first element is used)::

                >>> enricher._extract_example({'examples': ['mV', 'V', 'A']})
                'mV'

            From a scalar ``example`` field::

                >>> enricher._extract_example({'example': 42})
                42

            From a ``const`` value::

                >>> enricher._extract_example({'const': 'fixed'})
                'fixed'

            From an ``enum`` list (first element is used)::

                >>> enricher._extract_example({'enum': ['red', 'green', 'blue']})
                'red'

            Returns None when no example is available::

                >>> enricher._extract_example({'type': 'string'}) is None
                True

        """
        if (
            "examples" in current
            and isinstance(current["examples"], list)
            and len(current["examples"]) > 0
        ):
            return current["examples"][0]
        if "example" in current:
            return current["example"]
        if "const" in current:
            return current["const"]
        if (
            "enum" in current
            and isinstance(current["enum"], list)
            and len(current["enum"]) > 0
        ):
            return current["enum"][0]
        return None

    def _extract_from_oneof_anyof(self, current):
        r"""
        Extract example and description from ``oneOf`` / ``anyOf`` constructs.

        Scans the alternatives for a ``const`` value and returns the first one
        found, together with its optional description.

        :param current: Schema node dict
        :return: Tuple of (const_value, description) or (None, None)

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            With ``oneOf`` containing const values::

                >>> schema = {'oneOf': [
                ...     {'const': 'red', 'description': 'Red colour'},
                ...     {'const': 'blue', 'description': 'Blue colour'},
                ... ]}
                >>> enricher._extract_from_oneof_anyof(schema)
                ('red', 'Red colour')

            Returns (None, None) when no const is present::

                >>> enricher._extract_from_oneof_anyof({'type': 'string'})
                (None, None)

        """
        for keyword in ("anyOf", "oneOf"):
            if keyword in current and isinstance(current[keyword], list):
                for option in current[keyword]:
                    if "const" in option:
                        return option["const"], option.get("description")
        return None, None

    def _follow_refs(self, current, root_schema):
        r"""
        Follow ``$ref`` chains in a schema node until a concrete node is reached.

        :param current: Schema node (may contain a ``$ref``)
        :param root_schema: Root schema dict for resolving internal refs
        :return: Tuple of ``(resolved_node, root_schema)``

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Nodes without ``$ref`` are returned unchanged::

                >>> node = {'type': 'string', 'description': 'A name'}
                >>> enricher._follow_refs(node, {})
                ({'type': 'string', 'description': 'A name'}, {})

            A ``$ref`` chain is resolved::

                >>> schema = {'definitions': {'Foo': {'type': 'integer'}}}
                >>> ref_node = {'$ref': '#/definitions/Foo'}
                >>> resolved, _ = enricher._follow_refs(ref_node, schema)
                >>> resolved
                {'type': 'integer'}

        """
        while isinstance(current, dict) and "$ref" in current:
            resolved, new_root = self._resolve_ref(current["$ref"], root_schema)
            if resolved:
                current = resolved
                root_schema = new_root
            else:
                break
        return current, root_schema

    def _resolve_array_items(self, current, root_schema):
        r"""
        If *current* is an array schema, resolve and return its ``items`` schema.

        Non-array schemas are returned unchanged.

        :param current: Schema node dict
        :param root_schema: Root schema for resolving refs
        :return: Tuple of ``(items_or_current, root_schema)``

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Array schema — returns the items definition::

                >>> arr = {'type': 'array', 'items': {'type': 'string'}}
                >>> enricher._resolve_array_items(arr, {})
                ({'type': 'string'}, {})

            Non-array schema — returned as-is::

                >>> obj = {'type': 'object', 'properties': {}}
                >>> enricher._resolve_array_items(obj, {})
                ({'type': 'object', 'properties': {}}, {})

        """
        if current.get("type") == "array" and "items" in current:
            items, root_schema = self._follow_refs(current["items"], root_schema)
            return items, root_schema
        return current, root_schema

    def _extract_leaf_metadata(self, current, prop_description):
        r"""
        Extract description and example from a leaf schema node.

        Uses the property-level description as a fallback and tries
        :meth:`_extract_example` followed by :meth:`_extract_from_oneof_anyof`.

        :param current: Resolved schema node
        :param prop_description: Description set on the property reference (may be ``None``)
        :return: Tuple of ``(description, example)``

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Schema with description and examples list::

                >>> node = {'description': 'A voltage', 'examples': ['1.23']}
                >>> enricher._extract_leaf_metadata(node, None)
                ('A voltage', '1.23')

            Falls back to *prop_description* when node has no description::

                >>> node = {'examples': ['mV']}
                >>> enricher._extract_leaf_metadata(node, 'The unit')
                ('The unit', 'mV')

            ``oneOf`` const values used as example::

                >>> node = {'oneOf': [{'const': 'A', 'description': 'Option A'}]}
                >>> enricher._extract_leaf_metadata(node, None)
                ('Option A', 'A')

        """
        description = current.get("description") or prop_description

        example = self._extract_example(current)
        if example is None:
            example, alt_desc = self._extract_from_oneof_anyof(current)
            if not description and alt_desc:
                description = alt_desc

        return description, example

    def _get_field_metadata(
        self, schema: Dict, field_path: list, root_schema: Optional[Dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        r"""
        Extract description and example from a schema for a given field path.

        Walks the ``properties`` tree of *schema* following each element in
        *field_path*, resolving ``$ref`` and array ``items`` along the way.

        :param schema: The schema definition to search within
        :param field_path: List of field names representing the path
        :param root_schema: The root schema containing all definitions
        :return: Tuple of ``(description, example)`` or ``(None, None)``

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Look up a property in a simple schema::

                >>> schema = {
                ...     'properties': {
                ...         'name': {'type': 'string', 'description': 'Full name',
                ...                  'examples': ['Jane']}
                ...     }
                ... }
                >>> enricher._get_field_metadata(schema, ['name'])
                ('Full name', 'Jane')

            Empty field path returns ``(None, None)``::

                >>> enricher._get_field_metadata(schema, [])
                (None, None)

            Missing property returns ``(None, None)``::

                >>> enricher._get_field_metadata(schema, ['nonexistent'])
                (None, None)

        """
        if not field_path:
            return None, None

        current = schema
        if root_schema is None:
            root_schema = schema

        for i, field in enumerate(field_path):
            if not isinstance(current, dict):
                return None, None

            current, root_schema = self._follow_refs(current, root_schema)

            if "properties" not in current or field not in current["properties"]:
                return None, None

            current = current["properties"][field]
            prop_description = current.get("description")
            current, root_schema = self._follow_refs(current, root_schema)

            if i == len(field_path) - 1:
                return self._extract_leaf_metadata(current, prop_description)

            current, root_schema = self._resolve_array_items(current, root_schema)

        return None, None

    def enrich_row(  # pylint: disable=unused-argument
        self, key_path: str, current_value: Any
    ) -> Tuple[Optional[str], Optional[str]]:
        r"""
        Get description and example for a specific field path.

        Splits the dot-separated path, locates the matching top-level schema
        and walks down the definition tree to find the leaf metadata.

        :param key_path: Dot-separated path of keys (e.g., "curation.process.role")
        :param current_value: The current value in the YAML
        :return: Tuple of (description, example) or (None, None)

        EXAMPLES::

            >>> from mdstools.schema.enricher import SchemaEnricher
            >>> enricher = SchemaEnricher('schemas')

            Look up a deeply nested field::

                >>> desc, example = enricher.enrich_row('curation.process.role', 'curator')
                >>> 'person' in desc.lower()
                True
                >>> example in ['experimentalist', 'curator', 'reviewer', 'supervisor']
                True

            Top-level key without remaining path returns (None, None)::

                >>> enricher.enrich_row('curation', '<nested>')
                (None, None)

            Unknown field returns (None, None)::

                >>> enricher.enrich_row('nonexistent.field', 'value')
                (None, None)

            Empty or missing path::

                >>> enricher.enrich_row('', 'value')
                (None, None)

        """
        if not key_path:
            return None, None

        # Split the path and remove empty strings
        parts = [p for p in key_path.split(".") if p]

        if not parts:
            return None, None

        # Try to find the schema for the top-level key
        top_level = parts[0]

        if top_level in self.schema_cache:
            schema = self.schema_cache[top_level]

            # Look for the definition in the schema
            if "definitions" in schema:
                # With consistent naming conventions, the PascalCase definition
                # name is obtained by uppercasing the first letter of the
                # camelCase property key.
                main_def = None
                pascal_name = top_level[0].upper() + top_level[1:]
                if pascal_name in schema["definitions"]:
                    main_def = schema["definitions"][pascal_name]

                if main_def is not None:
                    # Pass the full schema as root_schema for resolving $refs
                    return self._get_field_metadata(
                        main_def, parts[1:], root_schema=schema
                    )

        return None, None

    def enrich_flattened_data(self, flattened_rows: list) -> list:
        r"""
        Enrich flattened YAML rows with description and example columns.

        Takes a list of ``[number, key, value]`` rows and returns a list of
        ``[number, key, value, example, description]`` rows by looking up each
        field in the loaded JSON schemas.

        :param flattened_rows: List of [level, key, value] rows
        :return: List of [level, key, value, example, description] rows

        EXAMPLES::

            Enriching curation metadata::

                >>> from mdstools.schema.enricher import SchemaEnricher
                >>> enricher = SchemaEnricher('schemas')
                >>> rows = [
                ...     ['1', 'curation', '<nested>'],
                ...     ['1.1', 'process', '<nested>'],
                ...     ['1.1.i1', '', '<nested>'],
                ...     ['1.1.i1.1', 'role', 'curator'],
                ...     ['1.1.i1.2', 'name', 'Jane Doe'],
                ... ]
                >>> enriched = enricher.enrich_flattened_data(rows)

            Each enriched row has 5 elements: [number, key, value, example, description]::

                >>> len(enriched[0])
                5

            Leaf fields get descriptions and examples from the schema::

                >>> enriched[3]  # 'role' field
                ['1.1.i1.1', 'role', 'curator', 'experimentalist', 'Role of a person in the data curation process.']

            Non-leaf ``<nested>`` rows may get descriptions too::

                >>> enriched[1][4]  # 'process' description
                'List of people involved in creating, recording, or curating this data.'

            Fields without schema information get empty strings::

                >>> rows_unknown = [['1', 'unknown_field', 'value']]
                >>> enriched_unknown = enricher.enrich_flattened_data(rows_unknown)
                >>> enriched_unknown[0][3:5]
                ['', '']

        """
        enriched = []
        path_stack = []  # Stack of (level_depth, key) tuples

        for row in flattened_rows:
            level, key, value = row

            # Parse level like "1.2.i1.3" to determine depth
            level_parts = level.split(".")
            depth = len(level_parts)

            # Determine if this level is an array item marker (i<n> format)
            is_array_item_marker = (not key or key == "") and value == "<nested>"

            # Update path stack based on depth
            # Remove items that are at same depth or deeper
            while path_stack and path_stack[-1][0] >= depth:
                path_stack.pop()

            # Build path: add key if it exists and is not empty
            # For array items without keys, we don't add to path (skip the 1.1.a level)
            if key and key != "":
                path_stack.append((depth, key))
            elif not is_array_item_marker:
                # This handles the case where we have a value but no key (shouldn't usually happen)
                pass

            # Build the full path (joining all keys in stack)
            full_path = ".".join([k for _, k in path_stack])

            # Get enrichment data
            description, example = self.enrich_row(full_path, value)

            # Add to result
            enriched.append(
                [
                    level,
                    key,
                    value,
                    example if example is not None else "",
                    description if description is not None else "",
                ]
            )

            # For leaf values (not nested), pop the key from stack
            if value != "<nested>":
                if path_stack and path_stack[-1][1] == key and key:
                    path_stack.pop()

        return enriched
