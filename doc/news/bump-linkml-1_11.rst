**Changed:**

* Changed version bounds of `linkml` and `linkml-runtime` from `>=10,<11` to `>=11,<12`.
* Regenerated JSON Schemas with LinkML 1.11: URL-typed properties now carry ``"format": "uri"`` and abstract base classes (e.g. ``ControlledOperation``) are included in ``$defs``.

**Fixed:**

* Strip MkDocs-Material search front matter and ``data-search-exclude`` divs from ``gen-doc`` output (new in LinkML 1.11), which broke the Sphinx/MyST documentation build.
