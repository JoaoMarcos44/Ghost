## Issue Summary

A theme using `{{#get}}` with an `id:-...` filter and successive pages can skip posts. The helper fetches with a larger limit to exclude the ID locally, but keeps the original page number. The API therefore uses a larger offset than the limit returned to the template.

Suggested priority: **P2**, limited to paginated helper queries with ID exclusions.

## Steps to Reproduce

1. Create ten posts with a stable ascending publication order, named post1 through post10.
2. Query them through `{{#get "posts" filter="id:-<post10-id>" order="published_at asc" limit="3" page="1"}}`.
3. Repeat for pages 2 and 3, keeping the same filter and order.

| Page | Expected | Actual |
| --- | --- | --- |
| 1 | post1, post2, post3 | post1, post2, post3 |
| 2 | post4, post5, post6 | post5, post6, post7 |
| 3 | post7, post8, post9 | post9 |

Posts 4 and 8 never appear. The returned `total` is 10 instead of 9. With limit 2, the page count is 4 instead of 5.

**Expected:** the paginated results and metadata describe the filtered collection with the requested limit.

**Actual:** [the optimization](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/ghost/core/frontend/helpers/get.js#L211) replaces the filter with `id:-null`, increases the limit, then filters and slices locally without correcting the page offset or all metadata.

## Validation

The unmodified helper and limit module from commit `5d4430c8c157990adbd69400f4cee9795037fbbb` ran with Node 22.23.4. An independent API collaborator performed actual SELECT/COUNT queries against SQLite in memory and implemented normal limit/offset pagination. Expected results came from the same collaborator with the original query options.

The diagnostic exited **0** after asserting the discrepancies and controls. No-filter controls passed across four pages; slug-exclusion controls passed across three pages, including metadata. Excluding IDs at the first, middle and final positions was exercised.

The real API controller, HTTP server, MySQL and a full theme/browser were not run. This demonstrates the real helper's composition with the pagination contract, not a complete deployment.

Related work checked: #30809 handles SafeString filters in the optimizer, not its page offsets. #23316 concerns a missing page field.

## Ghost Version

Source `6.74.0-rc.0`, commit `5d4430c8c157990adbd69400f4cee9795037fbbb`.

## Node.js Version

22.23.4.

## How did you install Ghost?

Isolated helper execution on Windows, with a disposable SQL-backed API collaborator.

## Database type

SQLite3 for the collaborator.

## Browser & OS version

Not applicable to the helper-level reproduction.

## Code of Conduct

- [x] I agree to be friendly and polite to people in this repository.

