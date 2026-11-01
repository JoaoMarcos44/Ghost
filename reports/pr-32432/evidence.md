# PR 32432 validation evidence

## Revisions and behavior

The final source head is [`4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`](https://github.com/TryGhost/Ghost/commit/4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef). Its individual merge with main at `3b395b6b082bb995bc8dc8d7b648fea7732fe839` completed without conflicts. This establishes mergeability, not test coverage for the merged tree.

The earlier audit compared PR head `af654561e2f883f086fd694abede433abfffff6b` with the supplied base `80b4c5d8f8a7cb90a93caa072140c54d4cb5b69b`. For the same imported HTML, the base flattened formatting but rendered the text `Hello world` in email. At the audited head, the parser retained `<strong>Hello</strong> <em>world</em>`, but the email template's existing whitespace helper joined it to `Helloworld`; formatted heading words were also joined. The earlier audit's eight behavior scenarios passed on each revision, including assertions that deliberately recorded this defect. Those passes did not establish correct email output.

After adding the regressions but before changing the email renderer, a focused run failed three of 19 tests: expected `Heading words` but obtained `Headingwords`, expected `Hello world` but obtained `Helloworld`, and the import-to-email test likewise observed the joined heading. After the renderer correction, the same 19 tests passed.

The final focused run at `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef` passed **56 tests in three files**, with exit code 0. Focused ESLint for the changed toggle node files and the Core regression, and `oxfmt --check --threads=1` for the Core test, also passed. Source commit hooks passed.

A separate run repeated the import-to-email test with the copied Ghost Core Vitest unit project, setup and hooks, with sandbox-local source aliases and paths. It passed **1 test in 1 file**, exit code 0. This is the same regression included in the 56, not a 57th distinct test. Both focused sandboxes were reported removed after their respective runs.

### Byte-for-byte comparison

An optional comparison against the renderer at `af654561e2f883f086fd694abede433abfffff6b` failed for plain content:

- Previous: `<td class="kg-toggle-content"> Content </td>`
- Corrected: `<td class="kg-toggle-content">Content</td>`

The focused tests passed for visible text and spacing between formatted words. They do not establish byte-for-byte equality of the email HTML.

## Reproduction outline

The checks used Node 22.23.4 and Vitest 4.1.12, one worker and a 2048 MB Node heap, from a checkout of the source head with its dependencies installed. The relevant committed tests are:

- [Toggle node tests](https://github.com/TryGhost/Ghost/blob/4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef/koenig/kg-default-nodes/test/nodes/toggle.test.ts)
- [HTML-to-Lexical conversion tests](https://github.com/TryGhost/Ghost/blob/4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef/koenig/kg-html-to-lexical/test/html-to-lexical.test.ts)
- [Core import-to-email regression](https://github.com/TryGhost/Ghost/blob/4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef/ghost/test/unit/server/services/email-service/toggle-email.test.ts)

For the focused run, create a disposable sandbox, copy those tests, the toggle test utilities, and the `src` directories and manifests of `kg-default-nodes`, `kg-html-to-lexical`, `kg-default-transforms`, `kg-clean-basic-html`, `kg-markdown-html-renderer`, `kg-utils` and `kg-lexical-html-renderer`. Make the installed root and package `node_modules` available to the sandbox. Create `vitest.sandbox.config.ts` with aliases for each copied package's `source` exports, ordered longest first; use source and node resolution conditions, `globals: true`, the Node environment, and `test.server.deps.inline` matching `/^@tryghost\/kg-/`. Keep temporary and cache paths inside the sandbox. Set `NODE_OPTIONS=--max-old-space-size=2048 --conditions=source`, `NODE_ENV=testing`, `CI=true`, `UV_THREADPOOL_SIZE=1`, `RAYON_NUM_THREADS=1` and `NX_DAEMON=false`. From the sandbox root, invoke:

```text
node.exe <checkout>/node_modules/vitest/vitest.mjs run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose koenig/kg-default-nodes/test/nodes/toggle.test.ts koenig/kg-html-to-lexical/test/html-to-lexical.test.ts ghost/test/unit/server/services/email-service/toggle-email.test.ts
```

For the separate Core configuration check, use a fresh sandbox containing the same Koenig sources, tracked `ghost/core` and `ghost/test/utils`, the Core manifest, `ghost/vitest.config.ts` and the Core regression. Add the same source aliases and dependency inlining to the copied configuration, retain its unit project and hooks, and configure SSR to use source and node conditions and `noExternal: [/^@tryghost\/kg-/]`. Point its cache, content and database paths into the sandbox and use the same environment limits. From the copied `ghost/` directory, invoke:

```text
node.exe <checkout>/node_modules/vitest/vitest.mjs run --config vitest.config.ts --project unit --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose test/unit/server/services/email-service/toggle-email.test.ts
```

The sandbox configuration is an adaptation of the repository setup. Remove each disposable sandbox after its run; these focused commands are not a substitute for `pnpm check`.

## Limits

The audit observed that an `onerror` attribute survived in an imported toggle's rendered HTML; the handler was not executed. An explicit raw HTML card retained the same attribute at both compared revisions. This observation is a changed data flow, not proof of a new privilege escalation or an established sanitization policy.

A nested-editor helper test dropped an image that the imported toggle had retained. That is a helper-level observation, not a browser-tested save result or a promise that arbitrary HTML survives editing. No full `pnpm check`, browser E2E or actual email delivery has been established for this PR alone. The observed product CI status was `action_required` and needs maintainer authorization; it does not count as a passing check.
