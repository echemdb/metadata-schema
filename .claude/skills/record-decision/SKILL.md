---
name: record-decision
description: Record a design decision, discussion outcome or useful background note as a comment on the related GitHub issue or PR in echemdb/metadata-schema, instead of adding it to the repository. Use when a session produced decisions, rejected alternatives or notes worth keeping, or when the user asks to document a decision.
---

# Record a decision on GitHub

The repository only contains what documents the current state of the project. Decisions,
reasoning, rejected alternatives and session notes go into issue or PR comments, where they
stay attached to the discussion they belong to.

## 1. Find the right place

- A PR for the current branch exists → comment there (`gh pr view --json number,url`).
- Otherwise search for a related issue:
  `gh issue list -R echemdb/metadata-schema --search "<keywords>" --state all`.
- Nothing fits → propose opening a new issue, with a title and body for the user to review.

## 2. Draft the comment

Keep it short and factual:

- **Decision:** what was decided, in one or two sentences.
- **Why:** the reasons and constraints.
- **Alternatives considered:** only those that were actually discussed, each with the reason
  it was rejected.
- **Affects:** classes, fields or files, and the PR or commit if there is one.

Write in the user's voice. Do not add an AI attribution line unless the user wants one.

## 3. Confirm and post

Show the full comment text and target (issue or PR number) and wait for an explicit "yes".
Then post with `gh issue comment <n> -R echemdb/metadata-schema --body-file <file>` or
`gh pr comment <n> -R echemdb/metadata-schema --body-file <file>`, writing the body to a
temporary file outside the repository (UTF-8). Report the comment URL.
