**Added:**

* Added ``pixi run doc-fast``, an incremental documentation build for quick previews while editing. It regenerates the schema pages only if ``linkml/`` changed and builds from scratch only if the page structure changed, so it is also safe after switching branches.
* Added ``pixi run doc-fast-serve``, which serves the documentation built by ``pixi run doc-fast`` on http://localhost:8080.

**Changed:**

* Changed ``pixi run doc`` to always build the documentation from scratch, so that the navigation of unchanged pages is never outdated after the page structure changes.
* Changed ``doc/generate_schema_docs.py`` to write only schema pages whose content changed, instead of deleting and regenerating all of them.

**Removed:**

* Removed ``doc/Makefile``; the pixi tasks call ``sphinx-build`` directly, and ``make`` is no longer a dependency of the documentation environment.
