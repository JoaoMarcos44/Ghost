# PR 32433 focused fix validation

Worktree: `C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031`  
HEAD: `2a62cbb7447c2c52e6b2be4029803f6ee64002d9`  
Fetched main inspected: `3b395b6b082bb995bc8dc8d7b648fea7732fe839`

## Reproductions and outcomes

- The initial focused run executed the existing `useForm` and `useSettingGroup` tests plus new tests against the real group and Design hooks. It exited 1 with **4 failed, 28 passed**. The failures showed an unsaved modal edit overwritten by a refresh, an invalid dirty edit overwritten by a refresh, a Design global edit overwritten by an earlier response, and a Design theme edit overwritten by a query refresh. Each expected B and received A (or Remote).
- Rendered Navigation and Stripe Direct component tests with mocked dependencies both failed on HEAD because a false save result still called `updateRoute`; both pass with the guards.
- Code Injection's save-button test failed because a false result left `isSaving` true. Additional targeted RED tests established that a second shortcut could end the first spinner, another shortcut could start during Saved feedback, and a thrown error left the spinner active. All four button tests pass with the guard and error cleanup.
- Portal component tests with mocked UI/API and real `useForm` both failed with the original setters: after editing B while saving A, the displayed setting or tier reverted to A. Both pass with the captured-array guards, including retry payload B.
- The User Detail component test with mocked UI/API/router and real `useForm` failed with the original setter because B became A. It passes with the identity guard and confirms a retry sends B. The mocked router uses the same slug throughout; it does not exercise route changes or 404 responses. The first attempted test run did not execute tests because the sandbox alias for `@tryghost/admin-x-framework` preceded its `/errors` alias. Reordering the sandbox aliases produced the expected RED, followed by GREEN.
- The first synchronization implementation was itself tested against additional timing cases. Closing an unchanged editor after a skipped refresh returned Original instead of Remote. Two further tests showed a normalized successful response being replaced by stale Original on cancel or an unchanged save. These cases passed after retaining the most recent save response as the local baseline.

## Final focused suite

```powershell
powershell -NoProfile -File C:/Users/Nitro/Ghost/reports/ghost-pr-fixes-2026-11-01/pr-32433/run-unit.ps1 -Worktree C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031
```

Exact final summary:

```text
v22.23.4
RUN  v4.1.12
Test Files  8 passed (8)
     Tests  47 passed (47)
  Duration  48.85s (transform 1.04s, setup 0ms, import 8.57s, tests 3.19s, environment 31.78s)
Exit: 0
```

The runner copies production files and tests into a fresh temporary directory under `apps/admin`, rewrites imports to isolated context/API shims, invokes the installed pinned Node and Vitest directly, and uses `--pool=threads --maxWorkers=1 --no-file-parallelism` with `NODE_OPTIONS=--max-old-space-size=2048`. The test files include the original framework `useForm` suite, the real settings and Design hooks, the real Navigation, Stripe Direct, Portal and User Detail components with mocked surrounding dependencies, and the save-button hook. The runner removes the sandbox in `finally`.

## Format and Oxlint

```powershell
powershell -NoProfile -File C:/Users/Nitro/Ghost/reports/ghost-pr-fixes-2026-11-01/pr-32433/run-checks.ps1 -Worktree C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031
```

Exact final output:

```text
Checking formatting...

All matched files use the correct format.
Finished in 545ms on 15 files using 1 threads.
Exit: 0
```

The runner copied the 15 changed files and repository formatting/lint configuration and plugins into a fresh sandbox. It ran `oxfmt --check --threads=1` and `oxlint --config .oxlintrc.json --deny-warnings --threads=1` sequentially; Oxlint printed no output and exited 0. The first setup attempt passed format but Oxlint failed to load its plugin because `.dependency-cruiser.cjs` was absent. The second copied that config, the resolver and service inventory and passed. `git diff --check` also exited 0.

## Scope and limitations

The tests use simulated API and context updates. They do not establish live React Query scheduling, browser keyboard behavior, a backend write, or the User Detail slug-change/404 path. `UserDetailModal` retains the last user while a new slug lookup is pending, but a settled empty/404 lookup can unmount the editor; that path remains untested. Other `useForm` consumers may have their own response setters and are outside this focused change. The orchestrator owns full type, ESLint, build, browser and integration validation.

At inspection time `git merge-tree --write-tree 3b395b6b082bb995bc8dc8d7b648fea7732fe839 HEAD` succeeded with tree `16f55e77bb54ca94ba1fe0f60230dd65c39613e4`; that command covers the committed PR head, not the uncommitted fixes. Comparing the two commits among changed production paths showed differences only in `use-form.ts` and `use-setting-group.tsx`. None of the six new test paths exists on fetched main. The orchestrator must check the final uncommitted patch in its integration context.

Every sandbox created by these runners was removed. The pre-existing blocked sandbox `apps/admin/.tmp-pr32433-probe-af6a3ab5bb37412e8e428eb977b8a7d2` was left untouched. No commits or remote operations were performed.

## Orchestrator completion

The statements above record the worker phase. The final regression commit is `dcb5bec1c377a22b517b314d31056e1085be611e`; the implementation commit is `1958aa6821284e1caba9c6cf88c222753d6aacf8`. Both passed all repository commit hooks, including real project ESLint, without suppression or fake declarations. Shade declarations were generated using its official declaration build in a separate sandbox.

The first regression commit attempt reported six test-only ESLint issues: four mocked buttons needed `type="button"` and two mock-call assertions needed correctly typed arguments. After fixing these, the affected suite passed **16 tests in 6 files** and the hook passed. These 16 are a subset of the 47 above. Each commit wrapper restored caches, removed its temporary declarations link, and removed its sandbox.

Final `git merge-tree --write-tree 3b395b6b082bb995bc8dc8d7b648fea7732fe839 1958aa6821284e1caba9c6cf88c222753d6aacf8` succeeded with tree `f21c7a795cc55ef685edc75ce07eea8ff31979a2`.
