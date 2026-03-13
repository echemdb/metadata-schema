project = "metadata-schema"
copyright = "2022-2025, the echemdb authors"
author = "the echemdb authors"

release = "0.5.1"

extensions = ["sphinx.ext.autodoc", "sphinx.ext.todo", "myst_parser", "sphinxcontrib.mermaid", "sphinx_design"]

source_suffix = [".rst", ".md"]

templates_path = ["_templates"]

exclude_patterns = [
    "generated",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    "news",
    ".ipynb_checkpoints",
    "*.ipynb",
    "**/*.ipynb",
]

myst_enable_extensions = ["amsmath", "dollarmath", "colon_fence"]

todo_include_todos = True

html_theme = "sphinx_rtd_theme"

html_static_path = []

myst_heading_anchors = 2

# Suppress warnings for external type references (e.g. pandas.DataFrame)
nitpick_ignore = [
    ("py:class", "pandas.DataFrame"),
]

# Add Edit on GitHub links
html_context = {
    "display_github": True,
    "github_user": "echemdb",
    "github_repo": "metadata-schema",
    "github_version": "main/doc/",
}

linkcheck_ignore = [
    "https://www.gnu.org/licenses/gpl-3.0.html*",
    r"https://echemdb\.github\.io/metadata-schema/.*",  # self-referential; exist only after deploy
    r"https://w3id\.org/linkml/.*",  # LinkML URIs redirect to pages that 404
    r"http://www\.w3\.org/2001/XMLSchema#.*",  # XSD anchors not resolvable
    r"http://www\.w3\.org/ns/shex#.*",  # SHEX anchors not resolvable
]
