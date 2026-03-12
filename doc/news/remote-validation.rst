g**Added:**

* Added ``validate()`` function and per-schema convenience wrappers
  (``validate_svgdigitizer()``, ``validate_autotag()``, etc.) that fetch
  JSON schemas directly from the metadata-schema GitHub repository and
  validate metadata dicts or YAML/JSON files against them.  A ``version``
  parameter selects the git tag or branch (default ``main``).
