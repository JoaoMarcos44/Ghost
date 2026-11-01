# Native image generation record

Generated 2026-11-01 with the built-in image generation tool. The Python helper was executed directly (no uv). Final selected image: `infographic.png`.

## Initial prompt

Create a polished landscape infographic for a GitHub pull request. Explain the architecture, problem, and corrected behavior in simple conceptual language. Use three clearly connected areas: Flow, Problem, Fix. Keep text brief and legible. Title: PR 32432 - Preserve toggle rich content. Summary: Flow: HTML card to parser to Lexical to rendered page. Problem: textContent drops links, emphasis and paragraphs. Fix: preserve heading and body with innerHTML. Review focus: keep escaped text safe and distinguish format preservation from sanitization.. Theme: Editorial print. Ivory newsprint, charcoal typography and vermilion accents. Book pages and rich-text blocks move through an HTML-to-Lexical conversion, with readable paragraph and link symbols. Use English captions for upstream reviewers. Do not invent benchmark numbers, test counts, or claims of complete validation. No credentials, brand logos, signatures, or watermarks. Documentation context: Audit at exact source af654561e2f883f086fd694abede433abfffff6b. Original focused tests reported 53 passing; do not depict full CI approval. Compare base and head behavior; review limitations remain explicit.. Design a high-quality wide 16:9 editorial infographic with exceptionally readable English labels and generous whitespace. Use numbered Flow / Problem / Fix sections and a clearly distinct small REVIEW FOCUS strip at the bottom. Do not print long commit hashes or test counts. The visual describes design intent, not merge approval.

## Technical correction after visual inspection

Correct the technical text while preserving the composition, typography, palette and diagram. In Problem, change 'Heading not preserved' to 'Heading formatting lost'. In Fix, change 'Heading preserved' to 'Heading formatting preserved'. The heading text exists before the fix; only its inline rich formatting is lost. On the source page, use well-formed illustrative HTML: <p>Read <a href="/guide">the guide</a></p>. Keep all remaining layout and wording. Do not introduce approval or test claims.

The selected output was visually inspected. The small HTML page is illustrative; the linked audit and runnable evidence define exact behavior. These images are explanatory diagrams, not evidence of complete validation.

