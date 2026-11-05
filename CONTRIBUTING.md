# Contributing to metadata-schema

Contributions are welcome, from changes to the schema to fixes in `mdstools` and the
documentation. If you want to discuss a change first, open an issue, or comment on an existing
one.

If you work with Claude Code, the same workflow is available as skills (`/new-pr`,
`/schema-change`, `/record-decision`); see `CLAUDE.md`.

## Setup

Install [pixi](https://pixi.sh), then:

```bash
pixi install -e dev        # environment with test, lint, validate and doc tools
pixi run test              # should pass on a clean checkout
```

Do not `pip install` into the environment. Dependencies are declared in `pyproject.toml`.

## Workflow

All contributions go through a **fork** and a **pull request** to `echemdb/metadata-schema`.

1. **Fork once** on GitHub and clone your fork, or add it as a remote to an existing clone.
   The remotes should be:
   - `origin` → `echemdb/metadata-schema` (upstream, you only fetch from it)
   - a remote for your fork, e.g. named after your GitHub user:
     `git remote add <user> git@github.com:<user>/metadata-schema.git`
2. **Start every change on a fresh branch from upstream:**

   ```bash
   git fetch origin
   git checkout -b <short-topic-name> --no-track origin/main
   ```

   Do not work on `main`, and do not reuse an old branch for a new change.
3. **Keep each branch minimal.** One concern per branch and pull request; no unrelated
   refactoring or formatting. This matters most for **schema changes that need a migration**:
   each breaking change gets its own branch with its migration, fixture and news entry, so it
   can be reviewed, released and reverted on its own.
4. Make the change and run the [checks](#checks) **locally**. They must pass before you push;
   CI is a safety net, not the first test run.
5. Add a [news entry](#news-entry).
6. Commit, push to your fork (`git push -u <user> <branch>`), and open a pull request against
   `echemdb/metadata-schema:main`. Fill in the pull request template.
7. If `origin/main` moves during review, `git fetch origin` and rebase or merge. If generated
   files conflict, regenerate them instead of resolving the conflict by hand.

Design decisions and discussion belong in the issue or pull request, not in the repository.

## Changing the schema

**Start with an example, not with the schema.** Edit the example in `examples/objects/` that
covers the part you want to change (e.g. `system.yaml` for electrodes, electrolytes or cells)
so that it shows the metadata as it *should* look. The example illustrates the proposal,
makes it easy to discuss, and stays in the repository as the example for the new fields.

If the change may be breaking, first copy the unchanged example to `tests/migrations/`. It is
the old-style data the migration has to upgrade (see step 5), and you can trim it to the part
that changes.

Discuss the proposal before implementing it: in the related issue, or by pushing the example
change alone and opening a draft pull request. Such a draft fails `validate` in CI until the
schema is implemented; that is expected. Besides the example, say whether new fields are
required, which values are allowed, and which units apply. A single new optional field needs
little discussion; a short note in the issue or the pull request is enough. Implement the
schema once the structure is agreed:

1. Edit the LinkML files in `linkml/`. Never edit `schemas/` or `mdstools/models/` by hand;
   they are generated.
2. Regenerate:

   ```bash
   pixi run generate-all
   pixi run update-expected-schemas
   ```

3. Review `git diff -- schemas mdstools/models`. Every change must follow from your LinkML
   edit. Generation depends only on the LinkML input, so the output is identical on every
   platform. A change you cannot explain (encoding, file paths, formatting) is a bug in
   `mdstools/schema/generate_from_linkml.py`; fix it there instead of committing it.
4. Run `pixi run validate`: the changed example must now pass. Update the other examples in
   `examples/` (e.g. `examples/file_schemas/`) where they include the changed part.
5. **Breaking changes**: a field moved, removed, renamed or retyped, or anything else that would
   make existing data fail validation. In the same branch:
   - add a migration step to `mdstools/schema/migrations.py` with `to_version="UNRELEASED"`
     (applied by `mdstools update`);
   - keep the old-style fixture under `tests/migrations/` and add a test that migrates it and
     validates the result against the current schema. Fixtures are committed: migrations
     chain across versions, and the tests run in CI without git history;
   - say in the news entry that the change is breaking.

   `UNRELEASED` is replaced by the release version when a release is made. A breaking change
   needs a minor version bump (0.8.x → 0.9.0). Purely additive changes need no migration.

Naming conventions (checked by `pixi run check-naming`): snake_case files, PascalCase classes,
camelCase properties.

## Checks

```bash
pixi run test        # doctests, integration tests, schema snapshots, generated-artifact check
pixi run validate    # examples against schemas, naming conventions
pixi run lint        # pylint, black, isort
pixi run check-news  # news entries are well-formed
```

## News entry

Every pull request adds `doc/news/<branch-name>.rst`. These files are merged into `ChangeLog`
when a release is made.

- Keep **only the sections that have entries**. Delete all other sections, and never leave a
  placeholder such as `<news item>` in the file.
- Allowed section headers, spelled exactly like this: `**Added:**`, `**Changed:**`,
  `**Deprecated:**`, `**Removed:**`, `**Fixed:**`, `**Performance:**`.
- Format: header line, blank line, one `*` bullet per item, blank line before the next header.
  Use RST double backticks for code: ``` ``field.name`` ```. Reference issues as `(#123)`.
- Each entry must be understandable on its own. Entries are merged and may be reordered in
  the `ChangeLog`, so do not refer to other entries ("the same", "see above").
- Save as UTF-8 without BOM. On Windows, do not create the file with PowerShell
  `>`, `Set-Content` or `Out-File`; use your editor.
- If your branch changes something that already has a staged news file, update that file
  instead of adding a contradicting one.

Example:

```rst
**Added:**

* Added ``system.electrolyte.preparationProcedure`` to describe how the electrolyte was prepared. (#128)

**Changed:**

* Changed ``system.electrochemicalCell.cleaningProcedure`` to ``preparationProcedure``. This is a breaking change; run ``mdstools update`` to migrate existing files.
```
