## What and why

<!-- What does this PR change, and why? Link the related issue, e.g. "Closes #123" or "Part of #123". -->

## Checklist

- [ ] The branch starts from a recent `origin/main` and contains only this change.
- [ ] `pixi run test`, `pixi run validate`, `pixi run lint` and `pixi run check-news` pass locally.
- [ ] Added `doc/news/<branch-name>.rst`.
- [ ] Schema changes only: regenerated with `pixi run generate-all` and `pixi run update-expected-schemas`, and reviewed the diff of `schemas/` and `mdstools/models/`.
- [ ] Breaking schema changes only: added a migration step (`to_version="UNRELEASED"`), an old-style fixture under `tests/migrations/` and a test that migrates it.

<!-- A draft PR that only proposes an example change fails `validate` until the schema is implemented. That is expected. -->
