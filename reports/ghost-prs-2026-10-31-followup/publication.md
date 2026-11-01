# Resumed publication — 1 November 2026

The three source fixes are implemented and committed. All three branches now exist on `JoaoMarcos44/Ghost`. Publication to `TryGhost/Ghost` remains blocked by GitHub permissions; no new PR number is claimed.

| Change | Issue | Source commit | Comparison for draft creation |
| --- | --- | --- | --- |
| Get-helper pagination | [#32427](https://github.com/TryGhost/Ghost/issues/32427) | `c3c35ad9e01cb2db160308e8d4286d7cdb848d77` | [Open comparison](https://github.com/TryGhost/Ghost/compare/main...JoaoMarcos44:fix/get-helper-pagination-20261031?expand=1) |
| Product-card button import | [#32429](https://github.com/TryGhost/Ghost/issues/32429) | `cd9dcd627bfdb151a376fcc2a6eaaf1bc085ecdb` | [Open comparison](https://github.com/TryGhost/Ghost/compare/main...JoaoMarcos44:fix/product-card-button-import-20261031?expand=1) |
| Historical subscriber values | [#32420](https://github.com/TryGhost/Ghost/issues/32420) | `54fe601764701dbc7eb3ec8ac3ec027d28f8955e` | [Open comparison](https://github.com/TryGhost/Ghost/compare/main...JoaoMarcos44:fix/subscriber-history-anchor-20261031?expand=1) |

Use the prepared descriptions in [pagination/pr-body.md](pagination/pr-body.md), [product/pr-body.md](product/pr-body.md) and [history/pr-body.md](history/pr-body.md). The intended state is **draft**. These links do not bypass GitHub's permission checks.

## Permission evidence

Creating the pagination draft through the GitHub connector returned HTTP 403, `Resource not accessible by integration`. The authenticated GitHub CLI also failed with exit 1:

```text
GraphQL: JoaoMarcos44 does not have the correct permissions to execute CreatePullRequest (createPullRequest)
```

`gh api user --jq .login` confirmed the CLI account as `JoaoMarcos44`. The fork reports write/admin permission; upstream reports read permission. Read-only access to upstream is normal for an external contributor and alone does not explain the PR-creation refusal. No token inspection, authentication change, alternative identity or further creation attempt was used to work around the denial. The exact upstream/account restriction is not established by the returned error.

The existing drafts are [#32432](https://github.com/TryGhost/Ghost/pull/32432), [#32433](https://github.com/TryGhost/Ghost/pull/32433) and [#32434](https://github.com/TryGhost/Ghost/pull/32434). Their state was verified through the CLI. The three follow-up head branches had no matching PR in GitHub searches before creation was attempted.

## Verification and preservation

The three source commits passed `git diff HEAD^ HEAD --check`. Upstream advanced to `5fc6896a354b966789986e2ea99d352e534aa47d`; the inspected source and test files for these fixes had no changes between their base `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b` and that upstream revision. This is not a full integration or mergeability test.

Historical focused validation passed 184 tests. The [resumed test report](validation/resume-tests.md) distinguishes the new runs and their failures/retries. The [representative global check](validation/results.md) timed out during formatting. Browser, MySQL and full repository validation remain outstanding.

The existing PNGs on documentation commit `592b7186cb503946ebd298b03433d3e6f61cd243` match the local Git blob hashes:

| Asset | Blob SHA |
| --- | --- |
| Pagination | `34415051db075e6643d07adcbf6205e4f3147924` |
| Product | `f426e6fb29e462db3fe0577cbb0404a09b6f50c9` |
| History | `aa69af170df2cae756c3d2fc89f48ba7166a88ca` |

Source worktrees and evidence are retained. Old artifacts from previous sessions were not deleted. New validation sandboxes and processes are covered by the resumed test report. The separate Codex WebSocket diagnosis stays local and is excluded from the public documentation branch.
