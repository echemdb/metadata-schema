---
name: schema-change
description: Change the echemdb LinkML metadata schema — look up related GitHub issues, first propose the change as an edit to an example YAML and discuss it with the user, then edit linkml/, regenerate JSON Schemas and Pydantic models, review the generated diff, validate the examples, and add a migration step and fixture for breaking changes. Use for any change to the metadata schema.
---

# Changing the schema

Follow "Changing the schema" in `CONTRIBUTING.md`. Work on a fresh branch (see `/new-pr`).
The order matters: **example → discussion → implementation**. Do not touch `linkml/` before
the user has agreed on the example.

## 1. Look for earlier discussion

Search the issues and PRs for the affected classes and fields:

```bash
gh issue list -R echemdb/metadata-schema --search "<class or field name>" --state all
gh pr list -R echemdb/metadata-schema --search "<class or field name>" --state all
```

Read the matching issues (`gh issue view <n> --comments`). Tell the user about earlier
decisions that affect the change, especially if the request contradicts one. Issue #86
("Migration Strategy") describes how breaking changes are handled.

## 2. Propose the change as an example

Find the example in `examples/objects/` that covers the affected part (e.g. `system.yaml` for
electrodes, electrolytes and cells).

- If the user already edited the example, read their diff (`git diff -- examples`) and
  summarize what it implies for the schema: new, renamed, moved or retyped fields.
- Otherwise, propose an edit to the example that shows the metadata as it should look, using
  realistic values. Keep it to the part being changed.

Point out open questions: naming, required vs. optional, allowed values, units, single value
vs. list, whether existing data would break.

If the change may be breaking, copy the unchanged example to `tests/migrations/` before
editing it. That copy is the old-style fixture for the migration (step 7).

## 3. Discuss

Let the user comment and revise the example until they agree. For a single new optional
field, a short confirmation is enough. If others should weigh in, offer to post the proposal
on the related issue (`/record-decision`) or to push only the example change and open a draft
PR (`/new-pr`), both only after confirmation. Tell the user that such a draft fails `validate`
in CI until the schema is implemented.

## 4. Edit the LinkML source

Only after agreement. Only edit files in `linkml/`. Keep the naming conventions (PascalCase
classes, camelCase slots, snake_case files). Give new slots a `description` and, for primitive
values, `examples` taken from the agreed example.

## 5. Regenerate and review

```bash
pixi run generate-all
pixi run update-expected-schemas
git diff --stat -- schemas mdstools/models
```

Read the diff and explain to the user how each change follows from the LinkML edit. Anything
unexplained (encoding, paths, ordering, formatting) is a generator bug to fix in
`mdstools/schema/generate_from_linkml.py`, not to commit.

## 6. Validate

`pixi run validate`: the agreed example must now pass. Update other examples (e.g.
`examples/file_schemas/`) that include the changed part.

## 7. Breaking or additive?

A change is **breaking** if existing valid data would fail validation: a field moved, removed,
renamed or retyped, or a field made required. Decide with the user; if in doubt, treat it as
breaking.

For a breaking change, in the same branch:

- add a step to `mdstools/schema/migrations.py` with `to_version="UNRELEASED"`;
- keep the old-style fixture from step 2 under `tests/migrations/` (trimmed to the changed
  part) and add a test that migrates it and validates the result against the current schema,
  like `mdstools/test/test_migration_preparation_procedure.py`. The fixture is committed;
  do not read old data from git history;
- say "This is a breaking change" in the news entry and mention `mdstools update`.

## 8. Checks and news

Run `pixi run test`, `pixi run validate`, `pixi run lint` and `pixi run check-news`, then write
the news entry and continue with `/new-pr` from step 6.

## 9. Record the decision

Offer to post the decisions from the discussion (naming, structure, rejected alternatives)
on the related issue or the PR with `/record-decision`.
