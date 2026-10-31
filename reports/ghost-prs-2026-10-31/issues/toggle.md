## Issue Summary

Converting a toggle card's rendered HTML back to Lexical loses rich content. The parser reads the heading and content using `textContent`, although the editor and renderer store and render rich HTML.

Suggested priority: **P2** for content loss during HTML conversion. This report does not claim that native JSON imports already containing Lexical or the internal Lexical clipboard take this path.

## Steps to Reproduce

1. Render a toggle card whose content is:
   `<p>Read <a href="https://example.com/doc">documentation</a></p><p>Second paragraph</p>`.
2. Pass the rendered card HTML to `htmlToLexical`.
3. Inspect the toggle node's `content`, and render the imported state again.

**Expected:** the two paragraphs and link destination survive the conversion.

**Actual:** content becomes `Read documentationSecond paragraph`. The link and paragraph boundaries are gone; the second rendering has no paragraphs or link.

A plain-text toggle roundtrip remains unchanged.

## Cause and scope

[The toggle parser uses textContent](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/koenig/kg-default-nodes/src/nodes/toggle/toggle-parser.ts#L10), while [the renderer inserts rich HTML](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/koenig/kg-default-nodes/src/nodes/toggle/toggle-renderer.ts#L25).

The production converter is called by the Admin posts input path with `source=html` and by the importer when converting HTML without existing Lexical. Those entry points were inspected, not exercised through HTTP in this reproduction.

## Validation

Node 22.23.4. The parsers, renderers and `htmlToLexical` source were extracted from commit `5d4430c8c157990adbd69400f4cee9795037fbbb`. Installed node classes from `@tryghost/kg-default-nodes 2.2.6` were wired in memory to the exact extracted parsers; this is not presented as a full installation of that main revision.

The diagnostic exited **0** after asserting the loss of paragraphs/link and the plain-text control. No full HTTP/importer/database test is claimed.

Related #29597 changes toggle accessibility and markup but retains `textContent` in the parser; its closed patch does not resolve this loss.

## Ghost Version

Source `6.74.0-rc.0`, commit `5d4430c8c157990adbd69400f4cee9795037fbbb`.

## Node.js Version

22.23.4.

## How did you install Ghost?

Isolated HTML → Lexical → HTML conversion on Windows with actual source functions and installed node dependencies.

## Database type

Not involved.

## Browser & OS version

DOM conversion in Node, not a full browser E2E run.

## Code of Conduct

- [x] I agree to be friendly and polite to people in this repository.

