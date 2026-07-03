**Added:**

* Added a metadata migration engine (``mdstools.schema.migrate``) that upgrades
  echemdb metadata dicts, files and data packages from older to newer schema
  versions. Breaking-change steps are declared in ``mdstools.schema.migrations``;
  only breaking changes need a step (additive changes are backward-compatible).
* Added the ``mdstools update`` command (and ``pixi run update``) to report or
  apply migrations. Without ``--in-place`` it is a dry run; ``--in-place``
  rewrites the file in its original format, preserving YAML comments and layout.
* Added ``MetadataMigrator.validate`` to check a migrated document against its
  target schema, including the instrument-reference check.

**Changed:**

* The release process (``rever.xsh``) now stamps unreleased migration steps
  (``to_version="UNRELEASED"``) with the concrete release version via a new
  ``finalize_migrations`` activity.
* Added ``ruamel.yaml`` as a dependency for comment-preserving YAML round-trips.
