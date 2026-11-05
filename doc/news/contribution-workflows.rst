**Added:**

* Added ``CONTRIBUTING.md`` describing the fork-based workflow (one minimal branch per change, checks run locally before pushing), schema changes with migrations, and how to write news entries, together with a pull request template.
* Added Claude Code skills ``/new-pr``, ``/schema-change`` and ``/record-decision`` in ``.claude/skills/`` for the same workflow.
* Added ``pixi run check-news``, also run in CI, which rejects malformed news entries (placeholders, unknown or empty sections, byte order mark).

**Changed:**

* Changed ``CLAUDE.md`` into short instructions for Claude that refer to ``CONTRIBUTING.md``; it no longer contains implementation notes from earlier sessions.
* Changed ``.gitattributes`` so that text files are checked out with LF line endings on every platform.
