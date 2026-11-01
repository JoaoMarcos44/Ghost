# Native image generation record

Generated 2026-11-01 with the built-in image generation tool. The Python helper was executed directly (no uv). Final selected image: `infographic.png`.

## Initial prompt

Create a polished landscape infographic for a GitHub pull request. Explain the architecture, problem, and corrected behavior in simple conceptual language. Use three clearly connected areas: Flow, Problem, Fix. Keep text brief and legible. Title: PR 32433 - Protect settings edits during Save. Summary: Flow: user edits A, saves A, then types B while A is pending. Problem: the older response can close the editor and overwrite B. Fix direction: track form versions and preserve unsaved edits. Review focus: every caller must honor false and every dirty editor must resist stale context refresh.. Theme: Engineering blueprint. Dark navy drafting paper, cyan and white linework, amber for pending edits. Precise timeline and layered form-state cards; clean technical typography. Use English captions for upstream reviewers. Do not invent benchmark numbers, test counts, or claims of complete validation. No credentials, brand logos, signatures, or watermarks. Documentation context: Audit at exact source 2a62cbb7447c2c52e6b2be4029803f6ee64002d9. Navigation integration requires review. Show intended behavior and remaining checks separately. No approval badge or invented test result.. Design a high-quality wide 16:9 editorial infographic with exceptionally readable English labels and generous whitespace. Use numbered Flow / Problem / Fix sections and a clearly distinct small REVIEW FOCUS strip at the bottom. Do not print long commit hashes or test counts. The visual describes design intent, not merge approval.

## Technical correction after visual inspection

Correct one architectural misstatement while preserving the infographic. In the Fix column under Track form versions, replace 'Each edit layer has a version. Responses include the version they were saved from.' with EXACTLY 'The browser tracks each edit version. At save start, it remembers which version is being saved.' Also change 'If a response version is older than the current form version' to 'If the saved form version is older than the current edit version'. The server does NOT return a version token: this is local client bookkeeping. Keep the visual timeline, color scheme and review-focus strip. Fix stray phrase 'If a save or refacth indicates' to 'If a save returns false,'. Keep intended-behavior notice.

The selected output was visually inspected. The small HTML page is illustrative; the linked audit and runnable evidence define exact behavior. These images are explanatory diagrams, not evidence of complete validation.

