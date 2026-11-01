# Validation against main

The three final source commits merge cleanly with main `3b395b6b082bb995bc8dc8d7b648fea7732fe839`, individually and together. The combined Git tree is `b9e69e2a3fb484830f4c869dba287e9b56567408`. The commits were pushed normally to their existing fork branches and read back from GitHub:

| PR     | Source head                                | Individual merge tree                      |
| ------ | ------------------------------------------ | ------------------------------------------ |
| #32432 | `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef` | `19bb1367d49ffb5653ae5bea24a6712df75cc2c2` |
| #32433 | `1958aa6821284e1caba9c6cf88c222753d6aacf8` | `f21c7a795cc55ef685edc75ce07eea8ff31979a2` |
| #32434 | `1cdac3b534035e02d995160c0b37d330e47b5ea5` | `aabf9ca607396d4f1652e7635cd9af716759046f` |

## Full check and environment diagnosis

```powershell
python -X utf8 reports/ghost-pr-fixes-2026-11-01/validation/check-integrated.py
```

The runner uses native pnpm 12.16.1, Node 22.23.4, a 2048 MB Node heap, one Nx task at a time, no daemon, and a 180-second process-tree timeout. It archives the combined tree into a disposable project sandbox and redirects workspace dependencies, caches and temporary output there. It reuses external dependencies already installed in the settings worktree; it does not install main's new lockfile.

The final `pnpm check` reached these results:

| Stage                               | Result                                                                             |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| Global `format:check`               | Passed: 7,254 files, 58.744 seconds. The tool used 12 formatter threads.           |
| Global `lint:oxlint`                | Passed with `--deny-warnings`.                                                     |
| Nx package lint / dependency checks | Could not start: three default Nx plugins exceeded the Windows socket path length. |
| Later full test/build stages        | Not reached. No claim that the full `pnpm check` passed.                           |

The earlier formatting result of 4,776 failures was a sandbox preparation problem. Default `git archive` applied Windows `core.autocrlf` conversion. A [targeted probe](format-probe.json) found 246 and 10 CRLF lines in two unchanged main files exported normally; `git -c core.autocrlf=false archive` matched their LF Git blobs exactly, and both passed the installed formatter without edits. The corrected full export then passed formatting. No repository-wide source reformatting was applied.

An intermediate preparation attempt also failed because the temporary Git alternates file used CRLF; writing its metadata with LF resolved that setup failure before the final check. The original check results are retained in [integrated-results-first.json](integrated-results-first.json); the final run is in [integrated-results.json](integrated-results.json).

This Windows account additionally lacks symlink creation privilege (`WinError 1314`), so the sandbox could not reproduce 28 repository skill symlinks. Those failures are listed in the final JSON. They did not prevent the format or Oxlint results, but they are another limitation on treating this sandbox as a full native checkout. A correctly bootstrapped environment with symlink support and a short `NX_SOCKET_DIR` is needed for complete repository validation.

## Type check

The initial official framework typecheck failed because internal workspace packages had no compiled declarations. Building the seven real package declarations, in dependency order, resolved that failure. The [official framework typecheck then passed](framework-types.md) on the same combined source tree. Shade declarations were also built and verified with its own scripts. No fake declarations, source-rule suppression or source changes were used to obtain this result.

## GitHub status after publication

All three PRs reported `mergeable: true` and `mergeable_state: blocked`. CI and Tinybird runs on the published heads require maintainer authorization:

| PR     | CI                                                                                           | Tinybird                                                                                     |
| ------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| #32432 | [41330449699](https://github.com/TryGhost/Ghost/actions/runs/41330449699), `action_required` | [41330449856](https://github.com/TryGhost/Ghost/actions/runs/41330449856), `action_required` |
| #32433 | [41330450096](https://github.com/TryGhost/Ghost/actions/runs/41330450096), `action_required` | [41330450057](https://github.com/TryGhost/Ghost/actions/runs/41330450057), `action_required` |
| #32434 | [41330452605](https://github.com/TryGhost/Ghost/actions/runs/41330452605), `action_required` | [41330452553](https://github.com/TryGhost/Ghost/actions/runs/41330452553), `action_required` |

The available account cannot administer the upstream repository. Required statuses include “All required tests passed or skipped” and “Tinybird required tests passed or skipped”. This authorization block is separate from source compatibility; it was not bypassed. Browser, MySQL/HTTP and real email-delivery coverage remain as described in the individual reports.

## Cleanup and reproducibility

All new validation sandboxes and child command processes were removed after use. Real Shade declarations were retained only while the hooks and type checks needed them, then removed. Rerunning requires rebuilding them with `shade_declarations.py` and updating the temporary path reported by that script. The pre-existing settings probe directory whose deletion was rejected in the earlier audit was left untouched, as documented there.

The runners import the shared helper at `reports/ghost-prs-2026-10-31/validation/run_checks.py`, published alongside these records. They use the audited Windows checkout/runtime paths; adapt those paths before running elsewhere.
