# PR #32434: bound bulk label lookups and validate responses

Bulk removal selects member IDs once and removes the selected label relations in one transaction. The previous lookup passed both complete ID lists to one query, so large SQLite selections could exceed its parameter limit. The follow-up deduplicates label IDs and batches both lists in groups of 400 before using the existing transactional delete. It does not change the legacy model lookup or the repository's action validation.

The client now parses both bulk response statistics as nonnegative integers. The current UI consumes `unsuccessful`. The parser accepts responses with or without `action` and retains extra fields, because the existing serializer omits `action`. `stats.successful` describes selected relation IDs, not distinct members, and may differ from affected rows under concurrent changes.

The [earlier audit](../../ghost-pr-review-2026-11-01/pr-32434/audit.md) records the SQLite boundary and response mismatch at `779635571ba48999068a61ae56ec1ae98678509e`. The serializer mismatch predates the PR. The correction is in local commit `1cdac3b534035e02d995160c0b37d330e47b5ea5`, following regression commit `0671fbd30c6bfb31e59c00777bdd20757ba2e32a`.

## Validation

In sandbox copies of the checkout, the Core test reproduced the SQLite limit using 32,765 selected member IDs and 1,002 label entries, including a duplicate. The selected-ID query was stubbed; the relation lookup and delete used the real model methods and in-memory SQLite. The response tests reproduced acceptance of malformed statistics. The final Core and framework suites passed with these commands, from the respective copied package directories:

```powershell
$Node = '<worktree>/node_modules/.bin/node.exe'
$CoreVitest = '<worktree>/ghost/node_modules/vitest/vitest.mjs'
$FrameworkVitest = '<worktree>/apps/admin-x-framework/node_modules/vitest/vitest.mjs'

# cwd: sandbox/checkout/ghost
& $Node $CoreVitest run --maxWorkers=1 --no-file-parallelism test/unit/server/services/members/members-api/repositories/member-repository.test.js
# cwd: sandbox/checkout/apps/admin-x-framework
& $Node $FrameworkVitest run --maxWorkers=1 --no-file-parallelism test/unit/api/members.test.tsx
```

Core passed 71 tests and the framework passed 43. After the final equivalent `z.looseObject` schema adjustment, the framework's `-t 'bulk-edit'` selection passed 5 tests with 38 skipped. A separate [SQLite behavior probe](../../ghost-pr-review-2026-11-01/pr-32434/behavior_probe.py) passed, including rollback of 102 relations after a real second-delete-chunk failure:

```powershell
python -X utf8 C:/Users/Nitro/Ghost/reports/ghost-pr-review-2026-11-01/pr-32434/behavior_probe.py
```

The probe uses an SQL stand-in for selection, so it does not exercise the real NQL filter or HTTP. Focused ESLint and formatting checks passed. Two initial source-condition typecheck attempts failed while resolving workspace sources. The [official framework typecheck subsequently passed](../validation/framework-types.md) on the combined main tree after real dependency declarations were built. A parse failure can happen after the server commits, while the existing mutation invalidates its cache only on success.

No browser acceptance, HTTP or MySQL suite, full build or full `pnpm check` was completed in this focused validation. Product workflows in `action_required` need maintainer authorization; that status is not a passing test result. See [evidence.md](evidence.md) for exact environment settings, failures and cleanup.

## Final integration status

The final source commit is published in the existing PR branch. All source commit hooks passed. The three fixes merge together with main without conflicts; combined-tree global formatting and Oxlint passed, and the official framework typecheck passed after real workspace declaration builds. Full `pnpm check` stopped at the Nx Windows socket-path limit, before its later test stages. See [integrated evidence](../validation/integrated.md) for exact SHAs, environment limits and the remaining CI/Tinybird maintainer-authorization block.
