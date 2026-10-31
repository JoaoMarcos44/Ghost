# Ghost functional audit and three pull requests

Scope: functional P0/P1/P2 defects in TryGhost/Ghost, excluding security and daybreaks. Source audit and implementation base: `5d4430c8c157990adbd69400f4cee9795037fbbb`. The upstream branch subsequently advanced to `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b` with dependency changes; the local test environment retained the audited dependency set.

## Findings and selection

No P0 or P1 was confirmed. Four additional P2 defects were reproduced across ten targeted review rounds. With the two earlier confirmed cases, six issues are documented. P2 is the proposed audit assessment, not a maintainer-assigned priority.

| Defect | Issue | Selected for this batch |
| --- | --- | --- |
| Settings edits lost during a pending save | [#32421](https://github.com/TryGhost/Ghost/issues/32421) | Yes |
| Bulk label removal changes its own member selection | [#32426](https://github.com/TryGhost/Ghost/issues/32426) | Yes |
| Toggle HTML conversion loses rich content | [#32428](https://github.com/TryGhost/Ghost/issues/32428) | Yes |
| Paginated get helper omits posts | [#32427](https://github.com/TryGhost/Ghost/issues/32427) | Issue only |
| Product HTML conversion mistakes a description link for its button | [#32429](https://github.com/TryGhost/Ghost/issues/32429) | Issue only |
| Historical subscriber counts change retroactively | [#32420](https://github.com/TryGhost/Ghost/issues/32420) | Issue only |

Exactly three source PRs are authorized. The documentation branch in the contributor's fork has no PR and does not consume a fourth slot. The unrelated All time analytics candidate was excluded because existing draft PR #32295 already covers it. Unreproduced hypotheses were not promoted to confirmed findings.

## Review coverage

1. Import/export and slug handling.
2. Scheduling and publishing transitions.
3. Members, CSV and bulk actions.
4. Newsletter queues and retries.
5. Admin lists, filters and selection.
6. Editor autosave and revision history.
7. Theme helpers, pagination and feeds.
8. Analytics ranges and historical series.
9. HTML/Lexical card conversion.
10. Public applications, search and comments.

Astra (`gpt-6-astra`, high reasoning) reviewed the selection and the final patches. Its two concrete pre-publication findings were resolved: newer edits must remain dirty during a save, and multi-label removal must detect support in independently deployed Core versions. The final static review found no further functional blocker; this was not a substitute for execution.

## Evidence

| Change | Focused execution | Boundaries |
| --- | --- | --- |
| Settings | 28 hook/context tests passed after an expected failing regression | API/error dependencies are mocked; not browser E2E |
| Labels | 89 Core unit tests passed; real-repository SQLite harness checked stable selection and rollback | Admin acceptance did not start because the Chromium download timed out; MySQL HTTP tests remain pending |
| Toggle | 16 node tests and 37 converter tests passed after expected failures | Broad Koenig suite stopped for runtime; no claim of a full suite pass |

All focused tests used Node 22.23.4, bounded concurrency and disposable sandboxes. Runner/setup failures are documented separately from assertion failures. A wrapper returning success or failure was never treated as proof when the underlying tests had not executed.

See [settings results](settings/results.md), [labels results](labels/results.md), [toggle evidence](toggle/evidence.md), and [repository validation](validation/results.md). The root `pnpm check` attempt stopped in formatting and did not reach full lint/tests. Draft status preserves these outstanding validation requirements.

## Infographics

[Open the visual report](infographic_report.md): settings uses an engineering blueprint; labels uses a paper-cut workshop; toggle uses editorial print. Each change has its own `infographic.png`, explanatory `infographic_report.md`, prompt inputs and generation instructions. The native image generator produced all three images, which were visually inspected. The prompt helper ran directly with Python, without uv.

The illustrations explain architecture, failure and corrected behavior. They are conceptual documentation rather than screenshots or test evidence. Assets live on the fork's documentation branch so the source PRs contain only their focused implementation, tests and required release metadata.

## Publication and cleanup

Final PR links, commit SHAs, hook results and cleanup exceptions are recorded in [publication.md](publication.md).

