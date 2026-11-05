"""Generate schema documentation from LinkML YAML files using gen-doc."""

import re
import subprocess
import sys
import tempfile
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

    - Strip MkDocs-Material search front matter and search-exclude divs
      (emitted by gen-doc >= 1.11; meaningless in Sphinx and the type pages
      glue the closing --- onto the H1, which MyST rejects as a transition)
    - Convert ```mermaid to ```{mermaid} for sphinxcontrib-mermaid
    - Add a glob toctree to index.md so all generated pages are included
    """
    for md_file in output_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # Strip leading "search: boost" front matter; handles both the
        # well-formed block and the malformed "---# Heading" variant
        content = re.sub(
            r"\A---\n.*?\n---", "", content, flags=re.DOTALL
        ).lstrip("\n")
        # Strip MkDocs search-exclude wrapper divs
        content = re.sub(
            r'^<div data-search-exclude markdown="1">\n|^</div>\n?',
            "",
            content,
            flags=re.MULTILINE,
        )
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


def _sync_tree(source, target):
    """Make ``target`` identical to ``source``, touching only files that differ.

    Unchanged files keep their modification time, so an incremental Sphinx
    build only re-renders the schema pages whose content actually changed.
    Hidden files in ``target`` (such as the stamp of ``doc_fast.py``) are kept.
    Returns the number of written and removed files.
    """
    written = removed = 0
    source_files = {p.relative_to(source) for p in source.rglob("*") if p.is_file()}
    if target.exists():
        for path in sorted(target.rglob("*"), reverse=True):
            relative = path.relative_to(target)
            if path.name.startswith("."):
                continue
            if path.is_file() and relative not in source_files:
                path.unlink()
                removed += 1
            elif path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    for relative in sorted(source_files):
        new = (source / relative).read_bytes()
        destination = target / relative
        if destination.exists() and destination.read_bytes() == new:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(new)
        written += 1
    return written, removed


def generate_schema_docs():
    """Generate Markdown documentation for each LinkML schema into doc/schema/<name>/."""
    with tempfile.TemporaryDirectory() as tmp:
        _generate_into(Path(tmp))
        written, removed = _sync_tree(Path(tmp), SCHEMA_DOC_DIR)

    print(
        f"Schema documentation generated successfully "
        f"({written} pages written, {removed} removed, others unchanged)."
    )


def _generate_into(schema_doc_dir):
    """Run gen-doc for all schemas into ``schema_doc_dir``."""
    for schema_name in SCHEMAS:
        linkml_file = LINKML_DIR / f"{schema_name}.yaml"
        output_dir = schema_doc_dir / schema_name

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


if __name__ == "__main__":
    generate_schema_docs()
