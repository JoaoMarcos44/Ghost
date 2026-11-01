# Toggle email spacing: validation evidence

Worktree HEAD: `af654561e2f883f086fd694abede433abfffff6b`. The following RED run happened after adding the two node regressions and the Ghost Core converter-to-email regression, but before changing the renderer. The runner copied the relevant source and tests into a disposable sandbox and used Node 22.23.4, Vitest 4.1.12, one worker and a 2048 MB Node heap.

Command:

```text
node.exe <worktree>/node_modules/vitest/vitest.mjs run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose koenig/kg-default-nodes/test/nodes/toggle.test.ts ghost/test/unit/server/services/email-service/toggle-email.test.ts
```

Exact excerpts from the RED output:

```text
× ToggleNode > exportDOM > preserves spaces between formatted heading words for email
  → expected 'Headingwords' to be 'Heading words'
× ToggleNode > exportDOM > preserves spaces between formatted content words for email
  → expected 'Helloworld' to be 'Hello world'
× Imported toggle email rendering > preserves spacing and formatting in the heading and content
  → Expected values to be strictly equal:
+ actual - expected

+ 'Headingwords'
- 'Heading words'

Test Files  2 failed (2)
     Tests  3 failed | 16 passed (19)
VITEST_EXIT=1
SANDBOX_REMOVED=True
```

After changing the renderer, the same command passed all 19 tests, including the original plain-email rendering test (`VITEST_EXIT=0`, `SANDBOX_REMOVED=True`). This first RED/GREEN run used the initial two-test-file version of `run-focused.py`; that script was then expanded for the checks below.

The expanded runner executed the same regressions plus `koenig/kg-html-to-lexical/test/html-to-lexical.test.ts` and a temporary byte-for-byte comparison against the original renderer. All 56 behavior/conversion tests passed; the extra comparison failed: the original emitted `<td class="kg-toggle-content"> Content </td>` for plain content and the new renderer emits `<td class="kg-toggle-content">Content</td>`. The existing formatted-output assertion still passed. The runner also passed ESLint for the changed node files and the Core test, and `oxfmt --check` for the Core test. The formatter reported 12 threads despite `RAYON_NUM_THREADS=1`; all processes exited and the sandbox was removed.

The expanded runner uses a sandbox Vitest configuration with source aliases; it is not the repository's full `pnpm check`.

Separately, `run-core.py` copied Ghost Core's actual `vitest.config.ts`, setup files, tracked Core sources and the upstream integration regression into a new sandbox. It added sandbox-local source aliases, inlining and cache locations to the copied configuration, while retaining the Core unit project and its real setup and hooks. It also redirected the test content and database paths into the sandbox. Command, run from the copied `ghost/` directory:

```text
node.exe <worktree>/node_modules/vitest/vitest.mjs run --config vitest.config.ts --project unit --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose test/unit/server/services/email-service/toggle-email.test.ts
```

Result: `Test Files 1 passed (1)`, `Tests 1 passed (1)`, `CORE_VITEST_EXIT=0`, `SANDBOX_REMOVED=True`. No browser, full `pnpm check`, or real email delivery was run. The existing PR changeset already declares a patch release for `@tryghost/kg-default-nodes`.

A later optional `oxfmt --help` command, which included creating and cleaning a new sandbox, was rejected before process creation with `blocked by policy`. It was not retried; the formatter run reported above had already completed and its sandbox had already been removed.

## Final committed-source rerun

After commit `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`, the maintained runner separates the exploratory byte comparison behind `--compare-baseline` and pins that comparison to the original PR head `af654561e2f883f086fd694abede433abfffff6b`. The comparison's historical failure above remains valid; exact bytes are not the behavior contract. The default command is:

```text
python -X utf8 reports/ghost-pr-fixes-2026-11-01/pr-32432/run-focused.py
```

It passed **56 tests in 3 files**, both ESLint commands and formatting, all exit 0. Formatting used `--threads=1`. The sandbox was removed. The separate Core-project result above is an additional configuration check of the same regression, not an extra distinct test to add to the 56.
