# Implementation simplicity review

Reviewed source: `4f9fd69ae03ea64c7da1daca4aaa4840e38d28ef`. No source changes were needed.

The HTML parser already expresses the fix directly by retaining the supported rich HTML fields. The email renderer keeps user content outside template whitespace normalization. Pre-flattening the template to avoid its small static normalization calls would make the HTML harder to read without a demonstrated performance benefit. The existing local implementation was retained.

The infographic is now displayed directly between the problem explanation and validation in this PR's description. Its image and documentation remain dedicated to this PR.

## Verification

A sandbox rerun passed the 56 behavioral tests and the selected ESLint and formatting checks. The optional `--compare-baseline` byte-comparison also ran and failed on the already-recorded whitespace around plain content, so that exploratory command exited 1. The byte difference is described in [evidence.md](evidence.md); it is not a new regression found in this review. An earlier output-printing attempt failed with a CP1252 encoding error. Both sandboxes were removed, and no source or test files changed.

This review does not establish full repository, browser or actual email-delivery validation.
