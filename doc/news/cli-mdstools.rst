**Added:**

* Added click-based CLI via ``mdstools.entrypoint`` with ``flatten`` and ``unflatten`` commands, registered as the ``mdstools`` entry point.
* Added ``mdstools/test/cli.py`` with ``invoke()`` helper for click CLI testing, following the unitpackage pattern.

**Changed:**

* Consolidated test directory from ``mdstools/tests/`` into ``mdstools/test/``.
* Updated pixi tasks ``flatten`` and ``unflatten`` to use the new click-based CLI.

**Removed:**

* Removed legacy argparse-based ``mdstools/cli.py``, replaced by ``mdstools/entrypoint.py``.
