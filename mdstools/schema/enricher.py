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

        :param schema_dir: Path to the directory containing JSON Schema files.
                          Will first look for resolved schemas in schema_dir/resolved/
        """
        self.schema_dir = Path(schema_dir)
        self.schema_cache = {}
        self._load_schemas()

    def _load_schemas(self):
        """Load all JSON schema files from both root (resolved) and schema_pieces (modular)."""
        if not self.schema_dir.exists():
            raise ValueError(f"Schema directory not found: {self.schema_dir}")

        # Load from schema_pieces for modular access (system.json, curation.json, etc.)
        schema_pieces = self.schema_dir / "schema_pieces"
        if schema_pieces.exists():
            for schema_file in schema_pieces.rglob("*.json"):
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema_name = schema_file.stem
                    # Only load if not already loaded (don't override)
                    if schema_name not in self.schema_cache:
                        self.schema_cache[schema_name] = json.load(f)

        # Also load resolved schemas from root for fallback
        for schema_file in self.schema_dir.glob("*.json"):
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_name = schema_file.stem
                if schema_name not in self.schema_cache:
                    self.schema_cache[schema_name] = json.load(f)

                    # For combined schemas like autotag/svgdigitizer,
                    # also register their sub-definitions
                    # This allows lookup by top-level keys like "system", "curation", etc.
                    schema_data = self.schema_cache[schema_name]
                    if "definitions" in schema_data:
                        for def_name, def_value in schema_data["definitions"].items():
                            # Register definitions by their lowercase name for lookup
                            lowercase_name = def_name.lower()
                            if lowercase_name not in self.schema_cache:
                                # Create a minimal schema structure for this definition
                                self.schema_cache[lowercase_name] = {
                                    "definitions": {def_name: def_value},
                                    "$schema": schema_data.get(
                                        "$schema",
                                        "http://json-schema.org/draft-07/schema#",
                                    ),
                                }

    def _resolve_ref(self, ref: str, current_schema: Dict) -> Optional[Dict]:
        """
        Resolve a $ref reference to its definition.

        :param ref: The $ref string (e.g., "#/definitions/Process")
        :param current_schema: The current schema dict
        :return: The resolved schema definition or None
        """
        if ref.startswith("#/"):
            # Internal reference
            parts = ref[2:].split("/")
            result = current_schema
            for part in parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                else:
                    return None
            return result
        if ref.startswith("./"):
            # External reference
            ref_path = ref.split("#")[0]
            ref_fragment = ref.split("#")[1] if "#" in ref else ""

            # Load the referenced schema
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
                            return None
                    return result
                return ref_schema

        return None

    def _get_field_metadata(  # pylint: disable=too-many-nested-blocks,too-many-branches
        self, schema: Dict, field_path: list, root_schema: Optional[Dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract description and example from schema for a given field path.

        :param schema: The schema definition to search within
        :param field_path: List of field names representing the path
        :param root_schema: The root schema containing all definitions (for resolving $refs)
        :return: Tuple of (description, example) or (None, None)
        """
        if not field_path:
            return None, None

        current = schema
        if root_schema is None:
            root_schema = schema  # Keep reference to root for cross-references

        # Navigate through the schema following the field path
        for i, field in enumerate(field_path):
            if not isinstance(current, dict):
                return None, None

            # Follow $ref if present at current level
            while "$ref" in current:
                resolved = self._resolve_ref(current["$ref"], root_schema)
                if resolved:
                    current = resolved
                else:
                    break

            # Check if we're at a property level
            if "properties" in current and field in current["properties"]:
                current = current["properties"][field]

                # Follow any $refs in the property definition
                while "$ref" in current:
                    resolved = self._resolve_ref(current["$ref"], root_schema)
                    if resolved:
                        current = resolved
                    else:
                        break

                # If this is the last field in the path, extract metadata
                if i == len(field_path) - 1:
                    description = current.get("description")

                    # Check for examples in different places
                    example = None
                    if (
                        "examples" in current
                        and isinstance(current["examples"], list)
                        and len(current["examples"]) > 0
                    ):
                        example = current["examples"][0]
                    elif "example" in current:
                        example = current["example"]
                    elif "const" in current:
                        example = current["const"]
                    elif "anyOf" in current and isinstance(current["anyOf"], list):
                        # Get the first const as example from anyOf
                        for option in current["anyOf"]:
                            if "const" in option:
                                example = option["const"]
                                if not description and "description" in option:
                                    description = option["description"]
                                break
                    elif "oneOf" in current and isinstance(current["oneOf"], list):
                        # Get the first const as example from oneOf
                        for option in current["oneOf"]:
                            if "const" in option:
                                example = option["const"]
                                if not description and "description" in option:
                                    description = option["description"]
                                break

                    return description, example

                # Not the last field - if this is an array, resolve its items
                if current.get("type") == "array" and "items" in current:
                    items = current["items"]

                    # Resolve $ref in items if present
                    while "$ref" in items:
                        resolved = self._resolve_ref(items["$ref"], root_schema)
                        if resolved:
                            items = resolved
                        else:
                            break

                    current = items
            else:
                # Can't navigate further with this field
                return None, None

        return None, None

    def enrich_row(  # pylint: disable=unused-argument
        self, key_path: str, current_value: Any
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Get description and example for a specific field path.

        :param key_path: Dot-separated path of keys (e.g., "curation.process.role")
        :param current_value: The current value in the YAML
        :return: Tuple of (description, example) or (None, None)
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
                # Usually the main definition has the same name as the file (capitalized)
                main_def_name = top_level.capitalize()
                if main_def_name in schema["definitions"]:
                    main_def = schema["definitions"][main_def_name]
                    # Pass the full schema as root_schema for resolving $refs
                    return self._get_field_metadata(
                        main_def, parts[1:], root_schema=schema
                    )

        return None, None

    def enrich_flattened_data(self, flattened_rows: list) -> list:
        """
        Enrich flattened YAML rows with description and example columns.

        :param flattened_rows: List of [level, key, value] rows
        :return: List of [level, key, value, example, description] rows
        """
        enriched = []
        path_stack = []  # Stack of (level_depth, key) tuples

        for row in flattened_rows:
            level, key, value = row

            # Parse level like "1.2.a.3" to determine depth
            level_parts = level.split(".")
            depth = len(level_parts)

            # Determine if this level is an array item marker (contains letters)
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
