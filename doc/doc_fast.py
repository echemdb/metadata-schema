r"""
Build the documentation incrementally, falling back to slower steps only when needed.

Used by ``pixi run doc-fast``. Compared with ``pixi run doc``, which always
regenerates the schema pages and builds from scratch, this script

* regenerates the schema pages only if ``linkml/`` (or the generator) changed,
* builds from scratch only if the page structure (toctrees, page list,
  ``conf.py``) changed, since Sphinx does not update the navigation of
  unchanged pages,
* and otherwise re-renders only the pages that changed.

It is therefore safe to use after switching branches.
"""

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

from generate_schema_docs import (
    LINKML_DIR,
    SCHEMA_DOC_DIR,
    TEMPLATE_DIR,
    generate_schema_docs,
)

DOC_DIR = Path(__file__).resolve().parent
BUILD_DIR = DOC_DIR / "generated"
SCHEMA_STAMP = SCHEMA_DOC_DIR / ".source-hash"
STRUCTURE_STAMP = BUILD_DIR / ".structure-hash"
IGNORED = {"generated", "schema", "news", "_build"}
TOCTREE = re.compile(r"^```\{toctree\}.*?^```", re.MULTILINE | re.DOTALL)


def _hash(chunks):
    r"""Return a SHA-256 hex digest of the given byte strings."""
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def schema_sources_hash():
    r"""Hash everything the generated schema pages depend on."""
    files = sorted(LINKML_DIR.rglob("*.yaml")) + sorted(TEMPLATE_DIR.rglob("*"))
    files.append(DOC_DIR / "generate_schema_docs.py")
    return _hash(
        p.relative_to(DOC_DIR.parent).as_posix().encode() + p.read_bytes()
        for p in files
        if p.is_file()
    )


def structure_hash():
    r"""Hash the page list, all toctrees of the hand-written pages and conf.py."""
    chunks = [(DOC_DIR / "conf.py").read_bytes()]
    for page in sorted(DOC_DIR.rglob("*.md")):
        relative = page.relative_to(DOC_DIR)
        if relative.parts[0] in IGNORED:
            continue
        toctrees = TOCTREE.findall(page.read_text(encoding="utf-8"))
        chunks.append(relative.as_posix().encode() + "\n".join(toctrees).encode())
    return _hash(chunks)


def _read(stamp):
    return stamp.read_text(encoding="utf-8").strip() if stamp.exists() else None


def main():
    r"""Regenerate and rebuild as much as needed, then run Sphinx."""
    schema_hash = schema_sources_hash()
    if _read(SCHEMA_STAMP) != schema_hash:
        print("linkml/ changed: regenerating the schema pages.")
        generate_schema_docs()
        SCHEMA_STAMP.write_text(schema_hash, encoding="utf-8")

    pages_hash = structure_hash()
    options = ["-j", "auto", "-W", "-n", "--keep-going"]
    if _read(STRUCTURE_STAMP) != pages_hash:
        print("Page structure changed: building from scratch.")
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    result = subprocess.run(
        ["sphinx-build", "-M", "html", str(DOC_DIR), str(BUILD_DIR), *options],
        check=False,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    STRUCTURE_STAMP.write_text(pages_hash, encoding="utf-8")


if __name__ == "__main__":
    main()
