STATUS: canonical
SOURCE_OF_TRUTH: docs/core/CODEX_DEVELOPMENT_RULES.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# Codex Development Rules

## Documentation Governance

1. Documentation must reflect the current codebase.

2. New architectural concepts must first appear in `docs/core/ROADMAP_MASTER.md` before being documented as implemented models.

3. Every document must expose two metadata fields:

- `status: implemented | experimental | planned`
- `doc_type: canonical | derived | temporary`

4. If a document describes a planned model, it must explicitly reference the planned module.

Example:

- `status: planned`
- `doc_type: derived`
- `module: analysis/rf_probability_field.py`

5. CODEX must not commit documentation that describes implemented functionality unless corresponding modules exist.

