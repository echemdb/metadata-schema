#!/usr/bin/env python
"""
Utility to resolve all $ref references in JSON schemas and create consolidated schemas.

This script loads JSON Schema files and resolves all external $ref references,
creating "resolved" versions where all definitions are inlined into a single file.
This makes schema parsing more reliable and efficient.

Usage:
    python mdstools/schema/resolver.py

The resolved schemas are saved to schemas/ directory.

EXAMPLES::

    Basic usage from Python::

        >>> import os
        >>> os.makedirs('schemas/resolved', exist_ok=True)
        >>> from mdstools.schema.resolver import SchemaResolver
        >>> resolver = SchemaResolver('schemas')
        >>> 'curation' in resolver.schema_cache
        True

    Resolve a schema::

        >>> if 'curation' in resolver.schema_cache:
        ...     resolved = resolver.resolve_all_refs('curation')
        ...     'definitions' in resolved
        ... else:
        ...     True  # Skip if schema not found
        True
"""

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

import yaml


class SchemaResolver:  # pylint: disable=too-few-public-methods
    r"""
    Resolves all ``$ref`` references in JSON schemas.

    Loads all modular schema pieces from ``schema_dir/schema_pieces/`` and
    provides :meth:`resolve_all_refs` to produce single-file resolved schemas
    with all external references inlined.

    EXAMPLES::

        >>> from mdstools.schema.resolver import SchemaResolver
        >>> resolver = SchemaResolver('schemas')
        >>> 'curation' in resolver.schema_cache
        True
        >>> 'system' in resolver.schema_cache
        True

    """

    @staticmethod
    def _snake_to_pascal(name: str) -> str:
        """Convert a snake_case name to PascalCase."""
        return "".join(part.capitalize() for part in name.split("_"))

    def __init__(self, schema_dir: str):
        self.schema_dir = Path(schema_dir)
        self.schema_cache = {}
        self._load_schemas()

    def _load_schemas(self):
        r"""
        Load all YAML schema files from the ``schema_pieces/`` subdirectory.

        Each file is stored in :attr:`schema_cache` under both its stem
        (e.g. ``"curation"``) and its relative path (e.g. ``"general/url.yaml"``).
        YAML schemas are wrapped in a ``{"definitions": ...}`` structure to
        match the expected JSON Schema format.

        :raises FileNotFoundError: If the ``schema_pieces/`` directory does not exist

        EXAMPLES::

            >>> from mdstools.schema.resolver import SchemaResolver
            >>> resolver = SchemaResolver('schemas')
            >>> 'curation' in resolver.schema_cache
            True
            >>> 'system' in resolver.schema_cache
            True

        """
        schema_pieces_dir = self.schema_dir / "schema_pieces"
        if not schema_pieces_dir.exists():
            raise FileNotFoundError(
                f"Schema pieces directory not found: {schema_pieces_dir}"
            )

        for schema_file in schema_pieces_dir.rglob("*.yaml"):
            with open(schema_file, "r", encoding="utf-8") as schema_f:
                schema_stem = schema_file.stem
                relative_path = schema_file.relative_to(schema_pieces_dir)
                raw = yaml.safe_load(schema_f)
                # Wrap flat YAML definitions into JSON Schema structure.
                # Files that already have 'definitions' (e.g. package schemas)
                # are kept as-is; files with 'type'/'properties' are standard
                # schemas that get wrapped as a single definition; otherwise
                # all top-level keys are flat PascalCase definitions.
                if "definitions" in raw:
                    schema_data = {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        **raw,
                    }
                elif "type" in raw or "properties" in raw:
                    # Standard schema (e.g. schema.yaml) — wrap as one definition
                    main_def = self._snake_to_pascal(schema_stem)
                    schema_data = {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "definitions": {main_def: raw},
                        "allOf": [{"$ref": f"#/definitions/{main_def}"}],
                    }
                else:
                    # Flat YAML: top-level keys are PascalCase definitions
                    main_def = self._snake_to_pascal(schema_stem)
                    schema_data = {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "definitions": raw,
                    }
                    # Add allOf entry point if the inferred definition exists
                    if main_def in raw:
                        schema_data["allOf"] = [{"$ref": f"#/definitions/{main_def}"}]
                self.schema_cache[schema_stem] = schema_data
                self.schema_cache[str(relative_path)] = self.schema_cache[schema_stem]

    def _resolve_ref(
        self, ref: str, base_schema_path: str = None
    ) -> (
        Any
    ):  # pylint: disable=unused-argument,too-many-return-statements,too-many-branches
        r"""
        Resolve a single ``$ref`` reference string.

        Handles internal (``#/...``), relative (``./...``, ``../...``), and
        filename-based (``curation.json#/...``) references.  HTTP(S) URLs are
        left unresolved.  Returns the original ``{"$ref": ref}`` dict when
        resolution is not possible.

        :param ref: The ``$ref`` string
        :param base_schema_path: Base path for relative lookups (currently unused)
        :return: Resolved schema fragment, or the original ``$ref`` dict

        EXAMPLES::

            >>> from mdstools.schema.resolver import SchemaResolver
            >>> resolver = SchemaResolver('schemas')

            HTTP URLs are preserved unchanged::

                >>> resolver._resolve_ref('https://example.com/schema.json')
                {'$ref': 'https://example.com/schema.json'}

            Internal ``#/`` refs are preserved (need context to resolve)::

                >>> resolver._resolve_ref('#/definitions/Foo')
                {'$ref': '#/definitions/Foo'}

            Relative path references are resolved from the cache::

                >>> result = resolver._resolve_ref('./curation.yaml#/definitions/Curation')
                >>> isinstance(result, dict) and '$ref' not in result
                True

        """
        # Skip external URLs (like frictionless schema)
        if ref.startswith("http://") or ref.startswith("https://"):
            return {"$ref": ref}

        if ref.startswith("#/"):
            # Internal reference - can't resolve without context
            return {"$ref": ref}

        # Handle references with filename and fragment (e.g., "curation.yaml#/definitions/Curation")
        if (
            ".yaml#" in ref
            or ref.endswith(".yaml")
            or ".json#" in ref
            or ref.endswith(".json")
        ):
            ref_path = ref.split("#")[0]
            ref_fragment = "#" + ref.split("#")[1] if "#" in ref else ""

            # Get schema name from path
            ref_schema_name = Path(ref_path).stem

            if ref_schema_name in self.schema_cache:
                ref_schema = copy.deepcopy(self.schema_cache[ref_schema_name])

                if ref_fragment and ref_fragment != "#":
                    # Navigate to the specific definition
                    parts = ref_fragment[2:].split("/")  # Skip "#/"
                    result = ref_schema
                    for part in parts:  # pylint: disable=duplicate-code
                        if isinstance(result, dict) and part in result:
                            result = result[part]
                        else:
                            return {"$ref": ref}  # Can't resolve
                    # Recursively resolve any $refs within the result
                    return self._resolve_schema(result, "")
                # Recursively resolve the whole schema
                return self._resolve_schema(ref_schema, "")

        elif ref.startswith("./") or ref.startswith("../"):
            # Relative path reference
            ref_path = ref.split("#")[0]
            ref_fragment = ref.split("#")[1] if "#" in ref else ""

            # Load the referenced schema
            # Normalize path by removing leading ./ and handling ../
            ref_file = ref_path.lstrip("./")
            # Try to find in cache with both forward slash path and stem
            ref_file_normalized = ref_file.replace("/", os.sep)
            ref_schema_name = Path(ref_file).stem

            # Try multiple lookup strategies
            ref_schema = None
            if ref_file_normalized in self.schema_cache:
                ref_schema = copy.deepcopy(self.schema_cache[ref_file_normalized])
            elif ref_schema_name in self.schema_cache:
                ref_schema = copy.deepcopy(self.schema_cache[ref_schema_name])

            if ref_schema is not None:
                # Resolve any $refs within the referenced schema
                ref_schema = self._resolve_schema(
                    ref_schema, str(Path(ref_file).parent)
                )

                if ref_fragment:
                    # Navigate to the specific definition
                    parts = ref_fragment[1:].split("/")
                    result = ref_schema
                    for part in parts:  # pylint: disable=duplicate-code
                        if isinstance(result, dict) and part in result:
                            result = result[part]
                        else:
                            return {"$ref": ref}  # Can't resolve
                    return result
                # No fragment specified
                return ref_schema

        # Can't resolve reference
        return {"$ref": ref}

    # pylint: disable=too-many-return-statements
    def _resolve_schema(self, schema: Any, base_path: str = "", depth: int = 0) -> Any:
        r"""
        Recursively resolve all ``$ref`` entries in a schema tree.

        Walks dicts and lists, replacing every resolvable ``$ref`` with its
        inlined content.  A *depth* guard prevents infinite recursion.

        :param schema: Schema node (dict, list, or scalar)
        :param base_path: Base directory for relative ref resolution
        :param depth: Current recursion depth (max 20)
        :return: Schema with ``$ref`` entries resolved where possible

        EXAMPLES::

            >>> from mdstools.schema.resolver import SchemaResolver
            >>> resolver = SchemaResolver('schemas')

            Scalars and plain dicts pass through unchanged::

                >>> resolver._resolve_schema('hello')
                'hello'
                >>> resolver._resolve_schema({'type': 'string'})
                {'type': 'string'}

            A resolvable ``$ref`` is replaced::

                >>> result = resolver._resolve_schema(
                ...     {'$ref': './curation.json#/definitions/Curation'})
                >>> '$ref' not in result
                True

        """
        # Prevent infinite recursion
        if depth > 20:
            return schema

        if isinstance(schema, dict):
            if "$ref" in schema and len(schema) == 1:
                # This is a pure $ref, resolve it
                resolved = self._resolve_ref(schema["$ref"], base_path)
                # Check if we actually resolved something
                if "$ref" not in resolved or resolved["$ref"] != schema["$ref"]:
                    # Successfully resolved - recursively resolve the result
                    return self._resolve_schema(resolved, base_path, depth + 1)
                return schema
            if "$ref" in schema:
                # Mixed $ref with other properties
                resolved_ref = self._resolve_ref(schema["$ref"], base_path)
                result = copy.deepcopy(schema)
                del result["$ref"]

                if "$ref" not in resolved_ref or resolved_ref["$ref"] != schema["$ref"]:
                    # Successfully resolved
                    if isinstance(resolved_ref, dict):
                        resolved_ref = self._resolve_schema(
                            resolved_ref, base_path, depth + 1
                        )
                        # Merge properties (properties in schema override resolved ones)
                        resolved_ref.update(result)
                        return resolved_ref
                return schema
            # No $ref in schema, recursively process all properties
            return {
                k: self._resolve_schema(v, base_path, depth + 1)
                for k, v in schema.items()
            }

        if isinstance(schema, list):
            return [self._resolve_schema(item, base_path, depth + 1) for item in schema]

        return schema

    def resolve_all_refs(
        self, schema_name: str
    ) -> Dict:  # pylint: disable=too-many-locals
        r"""
        Resolve all external ``$ref`` references in a schema, keeping internal refs.

        Loads the named schema from the cache, resolves every external
        ``$ref`` (relative file paths), strips ``$id`` fields, and collects
        only the definitions that are actually referenced.

        :param schema_name: Name of the schema file (without .json)
        :return: Resolved schema with all definitions inlined

        EXAMPLES::

            >>> from mdstools.schema.resolver import SchemaResolver
            >>> resolver = SchemaResolver('schemas')

            Resolve a schema and check the result is valid JSON Schema::

                >>> resolved = resolver.resolve_all_refs('curation')
                >>> '$schema' in resolved
                True
                >>> 'definitions' in resolved
                True

            The resolved schema contains inlined definitions::

                >>> 'Curation' in resolved['definitions'] or 'Process' in resolved['definitions']
                True

            Unknown schema names raise ``ValueError``::

                >>> try:
                ...     resolver.resolve_all_refs('nonexistent')
                ... except ValueError as e:
                ...     'not found' in str(e).lower()
                True

        """
        if schema_name not in self.schema_cache:
            raise ValueError(f"Schema '{schema_name}' not found")

        schema = copy.deepcopy(self.schema_cache[schema_name])

        # Track which definitions are actually used
        used_definitions = set()

        def collect_refs(obj):
            """Recursively find all definition references in the schema."""
            if isinstance(obj, dict):
                if "$ref" in obj:
                    ref = obj["$ref"]
                    # Check if it's a definitions reference
                    if ref.startswith("#/definitions/"):
                        def_name = ref.split("/")[-1]
                        used_definitions.add(def_name)
                for value in obj.values():
                    collect_refs(value)
            elif isinstance(obj, list):
                for item in obj:
                    collect_refs(item)

        # Now resolve all external $refs in the schema recursively
        # Pass empty base_path since we're starting from schema_pieces/ root
        resolved_schema = self._resolve_schema(schema, base_path="", depth=0)

        # Collect references from the resolved schema
        collect_refs(resolved_schema)

        # Remove $id fields from resolved content to avoid scope issues in validators
        resolved_schema = self._remove_schema_ids(resolved_schema)

        # Collect only the definitions that are actually referenced
        needed_definitions = {}
        definitions_to_check = list(used_definitions)
        checked_definitions = set()

        while definitions_to_check:
            def_name = definitions_to_check.pop(0)
            if def_name in checked_definitions:
                continue
            checked_definitions.add(def_name)

            # Find this definition in any cached schema
            found = False
            for _, cached_schema in self.schema_cache.items():
                if isinstance(cached_schema, dict) and "definitions" in cached_schema:
                    if def_name in cached_schema["definitions"]:
                        # Resolve $refs within this definition
                        resolved_def = self._resolve_schema(
                            cached_schema["definitions"][def_name],
                            base_path="",
                            depth=0,
                        )
                        # Remove $id from definitions to avoid scope issues
                        clean_def = self._remove_schema_ids(resolved_def)
                        needed_definitions[def_name] = clean_def

                        # Check if this definition references other definitions
                        collect_refs(resolved_def)
                        new_refs = used_definitions - checked_definitions
                        definitions_to_check.extend(new_refs)

                        found = True
                        break

            if not found and def_name not in needed_definitions:
                # Definition might already be in the schema's own definitions
                if "definitions" in schema and def_name in schema["definitions"]:
                    resolved_def = self._resolve_schema(
                        schema["definitions"][def_name], base_path="", depth=0
                    )
                    clean_def = self._remove_schema_ids(resolved_def)
                    needed_definitions[def_name] = clean_def

        # Merge collected definitions into the resolved schema
        if "definitions" not in resolved_schema:
            resolved_schema["definitions"] = {}
        # Add only the definitions that are actually used
        for key, value in needed_definitions.items():
            if key not in resolved_schema["definitions"]:
                resolved_schema["definitions"][key] = value

        return resolved_schema

    def _remove_schema_ids(self, schema: Any) -> Any:
        r"""
        Recursively remove ``$id`` fields to avoid creating new JSON Schema scopes.

        Validators use ``$id`` to set a new resolution base URI.  Removing them
        from resolved output prevents scope-related surprises.

        :param schema: Schema node (dict, list, or scalar)
        :return: Schema with all ``$id`` fields stripped

        EXAMPLES::

            >>> from mdstools.schema.resolver import SchemaResolver
            >>> resolver = SchemaResolver('schemas')

            ``$id`` is removed from dicts::

                >>> resolver._remove_schema_ids({'$id': 'urn:x', 'type': 'object'})
                {'type': 'object'}

            Works recursively::

                >>> resolver._remove_schema_ids(
                ...     {'defs': {'A': {'$id': 'urn:a', 'type': 'string'}}}
                ... )
                {'defs': {'A': {'type': 'string'}}}

            Lists are handled too::

                >>> resolver._remove_schema_ids([{'$id': 'x', 'v': 1}, 'plain'])
                [{'v': 1}, 'plain']

            Scalars pass through::

                >>> resolver._remove_schema_ids(42)
                42

        """
        if isinstance(schema, dict):
            result = {}
            for k, v in schema.items():
                if k == "$id":
                    continue  # Skip $id fields
                result[k] = self._remove_schema_ids(v)
            return result
        if isinstance(schema, list):
            return [self._remove_schema_ids(item) for item in schema]
        return schema


# Main script
if __name__ == "__main__":
    # Adjust path since we're now in mdstools/schema/
    project_root = Path(__file__).parent.parent.parent
    resolver = SchemaResolver(str(project_root / "schemas"))

    # Resolve the main combined schemas that users will work with
    # These are the "combined" schemas that reference multiple pieces
    schemas_to_resolve = [
        "autotag",  # Complete echemdb metadata
        "minimum_echemdb",  # Minimum metadata for echemdb
        "source_data",  # Source data with data description
        "svgdigitizer",  # Digitizer output metadata
        "echemdb_package",  # Data package for echemdb
        "svgdigitizer_package",  # Data package for svgdigitizer
    ]

    # Output to schemas/ root (parent of schema_pieces/)
    output_dir = project_root / "schemas"

    for schema_name_to_resolve in schemas_to_resolve:
        if schema_name_to_resolve in resolver.schema_cache:
            print(f"Resolving {schema_name_to_resolve}.json...")
            resolved_schema_output = resolver.resolve_all_refs(schema_name_to_resolve)

            output_file = output_dir / f"{schema_name_to_resolve}.json"
            with open(output_file, "w", encoding="utf-8") as output_f:
                json.dump(
                    resolved_schema_output,
                    output_f,
                    indent=2,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                # json.dump does not save files with a newline, which compromises the tests
                # where the output files are compared to an expected json.
                output_f.write("\n")

            print(f"  OK - Saved to {output_file}")
        else:
            print(f"  WARNING - Schema '{schema_name_to_resolve}' not found, skipping")

    print("\nOK - Done! Resolved schemas saved to schemas/ directory")
