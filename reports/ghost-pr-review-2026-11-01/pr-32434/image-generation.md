# Native image generation record

Generated 2026-11-01 with the built-in image generation tool. The Python helper was executed directly (no uv). Final selected image: `infographic.png`.

## Initial prompt

Create a polished landscape infographic for a GitHub pull request. Explain the architecture, problem, and corrected behavior in simple conceptual language. Use three clearly connected areas: Flow, Problem, Fix. Keep text brief and legible. Title: PR 32434 - Remove labels from one stable selection. Summary: Flow: Admin filter selects members, API takes one snapshot of matching IDs, one transaction removes selected labels. Problem: sequential filtering loses members after the first label removal. Fix: remove A and B from the same selected members. Review focus: capability-gated rollout, response validation and real database rollback.. Theme: Paper-cut workshop. Warm ivory, terracotta, moss green and muted mustard. Tactile paper-cut member cards and detachable label tabs, with a single clearly bounded batch tray. Use English captions for upstream reviewers. Do not invent benchmark numbers, test counts, or claims of complete validation. No credentials, brand logos, signatures, or watermarks. Documentation context: Audit at exact source 779635571ba48999068a61ae56ec1ae98678509e. Original Core unit and SQLite validation do not establish MySQL HTTP or browser acceptance. Show compatibility gate and all-or-nothing transaction without an approval badge.. Design a high-quality wide 16:9 editorial infographic with exceptionally readable English labels and generous whitespace. Use numbered Flow / Problem / Fix sections and a clearly distinct small REVIEW FOCUS strip at the bottom. Do not print long commit hashes or test counts. The visual describes design intent, not merge approval.

## Technical correction after visual inspection

Correct the Problem panel's causal explanation. Replace 'Then filter for label B finds fewer members because some no longer match.' with EXACTLY 'To remove B, reuse the original filter for A. Members that lost A no longer match, so B stays behind.' Add a small A-filter icon to the second request if needed. The selection filter is NOT changed to B; the SAME filter is reused. Keep the beautiful paper-cut style, layout and other panels. Remove the long commit hash footer, replace with 'Review scope: browser and MySQL HTTP validation remain open.' Avoid spelling errors.

The selected output was visually inspected. The small HTML page is illustrative; the linked audit and runnable evidence define exact behavior. These images are explanatory diagrams, not evidence of complete validation.

