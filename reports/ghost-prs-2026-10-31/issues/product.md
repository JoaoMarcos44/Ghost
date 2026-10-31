## Issue Summary

If a product-card description contains a link, HTML import uses that first link as the product button. The original button's label and destination are replaced. A description link can also create a button when the original card did not have one.

Suggested priority: **P2**, for incorrect product-card content after HTML conversion.

## Steps to Reproduce

1. Render a product card with description `<p>Read <a href="/guide">the guide</a></p>`.
2. Set its button to **Buy**, with destination `/buy`.
3. Convert the rendered HTML using `htmlToLexical` and render the imported node.
4. Repeat with the same linked description and no product button.

**Expected:** the first case retains Buy → /buy; the second remains without a button. The description link stays in the description.

**Actual:** the first case changes the button to the guide → /guide. The second creates that button despite there being none originally. The description link itself is preserved.

Controls with no link in the description preserve the original button and the absence of a button.

## Cause and scope

[The product parser selects the first anchor in the card](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/koenig/kg-default-nodes/src/nodes/product/product-parser.ts#L52). [The renderer places the description before the actual button](https://github.com/TryGhost/Ghost/blob/5d4430c8c157990adbd69400f4cee9795037fbbb/koenig/kg-default-nodes/src/nodes/product/product-renderer.ts#L105), so an anchor in that description wins.

The affected path is HTML conversion, including the inspected `source=html` input and HTML-without-Lexical import paths. Native JSON import with existing Lexical and the internal Lexical clipboard are not claimed to be affected.

## Validation

Node 22.23.4. Exact parsers/renderers/converter source from commit `5d4430c8c157990adbd69400f4cee9795037fbbb` was executed with installed node classes (`@tryghost/kg-default-nodes 2.2.6`) wired to those parsers. Rendered output was converted and rendered again.

The diagnostic exited **0** after asserting both wrong-button cases and both controls. This is a converter-level test, not a full installation, HTTP test or database import. Related #30526 adds image alt text and does not change how the parser selects the button.

## Ghost Version

Source `6.74.0-rc.0`, commit `5d4430c8c157990adbd69400f4cee9795037fbbb`.

## Node.js Version

22.23.4.

## How did you install Ghost?

Isolated source-function roundtrip on Windows with installed node dependencies.

## Database type

Not involved.

## Browser & OS version

DOM conversion in Node, not browser E2E.

## Code of Conduct

- [x] I agree to be friendly and polite to people in this repository.

