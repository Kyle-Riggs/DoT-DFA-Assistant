# Contributing

Thanks for your interest in DoT-DFA-Assistant. This is a course prototype, but it is maintained like a real project.

## Ground rules

- **Synthetic data only.** Never commit real driver records, personal data, credentials, or keys.
- **Small, focused commits** with messages in the form `type: summary` (`feat`, `fix`, `test`, `docs`, `chore`, `refactor`).
- **Tests accompany behavior.** New behavior needs a test; a bug fix needs a test that failed first.
- **Respect the boundaries.** The system produces a reviewable work product, keeps every finding traceable to a source, and holds extracted values as candidates until a person validates them. Changes must not weaken these.
- **Rule evaluation stays deterministic.** Models may propose document types and dates; they never decide whether a requirement is satisfied.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Pull requests

Describe what changed and why, link the requirement IDs (FR-/NFR-) affected, and note any deviation from the documented design.
