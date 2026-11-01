# PR 32433 behavioral probe validation

The parent agent took over after the initial launch was interrupted, corrected `run-probes.ps1` to invoke the worktree's pinned Node executable and installed Vitest entry point directly, and ran:

```powershell
powershell -NoProfile -File C:/Users/Nitro/Ghost/reports/ghost-pr-review-2026-11-01/pr-32433/run-probes.ps1 -Worktree C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031
```

Recorded result supplied by the parent (summary, not a verbatim stdout transcript):

```text
Node:       v22.23.4
Vitest:     4.1.12
Test files: 1 passed
Tests:      8 passed
Duration:   9.53s
Exit:       0
```

The runner uses `--pool=threads --maxWorkers=1 --no-file-parallelism` and `NODE_OPTIONS=--max-old-space-size=2048`. It extracts the hook source from head `2a62cbb7447c2c52e6b2be4029803f6ee64002d9` and base `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b`, changes imports to test doubles, and executes four scenarios against each revision:

1. With editing explicitly active, head retains B and stays open/unsaved after stale A completes; base retains B locally at that point but returns true and closes editing with `saved` state.
2. With editing never activated, a simulated context refresh carrying A replaces dirty B on both revisions. Head returns false after A completes; base returns true.
3. A callback shaped like the modal's unguarded `await handleSave(); close()` runs while A is pending and after B is entered. Head's callback completes before A and the mock receives only A; base's mock receives A and B and, for the test's A-then-B completion order, ends with B. This establishes the new rejected-second-request path for the harness, not all possible network orders.
4. The extracted Design hook receives a simulated A response after B is entered. Both revisions display A and a retry makes no additional mock API call; head returns false and remains unsaved after the first completion, while base returns true and becomes saved. The mock response has no local dirty flags.

These are hook tests using simulated API/context and, in scenario 3, a callback-shaped stand-in. They do not render the actual NavigationModal, Stripe Direct, Design modal, Shade components, or router; they do not exercise a live query cache, browser, or backend. The PR author's previously reported 28 focused tests were not rerun in this validation, and the full `pnpm check` was not run.

The parent's successful run used `.tmp-pr32433-probe-bf4b4416754847a98734ddd1247ec70d` and reports that the runner's `finally` block removed it. The earlier interrupted `pnpm exec` attempt had left `.tmp-pr32433-probe-af6a3ab5bb37412e8e428eb977b8a7d2`; two attempts to remove that older sandbox were blocked by execution policy, and it was not retried. See [audit.md](audit.md) for the original command and limitations.
