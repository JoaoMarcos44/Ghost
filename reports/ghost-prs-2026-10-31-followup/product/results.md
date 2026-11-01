# Product card HTML import — results

Worktree: `C:\Users\Nitro\Ghost\.worktrees\fix-product-card-button-import-20261031`, base `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b`. Source commit: `cd9dcd627bfdb151a376fcc2a6eaaf1bc085ecdb`.

The product parser now selects the anchor marked `kg-product-card-button`. Both the current web renderer and the legacy web renderer emit this class. The change leaves links in product descriptions as description content and preserves whether a real button is present. Custom product-card markup that omits this class on its button will no longer import that anchor as a button. The patch changeset targets `@tryghost/kg-default-nodes`.

## Validation

- **RED, before the parser change:** `product.test.ts` produced the two expected assertion failures: the description link text `the guide` replaced `Buy`, and the description link enabled a missing button. `html-to-lexical.test.ts` reproduced both failures in render → HTML import tests; both controls with plain descriptions passed. Each Vitest process exited 1, and the RED wrapper exited 0 after recognizing the expected failures.
- **GREEN, after the parser change:** `product.test.ts` passed **30/30** and `html-to-lexical.test.ts` passed **39/39**, each with exit 0. The latter verifies re-rendering after import, including the description HTML and button destination.
- **Targeted ESLint:** the parser and product node test passed together, and the converter test passed separately, each with exit 0. An initial lint attempt did not start because the Windows ESLint shim's relative path resolved incorrectly from the sandbox; calling the workspace ESLint entry via Node resolved it. The first attempt exited 1; no source change was needed.
- `git diff --check` passed with exit 0. Full repository suites, browser E2E, type checks and builds were not run.

The Vitest commands used `pnpm exec vitest run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism` with the relevant test file. The RED phase added a test-name filter and verbose reporter. The lint commands used `pnpm exec node <sandbox>/node_modules/eslint/bin/eslint.js --no-cache` with the changed TypeScript files. Node was 22.23.4 and Vitest was 4.1.12; `NODE_OPTIONS` limited the heap to 4096 MB, source export aliases and `pnpm_config_verify_deps_before_run=false` were set, and Git's Windows binaries were added to `PATH`.

All four sandboxes reported `SANDBOX_REMOVED=True`; subprocesses completed. The exact sandbox setup and commands are recorded in [reproduce.md](reproduce.md). The two test files are covered without claiming a full Koenig or repository validation.

## Commit verification

The unmodified commit hooks passed formatting, both package ESLint checks, staged-file inspection and release-intent validation. The final formatted change was pushed to the contributor fork. The [repository-wide check](../validation/results.md) timed out in formatting after 180 seconds (exit 124), before lint and the full test stage.
