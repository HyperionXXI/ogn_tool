# ARCHITECTURE GUARDRAILS

## Dependency Rule (Acyclic Principle)

- `analysis/` → no dependency on `pipeline/`, `engine/`, or `reporting/`
- `pipeline/` → may depend on `analysis/` only
- `engine/` → may depend on `pipeline/` and `analysis/`
- `reporting/` → may depend on `engine/`
- `apps/UI` → may depend on `reporting/`

**Never create a cycle in dependencies.**

### Why?
- Cycles cause import errors, make refactoring and testing difficult, and break modularity.
- Each layer should only depend on lower layers.

## Example (Good)
- `engine/` imports from `pipeline/` and `analysis/`
- `pipeline/` imports from `analysis/`
- `analysis/` only imports external libs (numpy, pandas, geo, etc.)

## Example (Bad)
- `analysis/` imports from `engine/` or `pipeline/`
- `pipeline/` imports from `engine/`

## How to enforce
- Review imports regularly.
- Optionally, add architecture tests to assert forbidden imports.

---

*This file documents the architectural dependency rules for maintainability and clarity. See NETWORK_ANALYTICS_ENGINE.md for canonical engine contracts.*
