"""Generate schema documentation from LinkML YAML files using gen-doc."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

# Schema names matching the LinkML YAML files under linkml/
SCHEMAS = [
    "autotag",
    "minimum_echemdb",
    "source_data",
    "svgdigitizer",
    "echemdb_package",
    "svgdigitizer_package",
]

DOC_DIR = Path(__file__).parent
LINKML_DIR = DOC_DIR.parent / "linkml"
SCHEMA_DOC_DIR = DOC_DIR / "schema"
TEMPLATE_DIR = DOC_DIR / "_templates" / "docgen"


def _postprocess_markdown(output_dir):
    """Fix generated markdown for Sphinx/MyST compatibility.

    - Convert ```mermaid to ```{mermaid} for sphinxcontrib-mermaid
    - Add a glob toctree to index.md so all generated pages are included
    """
    for md_file in output_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Convert fenced mermaid code blocks to MyST directive syntax
        content = re.sub(r"^```mermaid$", "```{mermaid}", content, flags=re.MULTILINE)
        # Remove mermaid blocks that contain only "None" (failed top-level diagrams)
        content = re.sub(
            r"```\{mermaid\}\s*\nNone\s*\n```", "", content
        )
        md_file.write_text(content, encoding="utf-8")

    # Add a glob toctree to the index so all class/slot/enum pages are included
    index_file = output_dir / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        if "toctree" not in content:
            content += "\n```{toctree}\n:hidden:\n:glob:\n\n*\n```\n"
            index_file.write_text(content, encoding="utf-8")


def generate_schema_docs():
    """Generate Markdown documentation for each LinkML schema into doc/schema/<name>/."""
    # Clean previous generated schema docs
    if SCHEMA_DOC_DIR.exists():
        shutil.rmtree(SCHEMA_DOC_DIR)
    SCHEMA_DOC_DIR.mkdir()

    for schema_name in SCHEMAS:
        linkml_file = LINKML_DIR / f"{schema_name}.yaml"
        output_dir = SCHEMA_DOC_DIR / schema_name

        if not linkml_file.exists():
            print(f"WARNING: {linkml_file} not found, skipping")
            continue

        print(f"Generating docs for {schema_name}...")
        result = subprocess.run(
            [
                "gen-doc",
                str(linkml_file),
                "-d",
                str(output_dir),
                "--format",
                "markdown",
                "--mergeimports",
                "--diagram-type",
                "mermaid_class_diagram",
                "--template-directory",
                str(TEMPLATE_DIR),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"ERROR generating docs for {schema_name}:")
            print(result.stderr)
            sys.exit(1)

        _postprocess_markdown(output_dir)
        print(f"  -> {output_dir}")

    print("Schema documentation generated successfully.")


if __name__ == "__main__":
    generate_schema_docs()
