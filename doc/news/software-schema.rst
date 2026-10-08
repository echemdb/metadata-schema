**Added:**

* Added an optional ``software`` attribute to ``figureDescription`` recording the software (``name``, ``version``, and optional ``url``) that created the data, e.g., the software that recorded, digitized, simulated, or processed it. If ``software`` is provided, ``name`` and ``version`` are required. (#126)

**Fixed:**

* Fixed ``generate_from_linkml.py`` decoding the output of ``gen-json-schema`` and ``gen-pydantic`` with the platform's locale encoding, which mangled non-ASCII characters (e.g. ``±`` became ``Â±``) in Pydantic models generated on Windows. The ``check-schemas`` CI job now regenerates on Linux, macOS, and Windows, and a new test ensures generated artifacts contain no non-ASCII characters absent from the LinkML sources.
