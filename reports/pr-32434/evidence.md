# PR #32434: evidence and validation limits

## Scope

The latest source commit is [`fcb5149b11d4b94433fbb682a37be7d116ef5c33`](https://github.com/JoaoMarcos44/Ghost/commit/fcb5149b11d4b94433fbb682a37be7d116ef5c33), simplifying the member-ID query. The query-limit and response-validation fixes remain in [`1cdac3b534035e02d995160c0b37d330e47b5ea5`](https://github.com/JoaoMarcos44/Ghost/commit/1cdac3b534035e02d995160c0b37d330e47b5ea5), following the [regression-test commit](https://github.com/JoaoMarcos44/Ghost/commit/0671fbd30c6bfb31e59c00777bdd20757ba2e32a). The earlier review examined [`779635571ba48999068a61ae56ec1ae98678509e`](https://github.com/JoaoMarcos44/Ghost/commit/779635571ba48999068a61ae56ec1ae98678509e). The first individual merge check used main `3b395b6b082bb995bc8dc8d7b648fea7732fe839`; the latest check below uses the newly fetched main.

The implementation bounds the [Core relation lookup](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/ghost/core/server/services/members/members-api/repositories/member-repository.js) and validates the [Admin framework response](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/apps/admin-x-framework/src/api/members.ts). The related regression tests are in [Core](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/ghost/test/unit/server/services/members/members-api/repositories/member-repository.test.js) and the [Admin framework](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/apps/admin-x-framework/test/unit/api/members.test.tsx).

## Isolated test results

The recorded Windows runs used Node `v22.23.4`, Vitest `4.1.12` and an SQLite build with `MAX_VARIABLE_NUMBER=32766`. Tests ran in temporary copies of the checkout with dependency directories linked and used without modification; temporary directories and Vite caches were directed into the sandbox. Environment settings included `NODE_OPTIONS="--conditions=source --max-old-space-size=2048"`, `UV_THREADPOOL_SIZE=1` and `TSX_DISABLE_CACHE=1`. Vitest used one worker and no file parallelism. The framework's temporary Vite configuration resolved workspace packages with the `source` condition because workspace builds were unavailable. The recorded sandboxes were removed and no test processes remained.

The following commands were run from the corresponding package directories in the sandbox copy. `$GhostSource` denotes the source worktree supplying the installed Node and Vitest binaries:

```powershell
$Node = "$GhostSource/node_modules/.bin/node.exe"
$CoreVitest = "$GhostSource/ghost/node_modules/vitest/vitest.mjs"
$FrameworkVitest = "$GhostSource/apps/admin-x-framework/node_modules/vitest/vitest.mjs"

# Working directory: sandbox/checkout/ghost
& $Node $CoreVitest run --maxWorkers=1 --no-file-parallelism test/unit/server/services/members/members-api/repositories/member-repository.test.js

# Working directory: sandbox/checkout/apps/admin-x-framework
& $Node $FrameworkVitest run --maxWorkers=1 --no-file-parallelism test/unit/api/members.test.tsx
```

The Core suite exited 0 with **71 passed**; the framework suite exited 0 with **43 passed**. After the final equivalent switch to `z.looseObject`, the framework command with `-t 'bulk-edit'` exited 0 with **5 passed and 38 skipped**. The 5 are a focused repeat, not an additional independent suite.

Before the fix, the Core large-selection regression failed with `The label lookup exceeded SQLite parameter limits`: it supplied 32,765 member IDs and 1,002 label entries, including a duplicate. The selected-ID query was stubbed; relation lookup and deletion used real model methods and in-memory SQLite. The final test verifies that each lookup has at most 999 bindings and that an unselected relation remains. The framework's focused regression initially had **3 failed, 2 passed and 38 skipped**: missing, string-valued and negative `unsuccessful` values were accepted. The two valid response examples, with and without `action`, already passed.

Separately, an in-memory SQLite behavior probe used the actual repository, relation query and bulk-delete plugin with a small SQL selection-filter stand-in. It reproduced the original two-request defect, confirmed one selection and four intended relation removals, and checked invalid, ambiguous and empty-selection cases. An SQLite trigger caused a real failure during the second delete chunk; the transaction restored all **102 relations**. The probe also used the API frame and serializer and confirmed that serialized JSON omits `bulk.action`. It did not exercise Ghost's real NQL selection, an HTTP server, MySQL or the browser.

Focused ESLint and formatting checks exited 0, and the final regression and implementation commit hooks passed. The first implementation-hook attempt timed out at the wrapper's 180-second limit; the subsequent unchanged hook passed after the stale local main was fast-forwarded to the already fetched revision. Its sandbox and process tree were cleaned.

## Second simplicity evaluation

The new `removeLabels` branch now obtains distinct member IDs using `.distinct().pluck('members.id')`. It replaces `.select('members.id').distinct()` followed by `memberRows.map(row => row.id)`. Only that query and two test mocks changed; the transaction, batching and legacy action remain unchanged.

The Core command above was rerun against this change and exited 0 with **71 tests passed**. The framework was unchanged; its earlier 43-test pass was not repeated. From the copied `ghost/` directory, the following checks also exited 0:

```text
node.exe <sandbox>/repo/node_modules/eslint/bin/eslint.js --no-cache core/server/services/members/members-api/repositories/member-repository.js test/unit/server/services/members/members-api/repositories/member-repository.test.js
node.exe <sandbox>/repo/node_modules/oxfmt/bin/oxfmt --threads=1 --check core/server/services/members/members-api/repositories/member-repository.js test/unit/server/services/members/members-api/repositories/member-repository.test.js
```

An additional sandbox-only Knex comparison compiled the old and new queries with SQLite and MySQL clients: SQL and bindings were identical. Real SQLite execution returned the same member IDs for a join producing duplicate rows, an empty selection, and rows visible within the active transaction. This does not establish MySQL runtime behavior or Ghost's full NQL filter behavior.

The existing in-memory SQLite repository probe was rerun against the copied changed source. It exited 0, confirming one selection, four intended removals, invalid and empty cases, and rollback of all **102 relations** after an injected failure during a later deletion. Its SQL selection stand-in remains a coverage limitation.

The rerun used one worker, `NODE_OPTIONS=--conditions=source --max-old-space-size=2048` and `UV_THREADPOOL_SIZE=1`. Temporary scripts and outputs stayed inside the sandbox; the sandbox was removed and no matching processes remained. `git diff --check` exited 0. No benchmark was run, so this simplification makes no latency or memory improvement claim.

Commit `fcb5149b11d4b94433fbb682a37be7d116ef5c33` passed the unchanged repository commit hooks. Its hook sandbox was removed. A new individual merge check exited 0 with tree `6ae2fe7efd238045414f9c5b42431272ab8bdb4e`:

```text
git merge-tree --write-tree 36d678dadd294555a9688f29b6a5ff86077dd8b6 fcb5149b11d4b94433fbb682a37be7d116ef5c33
```

This establishes a conflict-free source merge at those revisions; it does not establish runtime validation on the merged tree.

## Typecheck and coverage limits

Two typecheck attempts in the isolated framework copy failed:

```powershell
$Typecheck = "$GhostSource/apps/admin-x-framework/node_modules/@typescript/native/bin/tsc"
& $Node $Typecheck --noEmit --customConditions source
& $Node $Typecheck --noEmit --customConditions source --allowImportingTsExtensions
```

The first exited 1 with TS5097 errors for workspace imports ending in `.ts`. The second exited 1 with 160 diagnostics, including unresolved workspace aliases and SVG imports. The likely cause is checking workspace source under the framework compiler configuration instead of consuming built declarations; the evidence does not establish that every diagnostic was pre-existing. Neither attempt is an isolated typecheck pass.

Browser acceptance, HTTP and MySQL suites, the full build and full `pnpm check` were not completed for this branch. The SQLite selection stand-in does not establish the real filter or transport behavior. No production benchmark established transaction duration, memory usage or scale limits. The response parser can reject after a server-side commit, while existing cache invalidation runs only on success.

## Merge and CI snapshot

The individual command below exited 0 with tree `aabf9ca607396d4f1652e7635cd9af716759046f`; it establishes a conflict-free merge at these exact commits, not successful runtime validation:

```powershell
git merge-tree --write-tree 3b395b6b082bb995bc8dc8d7b648fea7732fe839 1cdac3b534035e02d995160c0b37d330e47b5ea5
```

At the recorded snapshot, [CI](https://github.com/TryGhost/Ghost/actions/runs/41330452605) and [Tinybird](https://github.com/TryGhost/Ghost/actions/runs/41330452553) were `action_required` and required maintainer authorization. That status does not establish passing checks.

After publishing the simplification, both the source branch and PR head reported `fcb5149b11d4b94433fbb682a37be7d116ef5c33`. Its new [CI run](https://github.com/TryGhost/Ghost/actions/runs/41343106718) and [Tinybird run](https://github.com/TryGhost/Ghost/actions/runs/41343106731) also reported `action_required`. Local results do not replace authorization and execution of those workflows.
