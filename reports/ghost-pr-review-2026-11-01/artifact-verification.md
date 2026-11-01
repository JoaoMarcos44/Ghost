# Artifact verification and publication scope

The final bundle was checked without modifying product files. The read-only command returned exit 0 and verified 33 files: relative Markdown links, JSON parsing, Python syntax, and all three PNG signatures and dimensions. The later addition of this record is documentation only.

| PR | Image dimensions | SHA-256 |
| --- | --- | --- |
| 32432 | 1672 × 941 | `24fcab30a41bec3b80e391a38ba1d7ceeef228137f01ae657cac8326a8f291df` |
| 32433 | 1672 × 941 | `a841ef72f2560236343fa0ae392d94f32817c2c5594c16f600a2e0846e810265` |
| 32434 | 1672 × 941 | `0a2c1103ffa69bfb9b8087e0d736d2d2780fc226a276cc7408c42b00ec1c7f8e` |

The images were generated and corrected with the native image generation tool. Visual inspection corrected three substantive wording issues: heading *formatting* rather than heading text; browser-local version bookkeeping rather than server version tokens; and reuse of the original label-A filter rather than a new label-B filter.

An initial combined command that would create an artifact-validation sandbox and later remove it was rejected before execution by automatic approval review with `blocked by policy`. That command created no sandbox. The successful alternative performed only read operations and emitted its result to stdout; it did not retry deletion.

The distinct, earlier settings-test sandbox remains as recorded in [the settings validation](pr-32433/validation.md). No attempt was made to circumvent that deletion rejection.

Publication is limited to this audit bundle on a documentation branch in the contributor's fork and factual updates/links in the three existing PR descriptions. No product source commit, merge, force push or new PR is part of this audit. The initial API snapshot and status files are historical captures, not continuously refreshed state.

