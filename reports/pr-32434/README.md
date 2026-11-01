# PR #32434: remove labels from one stable member selection

[Latest implementation simplicity review](implementation-review.md).

[Pull request](https://github.com/TryGhost/Ghost/pull/32434) · [Final source commit](https://github.com/JoaoMarcos44/Ghost/commit/1cdac3b534035e02d995160c0b37d330e47b5ea5) · [Evidence](evidence.md) · [Visual explanation](infographic_report.md)

When members are filtered by label A, removing A and B in separate requests reuses the A filter. The first request removes A; the second then misses those members, leaving B behind. The new `removeLabels` action selects the matching member IDs once when the request runs and removes the requested relations in one transaction. Admin offers multiple-label removal only when Core advertises `config.capabilities.membersBulkRemoveLabels`; older servers retain the single-label flow.

The [repository change](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/ghost/core/server/services/members/members-api/repositories/member-repository.js) also deduplicates label IDs and looks up relations in pairs of batches of at most 400 member IDs and 400 label IDs. Each lookup therefore binds at most 800 IDs across the two lists, below SQLite's historical 999-variable limit. The selected relation IDs are deleted in the existing transaction. This bounds each lookup, but the operation still holds all selected member and relation IDs in memory; no production-scale benchmark was performed.

The [client response parser](https://github.com/JoaoMarcos44/Ghost/blob/1cdac3b534035e02d995160c0b37d330e47b5ea5/apps/admin-x-framework/src/api/members.ts) requires nonnegative integer `successful` and `unsuccessful` statistics, accepts responses with or without `action`, and retains extra fields. This accommodates the existing serializer, which can omit `action`. For this removal, `stats.successful` counts selected relation IDs, not distinct members, and can differ from rows actually affected during concurrent changes. A response parsing failure can occur after the server commits; the existing mutation invalidates its cache only on success.

## Validation and status

- In isolated sandbox runs, the Core repository suite passed **71 tests** and the Admin framework suite passed **43 tests**. After the final equivalent schema adjustment, the focused framework bulk-edit selection passed **5 tests**; 38 were skipped.
- A separate in-memory SQLite probe exercised the real relation lookup and delete path and restored all **102 relations** after an injected failure in the second delete chunk. Its selection filter was a SQL stand-in, not Ghost's real NQL filter.
- Focused lint and formatting checks and the final source commit hooks passed. The commit merges individually without conflicts into main `3b395b6b082bb995bc8dc8d7b648fea7732fe839`.
- Two isolated source-condition typecheck attempts failed during workspace declaration resolution. A passing isolated typecheck has not been established.
- Browser acceptance, HTTP and MySQL suites, the full build and full `pnpm check` were not completed for this branch. The captured [CI run](https://github.com/TryGhost/Ghost/actions/runs/41330452605) and [Tinybird run](https://github.com/TryGhost/Ghost/actions/runs/41330452553) were `action_required`, requiring maintainer authorization; that is not a passing result.

See [evidence.md](evidence.md) for commands, test setup, failures and remaining limits.
