# Remaining Ghost fixes — draft PR batch

The user explicitly requested draft PRs for all remaining confirmed issues after the first three-PR batch. This follow-up covers pagination (#32427), product-card import (#32429), and historical subscriber counts (#32420). The earlier limit of three was superseded for these three additional drafts; no unconfirmed audit hypothesis is included.

Implementation base: `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b`. Runtime: Node 22.23.4, pnpm 12.16.1 and Vitest 4.1.12. Each change has its own branch and focused source/test diff.

| Change | Issue | Focused tests on 31 October | Important boundary |
| --- | --- | --- | --- |
| Preserve pagination when excluding posts | [#32427](https://github.com/TryGhost/Ghost/issues/32427) | 59 helper tests passed | MySQL E2E not run; cache sharing across different excluded IDs is reduced |
| Preserve the actual product button during HTML import | [#32429](https://github.com/TryGhost/Ghost/issues/32429) | 30 node + 39 converter tests passed | Custom markup must identify the CTA with the renderer's button class |
| Anchor historical subscriber values to the requested end | [#32420](https://github.com/TryGhost/Ghost/issues/32420) | 56 service tests passed | SQLite exercised; MySQL and the full HTTP path not run |

On 31 October, the 184 focused tests passed after regressions were shown to fail against the original behavior. Pagination's first full run had a five-second timeout in an existing error-handling test; a repeat with a fifteen-second timeout passed. The separate [1 November retest](validation/resume-tests.md) records execution on the final commits. No test result is inferred from a runner merely starting successfully.

The 1 November retest passed the same 184 focused tests on the final commits. Pagination needed a repeat with a 60-second timeout after the existing error-handling test exceeded 15 seconds; product's wrapper needed ANSI normalization after a successful test process. These details and cleanup outcomes are recorded in the retest report. No production code or tests changed during the resumption.

Astra (`gpt-6-astra`, high reasoning) reviewed all three final diffs and found no concrete blocker. That review was static and separate from execution. The pagination change preserves identical-query deduplication but removes the shortcut that shared normalized cache keys across different excluded IDs. Its performance impact was not measured. The history change preserves the separate current total and the existing date-grouping behavior.

Detailed evidence and reproduction commands:

- [Pagination](pagination/results.md)
- [Product-card import](product/results.md)
- [Subscriber history](history/results.md)

All three changes are prepared for draft publication, but GitHub rejected PR creation on 1 November 2026. **No follow-up PR has been created.** All three source branches are on the contributor fork. The three drafts from the first batch remain open. See [publication status and comparison links](publication.md).

Focused validation is not a claim that the entire repository, browser or MySQL suites passed. The representative `pnpm check` timed out after 180 seconds during formatting (exit 124); lint and the full test stage did not start. See [repository-check results](validation/results.md) and [final-commit retest](validation/resume-tests.md).

## Infographics

[Open the visual report](infographic_report.md). The themes are a transit map, a Bauhaus product poster and an observatory timeline. Each folder contains `infographic.png`, `infographic_report.md`, prompt inputs and exact generation instructions. All images were generated natively, inspected and corrected where needed. The helper was executed directly with Python, without uv.

The diagrams explain the failure and corrected behavior; they are not screenshots or validation badges. They are published on the contributor fork's documentation branch, keeping generated assets out of the source PRs.

The [earlier three-PR report](../ghost-prs-2026-10-31/README.md) remains as the historical record of the first batch.
