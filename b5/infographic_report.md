# B5: Telephone links in site navigation

![B5 infographic](infographic.png)

## Current validation

- Focused telephone URL tests: **2 passed**. From `apps/admin/`: `pnpm exec vitest run src/settings/utils/format-url.telephone.test.ts --maxWorkers=1 --no-file-parallelism`.
- PR: [#32139](https://github.com/TryGhost/Ghost/pull/32139).
- Full `pnpm check`: attempted, exited 130 after formatting/Oxlint passed; Nx lint/build tasks failed on this Windows environment. The full test stage was not reached. See the PR and the validation archive for details. Product CI and migration staging review remain unverified.

> **Historical generation record:** The content below records the image-generation context and status at that time. Any test-status statement below is superseded by Current validation above; the generation prompt is preserved unchanged.

**Architecture:** Admin formats navigation destinations before saving them.

**Problem:** The automatic trailing-slash rule also changes telephone URIs, so `tel:+15555550100` becomes `tel:+15555550100/`.

**Proposed solution:** Apply automatic trailing slashes only to HTTP and HTTPS URLs, preserving telephone URIs and their extension parameters. The change is proposed and not merged.

**Validation shown:** Telephone URI and extension examples, plus an HTTP child-path control. The infographic describes proposed checks, not a completed test run.
