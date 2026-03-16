**Changed:**

* Changed ``dataDescription.dialect.delimiters`` to ``dataDescription.dialect.delimiter`` in the source data schema and examples to match the file-loading API.
* Added optional ``dataDescription.dialect.candidateDelimiters`` to provide delimiter candidates for dialect inference.

**Fixed:**

* Fixed CI generation checks to prevent generator drift by regenerating schemas and Pydantic models and failing when tracked generated artifacts differ.
* Fixed OS-dependent absolute paths in generated Pydantic models (``source_file``) by passing relative POSIX paths to ``gen-pydantic``.
