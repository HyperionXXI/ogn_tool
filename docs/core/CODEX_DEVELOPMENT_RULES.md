STATUS: canonical
SOURCE_OF_TRUTH: docs/CODEX_DEVELOPMENT_RULES.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Codex Development Rules

## Documentation Governance

1. Documentation must reflect the current codebase.

2. New architectural concepts must first appear in `ROADMAP_MASTER.md`
   before being documented as implemented models.

3. All model documents must contain one of three status labels:

   STATUS: implemented
   STATUS: experimental
   STATUS: planned

4. If a document describes a planned model, it must explicitly reference
   the planned module.

   Example:

   STATUS: planned
   Module: analysis/rf_probability_field.py

5. CODEX must not commit documentation that describes implemented
   functionality unless corresponding modules exist.
