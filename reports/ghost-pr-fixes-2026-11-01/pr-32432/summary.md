# PR #32432: preserve spaces in toggle emails

The HTML import preserves inline formatting in a toggle, but the email template compacted the imported HTML too. For example, `<strong>Hello</strong> <em>world</em>` became `Helloworld` in email. The correction keeps heading and content HTML outside the template's whitespace-compacting tag. It changes the toggle email renderer only and leaves the shared helper and web renderer unchanged.

The [earlier audit](../../ghost-pr-review-2026-11-01/pr-32432/audit.md) describes the failure at `af654561e2f883f086fd694abede433abfffff6b`. The correction is in local commit `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`, following regression commit `c3eea6007371a914eae4e6989dd5edae859b94e9`. The change preserves supported inline content; it does not establish a sanitization contract or guarantee that arbitrary HTML survives an editor round trip.

## Validation

The focused sandbox used Node 22.23.4, Vitest 4.1.12, one worker and a 2048 MB Node heap. The following command failed on the previous renderer with three joined-word regressions and passed all 19 tests after the fix:

```text
node.exe <worktree>/node_modules/vitest/vitest.mjs run --config vitest.sandbox.config.ts --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose koenig/kg-default-nodes/test/nodes/toggle.test.ts ghost/test/unit/server/services/email-service/toggle-email.test.ts
```

After the fix commit, the expanded normal runner passed all 56 node, conversion and email behavior tests, exit 0. Focused ESLint and the Core test's formatting check also passed:

```powershell
python -X utf8 reports/ghost-pr-fixes-2026-11-01/pr-32432/run-focused.py
```

A separate optional byte-for-byte comparison with the previous renderer failed because plain content changed from `<td class="kg-toggle-content"> Content </td>` to `<td class="kg-toggle-content">Content</td>`. The visible text and inline spacing tests passed; the output is not byte-for-byte identical.

The converter-to-email regression also passed in a separate sandbox using the copied Core Vitest unit project, setup and hooks, with source aliases and sandbox paths added:

```text
node.exe <worktree>/node_modules/vitest/vitest.mjs run --config vitest.config.ts --project unit --no-coverage --pool=threads --maxWorkers=1 --no-file-parallelism --reporter=verbose test/unit/server/services/email-service/toggle-email.test.ts
```

That run passed one test. These overlapping runs are not a single combined suite. No browser test, actual email delivery or full `pnpm check` was completed as part of this focused validation. Product workflows in `action_required` need maintainer authorization; that status is not a passing test result. See [evidence.md](evidence.md) for the RED output and sandbox details.

## Final integration status

The final source commit is published in the existing PR branch. All source commit hooks passed. The three fixes merge together with main without conflicts; combined-tree global formatting and Oxlint passed, and the official framework typecheck passed after real workspace declaration builds. Full `pnpm check` stopped at the Nx Windows socket-path limit, before its later test stages. See [integrated evidence](../validation/integrated.md) for exact SHAs, environment limits and the remaining CI/Tinybird maintainer-authorization block.
