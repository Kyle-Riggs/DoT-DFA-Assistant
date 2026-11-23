# DoT-DFA-Assistant

**Driver Qualification File Audit Assistant** — a bounded document-intelligence prototype that reads a small motor carrier's existing, untagged driver qualification folders and produces a per-driver gap report. Every finding cites the regulation (49 CFR Part 391) and points to its source page, and a compliance manager reviews everything before it is exported.

> **Status: under construction.** This README is a stub and will be filled in as the prototype is built.

## Boundaries

- Produces a **reviewable work product**, not a qualification determination.
- Every finding is **traceable to a source** document and page.
- Extracted information stays **candidate** until a person validates it.
- Runs **locally**; nothing is transmitted to an external party and source files are never modified.
- **Synthetic data only.** Do not add real driver records to this repository.

## Contents (planned)

- Purpose and problem scenario
- Architecture summary
- Prerequisites and setup
- Configuration
- Running the prototype (including replay mode for machines without a local model)
- Testing and evaluation
- Sample (synthetic) data
- Known limitations
- AI assistance and validation record

## License

[MIT](LICENSE)
