# PR 32433 evidence

## Revisions

- Audited PR head: `2a62cbb7447c2c52e6b2be4029803f6ee64002d9`.
- Regression commit: `dcb5bec1c377a22b517b314d31056e1085be611e`.
- Final implementation commit: `1958aa6821284e1caba9c6cf88c222753d6aacf8`.
- Main used for the individual merge-tree check: `3b395b6b082bb995bc8dc8d7b648fea7732fe839`.

The audit found that a form version check alone did not protect every consumer. A dirty group could receive a context refresh, and a response setter could replace an edit made during a save. Some overwrite paths also existed before the audited PR. The follow-up covers the reproduced paths in the selected consumers, rather than every `useForm` caller.

## Recorded validation

The initial focused run reproduced four overwrites, with 28 other tests passing. Separate regression tests reproduced false-save modal closes, save-button state problems, and stale response overwrites. The focused run before the test-only lint fixes reported:

```text
Node v22.23.4
Vitest v4.1.12
Test Files  8 passed (8)
Tests       47 passed (47)
Exit        0
```

The suite includes the original `useForm` tests, the settings and Design hooks, the save-button hook, and rendered Navigation, Stripe Direct, Portal, and User Detail components. API, context, UI, and router dependencies around those subjects are simulated. The runner uses one worker, disables file parallelism, and sets a 2048 MB Node heap limit.

An initial regression commit attempt found six test-only ESLint issues. After those were corrected, 16 tests in six files, a subset of the 47 above, passed again. The regression and implementation commits then passed all repository commit hooks, including project ESLint. The focused format and Oxlint check passed on 15 files, using one thread for each command. `git diff --check` also passed.

The individual merge-tree check succeeded and produced tree `f21c7a795cc55ef685edc75ce07eea8ff31979a2`:

```powershell
git merge-tree --write-tree 3b395b6b082bb995bc8dc8d7b648fea7732fe839 1958aa6821284e1caba9c6cf88c222753d6aacf8
```

This result establishes a conflict-free tree for those two commits. It does not establish runtime behavior or a passing CI run. The published head's [CI](https://github.com/TryGhost/Ghost/actions/runs/41330450096) and [Tinybird](https://github.com/TryGhost/Ghost/actions/runs/41330450057) workflows reported `action_required` and require maintainer authorization.

## Reproduce the focused checks

Use Windows PowerShell from a Ghost checkout containing this report. Set `$worktree` to a separate checkout at the final implementation commit with the project dependencies installed. A fresh checkout requires `pnpm bootstrap`, as described in Ghost's development setup. The recorded run used Node v22.23.4 and Vitest v4.1.12; the scripts invoke the checkout's `node_modules/.bin/node.exe` and `apps/admin/node_modules/vitest/vitest.mjs` directly.

```powershell
$worktree = 'C:\path\to\Ghost-at-1958aa'
git -C $worktree rev-parse HEAD
powershell -NoProfile -File .\reports\pr-32433\run-unit.ps1 -Worktree $worktree
powershell -NoProfile -File .\reports\pr-32433\run-checks.ps1 -Worktree $worktree
```

Confirm that `git rev-parse HEAD` prints `1958aa6821284e1caba9c6cf88c222753d6aacf8`. Each runner creates a fresh temporary directory under the checkout's `apps/admin`, directs temporary files and caches there, and removes that directory in `finally`. The first command runs the eight test files. The second checks formatting and Oxlint on the 15 listed files. Successful commands exit 0. The runners use the checkout's installed dependencies and do not reproduce the repository commit hooks.

## Limits and cleanup

The tests do not establish live React Query scheduling, browser keyboard behavior, a backend write, or route changes and settled 404 responses in User Detail. They do not cover every `useForm` consumer. Full type, build, browser, integration, and `pnpm check` results are not established for this branch.

The successful focused runners removed the sandboxes they created. An earlier interrupted audit left a separate sandbox under the historical worktree's `apps/admin`. Two cleanup attempts were blocked by policy before execution. Its cleanup remains unverified; it was not retried.
