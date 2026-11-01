# PR 32433: preserve edits during a pending save

[PR 32433](https://github.com/TryGhost/Ghost/pull/32433) addresses a settings editor race. A user can save value A and enter value B before the request for A finishes. An older response or settings refresh could replace B, or an overlapping save could close a modal without saving B.

The follow-up at `1958aa6821284e1caba9c6cf88c222753d6aacf8` protects the tested dirty settings group and Design states from refreshes. It guards response setters in Design, Portal, and User Detail, and lets Navigation and Stripe Direct close only after a successful save. It also prevents overlapping save-button feedback and clears the saving state when an error is thrown. The settings group forwards save options and keeps the latest saved response as the baseline for cancel and unchanged saves.

The `handleSave` result has distinct meanings. A pending call returns `false` without submitting. A stale call can return `false` after the server has saved the earlier snapshot. Validation failure also returns `false`, while save errors are thrown. Callers must account for these cases when deciding whether to close an editor or show success.

The focused run passed 47 tests in eight files. After test-only lint fixes, 16 of those tests passed again in six files. Both the regression and implementation commits passed their repository hooks. The tests use real hooks and selected rendered components with mocked surrounding dependencies, so they do not establish live React Query ordering, browser keyboard behavior, a backend write, or the User Detail slug-change and settled-404 paths. Other `useForm` consumers remain outside this validation.

An individual merge-tree check against main at `3b395b6b082bb995bc8dc8d7b648fea7732fe839` produced a tree without conflicts. After publication of the final head, the [CI](https://github.com/TryGhost/Ghost/actions/runs/41330450096) and [Tinybird](https://github.com/TryGhost/Ghost/actions/runs/41330450057) workflows reported `action_required`. That status is not a passing check and requires maintainer authorization. A full `pnpm check` is not established for this branch.

See [the evidence and reproduction instructions](evidence.md) and [the infographic report](infographic_report.md).
