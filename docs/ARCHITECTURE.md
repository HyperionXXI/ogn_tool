# OGN Tool Architecture

This document is the entry point for architecture documentation.

## Documentation Layers

- `docs/architecture/`
  Canonical architecture rules, contracts, ADRs, and migration policies.
- `docs/core/`
  Explanatory system and domain documentation.
- `docs/internal/`
  Audits, cleanup plans, and non-canonical working notes.

## Recommended Reading Order

1. `architecture/INDEX.md`
   Architecture document map and reading order.

2. `architecture/ADR-001-project-vision.md`
   Project vision and architectural direction.

3. `architecture/REPOSITORY_CLASSIFICATION.md`
   Canonical, transitional, and legacy repository structure.

4. `core/DOC_MAP.md`
   Documentation role boundaries.

5. `core/ARCHITECTURE_OVERVIEW.md`
   High-level system view.

6. `core/SYSTEM_ARCHITECTURE.md`
   Runtime and package-layer architecture.

7. `core/RF_ARCHITECTURE.md`
   RF and network analysis architecture.

8. `architecture/RF_METRIC_CONTRACT.md`
   Typed runtime metric contract.

9. `architecture/RUNTIME_API_MIGRATION.md`
   Runtime migration policy from `ctx[...]` to `results.*`.

10. `architecture/OBSERVATION_GRAPH_CONTRACT.md`
    Future network-centric observation model.

11. `architecture/NETWORK_ENGINEERING_REPORT.md`
    Reporting-layer contract.

12. `core/RF_DATASET_SCHEMA.md`
    Current dataset and result surfaces.

## Notes

- `docs/architecture/` should be treated as the primary architectural
  source of truth.
- `docs/core/` explains the system, but may lag behind architecture
  governance if not updated.
- `docs/internal/` is not canonical.
