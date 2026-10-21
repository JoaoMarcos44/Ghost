# Validation record for the eleven Ghost fixes

Source base: Ghost `6.73.0-rc.0`, commit `11af3e13fdd310492ec6988585f2ed64be7a54ed`.
Runtime: Node.js `22.23.4`, pnpm `12.10.1`, Vitest `4.1.11`, Windows.
The individual PRs target `TryGhost/Ghost:main` from separate fork branches.

## Focused regression results

Each folder contains the command, working directory and exit code in JSON, and the corresponding captured output in a `.log` file. RED means the reported behavior assertion failed before its correction; GREEN means the focused suite passed after that correction. These counts are per run, not a claim of distinct tests or full product coverage.

| Finding | Issue | PR | GREEN tests |
| --- | --- | --- | ---: |
| B1 JSON-LD image arrays | [32129](https://github.com/TryGhost/Ghost/issues/32129) | [32132](https://github.com/TryGhost/Ghost/pull/32132) | 34 |
| B2 SDK initial history state | [32130](https://github.com/TryGhost/Ghost/issues/32130) | [32133](https://github.com/TryGhost/Ghost/pull/32133) | 11 |
| B3 GIF URL classification | [32134](https://github.com/TryGhost/Ghost/issues/32134) | [32135](https://github.com/TryGhost/Ghost/pull/32135) | 2 |
| B4 Navigation homepage subdirectory | [32136](https://github.com/TryGhost/Ghost/issues/32136) | [32137](https://github.com/TryGhost/Ghost/pull/32137) | 1 |
| B5 Telephone URI suffix | [32138](https://github.com/TryGhost/Ghost/issues/32138) | [32139](https://github.com/TryGhost/Ghost/pull/32139) | 2 |
| B6 Media import encoding | [32141](https://github.com/TryGhost/Ghost/issues/32141) | [32142](https://github.com/TryGhost/Ghost/pull/32142) | 58 |
| B7 Scheduled date timezone conversion | [32147](https://github.com/TryGhost/Ghost/issues/32147) | [32148](https://github.com/TryGhost/Ghost/pull/32148) | 1 |
| B8 Local comment calendar | [32149](https://github.com/TryGhost/Ghost/issues/32149) | [32150](https://github.com/TryGhost/Ghost/pull/32150) | 61 |
| C1 SQLite automation dates | [32140](https://github.com/TryGhost/Ghost/issues/32140) | [32151](https://github.com/TryGhost/Ghost/pull/32151) | 104 |
| C2 Portal fragment attribution | [32143](https://github.com/TryGhost/Ghost/issues/32143) | [32144](https://github.com/TryGhost/Ghost/pull/32144) | 20 |
| C3 First UTM snapshot | [32145](https://github.com/TryGhost/Ghost/issues/32145) | [32146](https://github.com/TryGhost/Ghost/pull/32146) | 22 |

Important distinctions:

- B1's first post-fix attempt timed out during setup. The later `b1-green-local-hook` run passed 34 tests; the setup timeout is not presented as an assertion failure.
- B4/B5 share a RED command; their GREEN runs were separate. One B4 test contains four fixtures. B7's one test contains winter, spring-gap and fall-overlap fixtures and uses synthetic model operations.
- B6/C2/C3 share a RED command containing six assertion failures and 74 passing tests. Their GREEN runs were separate. C3's GREEN also includes the existing server referrer-translator tests.
- C1's RED used the original writer and poller with the formatter/migration support still present. The future-step selection assertion failed; the two supporting migration cases passed. This is not described as a run of the entire unmodified tree.
- C1's GREEN is three in-memory SQLite integration cases plus 101 existing repository tests. The non-SQLite migration guard was mocked; no live MySQL migration was tested.

## Combined verification

The code and tests from all eleven branches were combined in an isolated worktree; per-PR member-attribution README edits were not needed in that combined source/test tree. No combined branch was submitted as a product PR.

`combined/combined-pnpm-check-stable.json` records **exit 130** for `pnpm check`:

- Formatting passed on 7,110 files.
- Oxlint passed, allowing the command to reach the Nx lint/build graph.
- Nx reported 67 tasks: 30 succeeded, 33 failed, and four skipped. Its captured per-task failure logs are in `combined/nx-task-logs/`.
- Windows `cmd` did not interpret scripts such as `pnpm run '/^lint:/'`, the Core regex containing `|`, or the Unix `rm` command. The Shade build also reported Rolldown `INVALID_OPTION` / missing `options.input`. The Shade failure was not established as a baseline failure by a separate clean-base build, so it remains unresolved rather than being declared harmless.
- Because `check` chains stages with `&&`, the remaining lint stages and `pnpm test` were not reached. This record does not claim a successful full monorepo build, type check, lint, or test suite.

Two early formatter attempts were superseded while checkout line-ending normalization was incomplete. Windows `core.autocrlf` had produced CRLF worktree bytes for source blobs stored as LF. Only tracked files with LF index content and CRLF/mixed worktree content were normalized in the sandbox. A static sample then passed, followed by the complete formatting pass above. No mass formatting change was committed to any PR.

The temporary root scripts added only `--threads=2` to Oxfmt/Oxlint. Nx ran with two concurrent tasks, Vitest with one worker per run, and Node heaps were bounded to 2 GiB. These validation settings, temporary ignore rules, runner configuration, caches and generated outputs were excluded from all source PRs.

A separate shell experiment changed `ComSpec` to Git Bash for one SDK lint command. It failed with `/d: Is a directory` and exit 1; it is not recorded as a successful workaround. The source PRs do not change repository shell behavior.

Combined regression results are recorded in `combined/combined-navigation-regressions.*` and `combined/combined-core-regressions.*`. The navigation run passed **three tests across two files**. The Core run passed **239 tests across eight files**, including the real SQLite writer/poller regression and the existing repository/referrer tests. Both commands exited 0. These combined counts are additional runs, not distinct-test totals to add to the per-PR counts.

## Reproducing the SQLite-only validation

From a bootstrapped checkout of C1, copy `c1/sqlite-validation.config.ts` to `ghost/.c1-vitest.config.ts` and run from `ghost/`:

```sh
pnpm exec vitest run --config .c1-vitest.config.ts --maxWorkers=1 --no-file-parallelism
```

The temporary configuration uses the existing Core unit setup and a private in-memory SQLite fixture. It allows the integration regression to run without the MySQL-backed integration project. It raises setup timeouts for the loaded Windows host; no source test assertion was removed. The configuration is evidence/support documentation and is not part of C1's code diff. The combined Core configuration is archived separately in `combined/core-regression-validation.config.ts`.

## Contribution checks and external gates

Commits retained repository hooks. Formatting/ESLint and relevant staged dependency/documentation checks passed. The changeset reminder's temporary checkout failed with `ERR_PNPM_FROZEN_LOCKFILE_WITH_OUTDATED_LOCKFILE`; it was nonblocking and is not counted as a passing versioning check. B3 includes the required patch changeset for its publishable package; the other changes are Core or private apps/SDK.

The GitHub snapshot found all eleven PRs open as drafts. The successful labeling action is metadata automation, not product test CI. CodeRabbit explicitly skipped review for drafts; its green status does not mean code review passed.

C1's successful migration-checklist job only posted [an unchecked checklist](https://github.com/TryGhost/Ghost/pull/32151#issuecomment-6327077379). The in-memory tests establish repeatable `up()` conversion for the fixture, not staging performance, full migrator up/down lifecycle validation, or reviewer sign-off. The migration uses the repository's irreversible-migration helper. No staging or production database was touched. The Docker engine was unavailable; no live MySQL, legacy database suite, browser E2E, or full automation lifecycle result is claimed.

## Historical investigation

`historical/` retains the earlier investigation JSON records cited in the issue descriptions. Those records may use historical source revisions/runtimes; each issue distinguishes them from the current-base Vitest results above. The duplicate review records 29 successful public searches and no exact match within the documented search bounds. It is not an exhaustive guarantee that no duplicate exists.
