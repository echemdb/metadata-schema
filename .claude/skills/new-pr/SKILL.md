---
name: new-pr
description: Start a change in metadata-schema and carry it through to a pull request — check the fork setup, create a fresh branch from origin/main, run the local checks, write the news entry, then commit, push and open the PR, each git step only after the user confirms. Use when the user wants to start a new change, contribute, or open a PR.
---

# New change → pull request

Follow the "Workflow" in `CONTRIBUTING.md`. Ask for explicit confirmation before every
`git commit`, `git push` and `gh pr create`, showing exactly what will happen.

## 1. Check the setup

- `git remote -v`: `origin` must point to `echemdb/metadata-schema`. There must be a remote for
  the user's fork. If there is none, explain forking and offer
  `git remote add <user> git@github.com:<user>/metadata-schema.git`.
- `git status`: if there are uncommitted changes, stop and ask what to do with them.

## 2. Find the context

Ask what the change is about, then search for a related issue:
`gh issue list -R echemdb/metadata-schema --search "<keywords>" --state all`.
Mention matching issues and use their number in the branch description, news entry and PR.

## 3. Create the branch

```bash
git fetch origin
git checkout -b <short-topic-name> --no-track origin/main
```

One concern per branch. If the user's request covers several independent changes, propose
one branch per change. A breaking schema change always gets its own branch.

## 4. Make the change

For schema changes, follow the `/schema-change` skill. Keep the diff limited to what was asked.

## 5. Run the checks locally

```bash
pixi run test
pixi run validate
pixi run lint
pixi run check-news
```

All must pass before pushing. If `lint` reformats files, show the user what changed.

## 6. News entry

Write `doc/news/<branch-name>.rst` following the "News entry" rules in `CONTRIBUTING.md`:
only the sections that have entries, no placeholders, UTF-8 without BOM. Reference the issue as
`(#123)`. `pixi run check-news` verifies the format.

## 7. Commit (confirm first)

Show `git status` and `git diff --stat`, list the files, propose a commit message, and wait
for a "yes".

## 8. Push and open the PR (confirm each)

```bash
git push -u <fork-remote> <branch>
gh pr create -R echemdb/metadata-schema --base main --head <user>:<branch>
```

Fill in `.github/pull_request_template.md`: what changed and why, the linked issue
(`Closes #123` only if it fully resolves it), and the checklist. Show the full text before
creating the PR.

Design notes or decisions from the session go into a PR or issue comment (`/record-decision`),
not into the repository.
