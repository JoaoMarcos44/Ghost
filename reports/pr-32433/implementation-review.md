# Simplified failed-save feedback cleanup

Published source commit: [`5b90b7b188a5a3263ad3bb055cb83cf8b077b33f`](https://github.com/JoaoMarcos44/Ghost/commit/5b90b7b188a5a3263ad3bb055cb83cf8b077b33f).

`useSaveButton` previously restored its idle state in both a `catch` block and the `false` result branch. It now initializes `saved` to false and performs that cleanup once in `finally` when the save did not succeed. A thrown error still propagates naturally. The pending-save guard, successful feedback timers, caller return behavior and all form-version/refresh/cancel safeguards are unchanged.

This removes duplicated state updates and an unnecessary catch-and-rethrow. It introduces no helper abstraction, new feature or API change. The source diff is limited to `apps/admin/src/settings/hooks/use-save-button.ts`: seven additions and nine removals. No performance benchmark or latency improvement is claimed.

The infographic is now displayed directly between the problem explanation and validation in this PR's description. Its existing architecture remains accurate for this behavior-preserving cleanup.

## Validation

- Before editing, the four existing save-button tests passed.
- After editing, the existing suite passed **47 tests in eight files**, including false results, thrown errors, overlapping saves and success-feedback timing.
- The focused formatting and Oxlint checks passed on 15 files. `git diff --check` passed.
- All unchanged source commit hooks passed, including real ESLint, dependency boundaries and secret scanning. The first wrapper attempt stopped the hook after 180 seconds while ESLint was still running; a bounded 360-second retry completed successfully. No hooks or rules were disabled.
- An individual merge-tree check with main `3b395b6b082bb995bc8dc8d7b648fea7732fe839` produced `41da68a718cf682da96dcd5481e8427097ee9ddc` without conflicts. The source branch was pushed normally.

Commands from a checkout containing this report:

```powershell
powershell -NoProfile -File reports/pr-32433/run-unit.ps1 -Worktree <source-worktree> -TestFile use-save-button.test.ts
powershell -NoProfile -File reports/pr-32433/run-unit.ps1 -Worktree <source-worktree>
powershell -NoProfile -File reports/pr-32433/run-checks.ps1 -Worktree <source-worktree>
```

The test runners used isolated sandboxes, one worker and a 2048 MB Node heap. Their sandboxes and child processes were cleaned. Genuine Shade declarations built temporarily for the hooks were removed afterward. The interrupted hook's own backup stash was removed only after its full tree matched the committed source; unrelated stashes were preserved.

The same validation limits apply: surrounding APIs, context and UI are mocked; no new browser, backend, slug/404, full build or complete `pnpm check` result is claimed. The historical blocked settings sandbox was not touched.
