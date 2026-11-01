# PR #32434 — implementation evidence

Worktree: `C:/Users/Nitro/Ghost/.worktrees/fix-member-label-removal-20261031`,
HEAD `779635571ba48999068a61ae56ec1ae98678509e`. The changes below are
uncommitted. The fetched main revision inspected was
`3b395b6b082bb995bc8dc8d7b648fea7732fe839`.

## Changes

- `ghost/core/server/services/members/members-api/repositories/member-repository.js`:
  batch distinct label IDs and selected member IDs in groups of 400 each, then
  delete the collected relations in the existing transaction.
- `ghost/test/unit/server/services/members/members-api/repositories/member-repository.test.js`:
  exercise the real relation lookup and bulk delete against in-memory SQLite,
  with a large synthetic selected-ID list and duplicate labels.
- `apps/admin-x-framework/src/api/members.ts` and
  `apps/admin-x-framework/test/unit/api/members.test.tsx`: validate bulk-edit
  stats at the mutation boundary, accept responses with or without `action`,
  and retain extra response fields.
- `apps/admin/src/members/members-bulk-actions.acceptance.test.tsx`: remove
  `action` from the fake response to match the observed server response.

## Runtime and isolation

Node `v22.23.4`, Vitest `4.1.12`, SQLite `MAX_VARIABLE_NUMBER=32766`.
Tests ran on Windows in temporary directories under `C:/Users/Nitro/Ghost`;
the tracked checkout was copied there, installed dependency directories were
linked and used without modification, and `TEMP`, `TMP`, `TMPDIR`, `XDG_CACHE_HOME` and Vite caches
were directed into the sandbox. `NODE_OPTIONS` was
`--conditions=source --max-old-space-size=2048`, `UV_THREADPOOL_SIZE=1`,
`TSX_DISABLE_CACHE=1`, and `pnpm_config_verify_deps_before_run=false`.
Vitest used `--maxWorkers=1 --no-file-parallelism`. The temporary Vite config
for the framework additionally resolved workspace packages with the `source`
condition because workspace builds were absent. No external service was used.

Each test sandbox reported `SANDBOX_REMOVED=True`; no test process remained.
One exploratory formatter run used 12 threads despite `RAYON_NUM_THREADS=1`;
it completed, and the final formatter check used `--threads=1` explicitly.
The temporary Python wrappers were inline and were removed with their sandbox;
the exact test invocations and persistent probe are recorded below.

## RED / GREEN

In the following commands, `$GhostSource` is the worktree path above and
`$Node` is `$GhostSource/node_modules/.bin/node.exe`. The working directories
were the corresponding copied `ghost` or `apps/admin-x-framework` directories
in the sandbox.

```powershell
$CoreVitest = "$GhostSource/ghost/node_modules/vitest/vitest.mjs"
$FrameworkVitest = "$GhostSource/apps/admin-x-framework/node_modules/vitest/vitest.mjs"

# RED, Core; cwd = sandbox/checkout/ghost
& $Node $CoreVitest run --maxWorkers=1 --no-file-parallelism test/unit/server/services/members/members-api/repositories/member-repository.test.js -t 'large selection'

# RED, framework; cwd = sandbox/checkout/apps/admin-x-framework
& $Node $FrameworkVitest run --maxWorkers=1 --no-file-parallelism test/unit/api/members.test.tsx -t 'bulk-edit'

# GREEN, same working directories
& $Node $CoreVitest run --maxWorkers=1 --no-file-parallelism test/unit/server/services/members/members-api/repositories/member-repository.test.js
& $Node $FrameworkVitest run --maxWorkers=1 --no-file-parallelism test/unit/api/members.test.tsx
```

- Core RED: exit 1, **1 failed, 70 skipped**, duration 69.12 s. The executed
  test failed with `The label lookup exceeded SQLite parameter limits`. It
  supplied 32,765 selected member IDs and 1,002 label entries including a
  duplicate; the selected-ID query was stubbed, while the relation lookup and
  deletion used the actual model methods and a single in-memory SQLite
  connection. It checks the unselected relation remains and bounds each lookup
  to 999 parameters or fewer.
- Framework RED: exit 1, **3 failed, 2 passed, 38 skipped**, duration 4.80 s.
  Missing, string-valued and negative `unsuccessful` counts were accepted
  instead of rejecting; the two valid responses with and without `action`
  already passed.
- Core GREEN: exit 0, **71 passed**, duration 24.13 s. Framework GREEN: exit
  0, **43 passed**, duration 12.55 s. After the schema was changed from
  passthrough objects to equivalent `z.looseObject` objects, the focused
  framework command above was rerun: exit 0, **5 passed, 38 skipped**, 4.14 s.
  Subsequent Core edits were formatting only.
- Test setup first failed before execution with `__dirname is not defined`
  under `--configLoader runner`; switching to the default config loader fixed
  that. Framework startup then exposed the missing built `@tryghost/nql-string`
  package; resolving workspace source in the copied Vite config allowed the
  RED and GREEN tests to run.

## Additional checks

The persistent [SQLite behavior probe](../../ghost-pr-review-2026-11-01/pr-32434/behavior_probe.py)
was rerun with:

```powershell
python -X utf8 C:/Users/Nitro/Ghost/reports/ghost-pr-review-2026-11-01/pr-32434/behavior_probe.py
```

Exit 0 and `SANDBOX_REMOVED=True`. It confirmed one selection, the intended
four relation removals, the empty/invalid cases and rollback of all 102
relations after an injected real second-delete-chunk failure. It also confirmed
the existing serializer omits `bulk.action`. Its selection filter is an SQL
stand-in, so it does not validate HTTP or Ghost's actual NQL filter. Its direct
model lookup still fails at 32,767 bindings; the new repository action avoids
that unbounded call through batching, while the legacy model method is unchanged.

Focused ESLint and formatting commands, each run in the copied checkout:

```powershell
$ESLint = "$GhostSource/node_modules/eslint/bin/eslint.js"
$Oxfmt = "$GhostSource/node_modules/oxfmt/bin/oxfmt"
# cwd = sandbox/checkout/apps/admin-x-framework
& $Node $ESLint --no-cache src/api/members.ts test/unit/api/members.test.tsx
# cwd = sandbox/checkout/apps/admin
& $Node $ESLint --no-cache src/members/members-bulk-actions.acceptance.test.tsx
# cwd = sandbox/checkout/ghost
& $Node $ESLint --no-cache core/server/services/members/members-api/repositories/member-repository.js test/unit/server/services/members/members-api/repositories/member-repository.test.js
# cwd = sandbox/checkout
& $Node $Oxfmt --threads=1 --check apps/admin-x-framework/src/api/members.ts apps/admin-x-framework/test/unit/api/members.test.tsx apps/admin/src/members/members-bulk-actions.acceptance.test.tsx ghost/core/server/services/members/members-api/repositories/member-repository.js ghost/test/unit/server/services/members/members-api/repositories/member-repository.test.js
```

All exited 0. The final format check followed normalization of a CRLF
line-ending mismatch. No browser acceptance, HTTP or MySQL suite, full build,
or `pnpm check` was run.

## Typecheck attempts and limit

Both commands below ran from `sandbox/checkout/apps/admin-x-framework`, using
the same Node binary and resource limits. They are source-condition attempts,
not the normal built-declaration workspace typecheck.

```powershell
$Typecheck = "$GhostSource/apps/admin-x-framework/node_modules/@typescript/native/bin/tsc"
& $Node $Typecheck --noEmit --customConditions source
& $Node $Typecheck --noEmit --customConditions source --allowImportingTsExtensions
```

1. Exit 1: TS5097 errors for workspace source imports ending in `.ts` without
   `allowImportingTsExtensions`.
2. Exit 1: **160 diagnostics**: 154 TS2307, 3 TS7006, 1 TS2741 and 2 TS2322.
   Examples include unresolved Shade aliases such as `@/components/primitives`
   and SVG imports ending in `?react`.

The likely cause is checking Shade's source under the framework's compiler
configuration rather than consuming its built declarations. This inference
does not establish whether all reported type errors are pre-existing. Work on
this failing check stopped after the second attempt; its sandbox was removed.

The parsed-response failure path is also worth review: the server may already
have committed an edit when parsing fails, and the existing mutation invalidates
the cache only on success. The schema validates both stats counters even though
the current UI reads only `unsuccessful`.

## Orchestrator completion

The statements above record the worker phase. The final regression commit is `0671fbd30c6bfb31e59c00777bdd20757ba2e32a`; the implementation commit is `1cdac3b534035e02d995160c0b37d330e47b5ea5`. Both passed all repository commit hooks. The first implementation hook attempt reached the changeset check but exceeded the wrapper's 180-second limit. After the stale local `main` was fast-forwarded to the already-fetched upstream revision, the unchanged hook passed. The timeout's process tree and sandbox were cleaned.

Final `git merge-tree --write-tree 3b395b6b082bb995bc8dc8d7b648fea7732fe839 1cdac3b534035e02d995160c0b37d330e47b5ea5` succeeded with tree `aabf9ca607396d4f1652e7635cd9af716759046f`.
