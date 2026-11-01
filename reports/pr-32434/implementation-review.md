# Implementation simplicity review

The first review retained source `1cdac3b534035e02d995160c0b37d330e47b5ea5`. A second review found a small, behavior-preserving simplification in the new bulk-removal path, committed as [`fcb5149b11d4b94433fbb682a37be7d116ef5c33`](https://github.com/JoaoMarcos44/Ghost/commit/fcb5149b11d4b94433fbb682a37be7d116ef5c33).

The member query now uses `.distinct().pluck('members.id')` instead of selecting row objects and explicitly mapping each row to its ID. This expresses the required result directly through Knex. Two query mocks were adjusted to match the call chain; the legacy action is unchanged. This is a readability improvement, not a measured performance gain.

Label IDs are already deduplicated and divided into chunks once, before the member-chunk loop. Each relation lookup remains bounded, and all requested removals use the existing transaction. Moving the loops into a new abstraction would hide these important boundaries without eliminating repeated work. The response schema and older-server capability fallback were retained.

The infographic is now displayed directly between the problem explanation and validation in this PR's description. Its image and documentation remain dedicated to this PR.

## Verification

During the first review, no product tests were rerun. An attempted validation wrapper stopped at Python argument parsing before creating a sandbox or starting tests; it was not retried.

For the second review's changed source, the Core repository suite passed all 71 tests. ESLint, formatting and `git diff --check` passed. An isolated comparison produced identical SQL and bindings before and after the change using both SQLite and MySQL query compilers. Real SQLite queries returned the same IDs for duplicate-producing joins, empty selection and rows visible within the transaction. The existing repository probe passed again, including rollback of 102 relations after a later delete failed. All temporary sandboxes and their processes were cleaned.

The framework was unchanged and its earlier 43-test result was not repeated. The MySQL comparison checked SQL compilation, not a running MySQL database. The repository probe still uses a controlled SQL selection filter rather than Ghost's real NQL filter. Full commands and historical results are recorded in [evidence.md](evidence.md).

The commit hooks passed with the repository rules enabled. The commit merges without conflicts with main `36d678dadd294555a9688f29b6a5ff86077dd8b6`; this is a source-merge check, not a full test pass on the merged tree.

No production-scale benchmark, browser, HTTP or MySQL runtime validation is claimed. The current implementation still keeps selected IDs in memory for the transaction.
