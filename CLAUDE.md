# Instructions for Claude — metadata-schema

Metadata schemas for echemdb, defined in **LinkML** (`linkml/`, the single source of truth).
From them we generate JSON Schemas (`schemas/*.json`, snapshots in `schemas/expected/`) and
Pydantic models (`mdstools/models/*.py`). The `mdstools` package (CLI: `mdstools`) flattens,
enriches, validates and migrates metadata files.

**Follow `CONTRIBUTING.md`** for setup, the fork/branch workflow, schema changes and
migrations, the checks, and news entries. This file only adds what is specific to Claude.

## Keep the repository clean

- Do what the user asked and nothing more. No extra files, helper scripts, summaries or
  comments that the request did not call for.
- Files and text written by Claude are committed only if they document the **current state**
  of the project (code, schema, user docs, news entry). Session notes, design discussions,
  rejected alternatives and ideas belong in the related GitHub **issue or PR comments**, not
  in the repository. Use `/record-decision` for that.
- Keep each branch to one concern. If a request covers several independent changes, propose
  one branch per change.

## Git and GitHub

- Never `git commit`, `git push`, or create, edit or comment on issues and PRs without showing
  exactly what will happen and getting an explicit "yes". Approval for one step does not
  cover the next.
- Run `pixi run test`, `pixi run validate`, `pixi run lint` and `pixi run check-news` locally
  before proposing a push.
- If the user seems new to the repository (no fork remote, first PR, asks how to contribute),
  walk them through the setup and workflow in `CONTRIBUTING.md` and explain each git step
  before running it.

## Generated files

After `pixi run generate-all`, read `git diff -- schemas mdstools/models` and explain to the
user how each change follows from the LinkML edit. Passing tests are not enough: the
regeneration tests reuse the generator, so they repeat any bug in it.

## Skills in this repository

- `/new-pr`: start a change and carry it through to a pull request.
- `/schema-change`: change the LinkML schema, including related issues, regeneration and
  migrations.
- `/record-decision`: post a decision or design note as a comment on the related issue or PR.
