#!/usr/bin/env python
"""
Utility to resolve all $ref references in JSON schemas and create consolidated schemas.

This script loads JSON Schema files and resolves all external $ref references, 
creating "resolved" versions where all definitions are inlined into a single file.
This makes schema parsing more reliable and efficient.

Usage:
    python resolve_schemas.py

The resolved schemas are saved to schemas/resolved/ directory.

EXAMPLES::

    Basic usage from Python::
    
        >>> import os
        >>> os.makedirs('schemas/resolved', exist_ok=True)
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

import json
import os
from pathlib import Path
from typing import Dict, Any
import copy


class SchemaResolver:
    """Resolves all $ref references in JSON schemas."""
    
    def __init__(self, schema_dir: str):
        self.schema_dir = Path(schema_dir)
        self.schema_cache = {}
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all JSON schema files."""
        for schema_file in self.schema_dir.rglob("*.json"):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_name = schema_file.stem
                relative_path = schema_file.relative_to(self.schema_dir)
                # Store with both stem and relative path as keys
                self.schema_cache[schema_name] = json.load(f)
                self.schema_cache[str(relative_path)] = self.schema_cache[schema_name]
    
    def _resolve_ref(self, ref: str, base_schema_path: str = None) -> Any:
        """Resolve a $ref reference."""
        if ref.startswith("#/"):
            # Internal reference - can't resolve without context
            return {"$ref": ref}
        
        elif ref.startswith("./") or ref.startswith("../"):
            # External reference
            ref_path = ref.split("#")[0]
            ref_fragment = ref.split("#")[1] if "#" in ref else ""
            
            # Load the referenced schema
            ref_file = ref_path.lstrip("./").replace("/", os.sep)
            ref_schema_name = Path(ref_file).stem
            
            if ref_schema_name in self.schema_cache:
                ref_schema = copy.deepcopy(self.schema_cache[ref_schema_name])
                
                # Resolve any $refs within the referenced schema
                ref_schema = self._resolve_schema(ref_schema, str(Path(ref_file).parent))
                
                if ref_fragment:
                    # Navigate to the specific definition
                    parts = ref_fragment[1:].split("/")
                    result = ref_schema
                    for part in parts:
                        if isinstance(result, dict) and part in result:
                            result = result[part]
                        else:
                            return {"$ref": ref}  # Can't resolve
                    return result
                return ref_schema
        
        return {"$ref": ref}  # Can't resolve
    
    def _resolve_schema(self, schema: Any, base_path: str = "") -> Any:
        """Recursively resolve all $refs in a schema."""
        if isinstance(schema, dict):
            if "$ref" in schema:
                # Resolve this reference
                resolved = self._resolve_ref(schema["$ref"], base_path)
                if resolved != {"$ref": schema["$ref"]}:
                    # Successfully resolved - merge with any other properties
                    result = copy.deepcopy(schema)
                    del result["$ref"]
                    if isinstance(resolved, dict):
                        # Recursively resolve the resolved schema
                        resolved = self._resolve_schema(resolved, base_path)
                        resolved.update(result)
                        return resolved
                    return resolved
                return schema
            else:
                # Recursively process all properties
                return {k: self._resolve_schema(v, base_path) for k, v in schema.items()}
        
        elif isinstance(schema, list):
            return [self._resolve_schema(item, base_path) for item in schema]
        
        else:
            return schema
    
    def resolve_all_refs(self, schema_name: str) -> Dict:
        """
        Resolve all external $refs in a schema, keeping internal refs.
        
        :param schema_name: Name of the schema file (without .json)
        :return: Resolved schema with all definitions inlined
        """
        if schema_name not in self.schema_cache:
            raise ValueError(f"Schema '{schema_name}' not found")
        
        schema = copy.deepcopy(self.schema_cache[schema_name])
        
        # First, collect all definitions from referenced schemas
        all_definitions = {}
        
        # Recursively resolve external references and collect definitions
        def collect_definitions(obj, path=""):
            if isinstance(obj, dict):
                # If this has a $ref to another file, resolve it and collect its definitions
                if "$ref" in obj and obj["$ref"].startswith("./"):
                    resolved = self._resolve_ref(obj["$ref"], path)
                    if isinstance(resolved, dict):
                        collect_definitions(resolved, path)
                
                # If this has definitions, collect them
                if "definitions" in obj:
                    all_definitions.update(obj["definitions"])
                
                # Recurse into all values
                for k, v in obj.items():
                    if k != "definitions":  # Don't double-process
                        collect_definitions(v, path)
            
            elif isinstance(obj, list):
                for item in obj:
                    collect_definitions(item, path)
        
        collect_definitions(schema)
        
        # Now resolve all external $refs in the schema
        resolved_schema = self._resolve_schema(schema)
        
        # Merge collected definitions
        if "definitions" not in resolved_schema:
            resolved_schema["definitions"] = {}
        resolved_schema["definitions"].update(all_definitions)
        
        return resolved_schema


# Main script
if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Adjust path since we're now in mdstools/
    project_root = Path(__file__).parent.parent
    resolver = SchemaResolver(str(project_root / "schemas"))
    
    # Resolve the main schemas that users will work with
    schemas_to_resolve = [
        "curation",
        "system",
        "source",
        "figure_description",
        "svgdigitizer",
        "minimum_echemdb"
    ]
    
    output_dir = project_root / "schemas" / "resolved"
    output_dir.mkdir(exist_ok=True)
    
    for schema_name in schemas_to_resolve:
        if schema_name in resolver.schema_cache:
            print(f"Resolving {schema_name}.json...")
            resolved = resolver.resolve_all_refs(schema_name)
            
            output_file = output_dir / f"{schema_name}_resolved.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resolved, f, indent=2)
            
            print(f"  -> Saved to {output_file}")
        else:
            print(f"  ⚠ Schema '{schema_name}' not found, skipping")
    
    print("\nDone! Resolved schemas saved to schemas/resolved/")
