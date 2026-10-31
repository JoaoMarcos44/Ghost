# Publication and final verification

Exactly three source PRs were opened in TryGhost/Ghost. The open-PR count was checked immediately before each creation: 0, then 1, then 2. All three are drafts while the documented broad, browser and database validation remains outstanding. No fourth PR was created for the documentation branch.

| Change | Issue | Pull request | Source commit |
| --- | --- | --- | --- |
| Settings pending save | [#32421](https://github.com/TryGhost/Ghost/issues/32421) | [#32433](https://github.com/TryGhost/Ghost/pull/32433) | `2a62cbb7447c2c52e6b2be4029803f6ee64002d9` |
| Bulk label removal | [#32426](https://github.com/TryGhost/Ghost/issues/32426) | [#32434](https://github.com/TryGhost/Ghost/pull/32434) | `779635571ba48999068a61ae56ec1ae98678509e` |
| Toggle HTML conversion | [#32428](https://github.com/TryGhost/Ghost/issues/32428) | [#32432](https://github.com/TryGhost/Ghost/pull/32432) | `af654561e2f883f086fd694abede433abfffff6b` |

Four new issues were published in this phase: #32426 (labels), #32427 (pagination), #32428 (toggle), and #32429 (product-card links). Existing issues #32420 and #32421 remain part of the audit record. Pagination, product-card links and subscriber history have no PR in this batch.

## Validation status

170 focused tests passed: 28 settings tests, 89 Core tests for labels/config, and 53 toggle/converter tests. Regression evidence and the real-repository SQLite rollback experiment are documented in the per-change reports. These are not a claim that all repository tests passed.

All three source commits passed their unmodified commit hooks, including applicable formatting, ESLint, dependency-boundary checks, staged-file inspection and release-intent checks. Hooks were not disabled. Settings' new test component was capitalized to satisfy React hook rules. Label acceptance expectations were adjusted to avoid assigning an untyped asymmetric matcher to an object property, while still checking the action, requested IDs, label count and single request.

The original Windows `pnpm` command existed only as shell wrappers on PATH, so the formatter's direct Node spawn failed. A temporary native launcher established the cause. The installed official pnpm executable was then found and placed on PATH for the final source commits. Generated Shade declarations were produced in a sandbox with the official TypeScript, alias-rewrite and declaration-check commands, all exit 0, and temporarily linked for type-aware lint. No declaration stubs or rule suppression were used.

Outstanding validation is explicit in every draft PR:

- The batch's `pnpm check` attempt stopped in global formatting, reporting 4,763 files, mostly outside the patch. It did not execute full lint/tests. The changed converter test was subsequently formatted by the passing hook. Global formatting causes were not fully diagnosed; no unrelated formatting changes were committed.
- Admin acceptance did not execute: the required Chromium was missing, and its download timed out twice.
- New MySQL HTTP tests and the config snapshot were not executed locally because the database/Docker engine was unavailable.
- The broad Koenig test run was interrupted for runtime. Only the focused 16-node and 37-converter results are reported as passed.

CI and maintainer review remain outstanding. Automated labeling success is not treated as product/test CI approval.

## Documentation and images

All PRs contain an issue reference, explanation, validation boundaries, reproduction/report links and a themed infographic. The images and reports live on `JoaoMarcos44/Ghost`, branch `docs/functional-fixes-20261031`, without adding generated graphics to the source diffs.

The published PNG blobs were compared with the local files using `git hash-object` and matched:

| Theme | File | Git blob SHA |
| --- | --- | --- |
| Engineering blueprint | `settings/infographic.png` | `a37fb6b24672365aa0b35bc1ac8b99f8ae1ab9f9` |
| Paper-cut workshop | `labels/infographic.png` | `28f76836ed810a0ec499761967885aaf623a23ec` |
| Editorial print | `toggle/infographic.png` | `9cf89a52f03d1e60d87ae9f6a62c0121c03451b5` |

## Cleanup and preservation

The focused-test, browser-download, global-validation and Shade-declaration sandboxes were removed. The temporary Shade junctions were detached, the final commit runtime directory and its Node cache were removed, and task-owned test/build processes ended. The three source worktrees and this documentation are retained as reviewable deliverables. Existing unrelated checkout artifacts were preserved.

Two earlier cleanup actions remain blocked by automatic approval review:

- `C:\Users\Nitro\Ghost\.tmp-sandbox-settings-687f4ed0` from the earlier audit phase.
- `C:\Users\Nitro\Ghost\.tmp-sandbox-commit-env-20261031`, the first temporary launcher directory from this phase.

The latest rejection supplied only `blocked by policy`, without a more specific reason. These targets were not retried using another deletion mechanism. The separate labels cleanup incident, where a worker attempted an alternative before receiving the stop instruction, is transparently recorded in [labels/results.md](labels/results.md); that sandbox no longer exists. A filesystem ReadOnly error during global validation was separately diagnosed and resolved within that sandbox; it was not an approval-policy rejection.

