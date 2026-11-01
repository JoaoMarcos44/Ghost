# PR 32432: preserve rich content in imported toggles

[Latest implementation simplicity review](implementation-review.md).

The latest review retained the renderer: replacing its compacted static fragments with one indented template introduced extra blank lines in plaintext emails in all six exploratory cases. The retained implementation's earlier 56-test pass remains applicable; those tests were not rerun during this experiment.

Fixes [TryGhost/Ghost#32428](https://github.com/TryGhost/Ghost/issues/32428).

Importing a toggle card previously read its heading and body as plain text, so links, emphasis and paragraph boundaries were lost. The parser now preserves the fields' inner HTML for supported rich content.

A review of the first implementation found a second issue in the email path. The HTML import kept the space in `<strong>Hello</strong> <em>world</em>`, but email template whitespace compaction removed it, producing **Helloworld**. The email renderer now inserts heading and body HTML outside the whitespace-compacting template tag. The same regression is covered for formatted heading and body text, including an import-to-email test.

## Scope and review boundaries

HTML is converted into a Lexical toggle and later rendered for the web or for email. The supported formatting cases were checked in the focused tests; preservation of arbitrary HTML through an editor round trip is not guaranteed. This change does not establish an HTML sanitization contract. An earlier audit observed that an active attribute survived this toggle conversion, but did not execute the attribute or establish a new exploit. See [evidence.md](evidence.md) for the observed trust and editor boundaries.

The source head reviewed here is [`4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`](https://github.com/TryGhost/Ghost/commit/4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef). The latest individual merge against main at `36d678dadd294555a9688f29b6a5ff86077dd8b6` completed without conflicts; that is a mergeability check, not a full validation of the merged tree.

## Validation

- The final source passed **56 focused behavior and conversion tests in three files**, plus the focused ESLint checks and the Core test's formatting check.
- The import-to-email regression also passed in Ghost Core's unit-project configuration with its setup and hooks. This is a repeat of one of the 56 tests, not an additional distinct case.
- Source commit hooks passed.
- An optional byte-for-byte comparison found a change in whitespace around plain email content. Visible text and inline-spacing assertions passed; the output is not byte-for-byte identical. The exact old and new HTML is in [evidence.md](evidence.md).
- A full `pnpm check`, browser E2E and actual email delivery have not been established for this PR alone. The observed product CI status was `action_required`, requiring maintainer authorization; it is not a passing result.

See the [validation evidence and reproduction outline](evidence.md) and the [visual explanation](infographic_report.md).
