**Changed:**

* Changed release workflow: replaced local ``ghrelease`` rever activity (broken due to ``github3.py`` authentication issues) with a tag-triggered GitHub Actions workflow that creates GitHub releases from ``rever/LATEST`` changelog.

**Removed:**

* Removed ``twine``, ``build``, and ``setuptools`` from release dependencies (not needed since this project is not published to PyPI).
