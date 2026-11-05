**Added:**

* Added ``CONTRIBUTING.md`` describing the fork-based workflow (one minimal branch per change, checks run locally before pushing), schema changes (starting from an edited example that is discussed before the LinkML is changed) with migrations, and how to write news entries, together with a pull request template.
* Added Claude Code skills in ``.claude/skills/``: ``/new-pr`` for the fork-based pull request workflow, ``/schema-change`` for schema changes with migrations, and ``/record-decision`` for recording design decisions on GitHub issues and pull requests.
* Added ``pixi run check-news``, also run in CI, which rejects malformed news entries (placeholders, unknown or empty sections, byte order mark).

**Changed:**

* Changed ``CLAUDE.md`` into short instructions for Claude that refer to ``CONTRIBUTING.md``.
* Changed ``.gitattributes`` so that text files are checked out with LF line endings on every platform.
