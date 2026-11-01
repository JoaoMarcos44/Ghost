# PR #32433: retain edits while a save is pending

If a user saves A and edits B before A completes, an older response or context refresh could still replace B. Navigation and Stripe Direct could also close after a rejected overlapping save. The follow-up protects the tested dirty group and Design states through refreshes, applies saved responses only to the submitted state, and guards the affected Design, Portal and User Detail response setters. Navigation and Stripe Direct close only after a successful save. The save button also handles `false`, a pending shortcut and thrown errors without leaving a false saving state.

The `handleSave` contract now states that a pending call returns `false` without submitting, while a stale save can return `false` after the server has saved its earlier snapshot. Validation failure also returns `false`; save errors are thrown. The group forwards save options and retains the latest response as the cancel and unchanged-save baseline. These changes target the reproduced consumers and synchronization cases rather than redesigning every `useForm` caller.

The [earlier audit](../../ghost-pr-review-2026-11-01/pr-32433/audit.md) records findings at `2a62cbb7447c2c52e6b2be4029803f6ee64002d9`. Some overwrite paths already existed before that PR. The focused follow-up fixes those reproduced paths in `1958aa6821284e1caba9c6cf88c222753d6aacf8`, following regression commit `dcb5bec1c377a22b517b314d31056e1085be611e`. Both commits passed the unchanged repository hooks.

## Validation

The initial hook run reproduced four overwrites with 28 other tests passing. Separate RED tests reproduced the modal close, save-button and stale response cases. The final focused run passed all 47 tests in 8 files:

```powershell
powershell -NoProfile -File C:/Users/Nitro/Ghost/reports/ghost-pr-fixes-2026-11-01/pr-32433/run-unit.ps1 -Worktree C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031
```

The suite includes the original `useForm` tests, real settings and Design hooks, rendered Navigation, Stripe Direct, Portal and User Detail components, and the save-button hook. Surrounding API, context, UI and router dependencies are simulated. It uses Node 22.23.4, Vitest 4.1.12, one worker and a 2048 MB heap in a temporary sandbox.

The following sandbox check passed `oxfmt --check --threads=1` and `oxlint --config .oxlintrc.json --deny-warnings --threads=1` on 15 files:

```powershell
powershell -NoProfile -File C:/Users/Nitro/Ghost/reports/ghost-pr-fixes-2026-11-01/pr-32433/run-checks.ps1 -Worktree C:/Users/Nitro/Ghost/.worktrees/fix-settings-pending-save-20261031
```

These tests do not prove live React Query ordering, browser keyboard behavior or a backend write. The User Detail test keeps the same slug and does not cover a route change or settled 404. Other `useForm` consumers remain outside the focused validation. Full type, build, browser and integration checks are not established here. Product workflows in `action_required` need maintainer authorization; that status is not a passing test result. See [validation.md](validation.md) for the exact results, earlier setup failures and cleanup details.

## Final integration status

The final source commit is published in the existing PR branch. All source commit hooks passed. The three fixes merge together with main without conflicts; combined-tree global formatting and Oxlint passed, and the official framework typecheck passed after real workspace declaration builds. Full `pnpm check` stopped at the Nx Windows socket-path limit, before its later test stages. See [integrated evidence](../validation/integrated.md) for exact SHAs, environment limits and the remaining CI/Tinybird maintainer-authorization block.
