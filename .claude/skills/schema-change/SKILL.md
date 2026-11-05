---
name: schema-change
description: Change the echemdb LinkML metadata schema — look up related GitHub issues first, edit linkml/, regenerate JSON Schemas and Pydantic models, review the generated diff, update examples, and add a migration step and fixture for breaking changes. Use for any edit to files under linkml/.
---

# Changing the schema

Follow "Changing the schema" in `CONTRIBUTING.md`. Work on a fresh branch (see `/new-pr`).

## 1. Look for earlier discussion

Before editing, search the issues and PRs for the affected classes and fields:

```bash
gh issue list -R echemdb/metadata-schema --search "<class or field name>" --state all
gh pr list -R echemdb/metadata-schema --search "<class or field name>" --state all
```

Read the matching issues (`gh issue view <n> --comments`). Tell the user about earlier
decisions that affect the change, especially if the request contradicts one. Issue #86
("Migration Strategy") describes how breaking changes are handled.

## 2. Edit the LinkML source

Only edit files in `linkml/`. Keep the naming conventions (PascalCase classes, camelCase slots,
snake_case files). Give new slots a `description` and, for primitive values, `examples`.

## 3. Regenerate and review

```bash
pixi run generate-all
pixi run update-expected-schemas
git diff --stat -- schemas mdstools/models
```

Read the diff and explain to the user how each change follows from the LinkML edit. Anything
unexplained (encoding, paths, ordering, formatting) is a generator bug to fix in
`mdstools/schema/generate_from_linkml.py`, not to commit.

## 4. Examples

Update or add files in `examples/objects/` and `examples/file_schemas/` so the new or changed
fields are covered. `pixi run validate` must pass.

## 5. Breaking or additive?

A change is **breaking** if existing valid data would fail validation: a field moved, removed,
renamed or retyped, or a field made required. Decide with the user; if in doubt, treat it as
breaking.

For a breaking change, in the same branch:

- add a step to `mdstools/schema/migrations.py` with `to_version="UNRELEASED"`;
- add old/new fixtures under `tests/migrations/` (see the existing `*_pre_0_8_0.*` files);
- say "This is a breaking change" in the news entry and mention `mdstools update`.

## 6. Checks and news

Run `pixi run test`, `pixi run validate`, `pixi run lint` and `pixi run check-news`, then write the news entry and
continue with `/new-pr` from step 6.

## 7. Record the decision

If the user made a design decision (naming, structure, why an alternative was rejected),
offer to post it on the related issue or the PR with `/record-decision`.
