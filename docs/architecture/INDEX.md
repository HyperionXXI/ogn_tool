# Architecture Documentation

This directory contains the canonical architecture-level documents for the
project.

Use this directory for:
- architectural decisions
- contract documents
- repository governance
- migration rules
- reporting and runtime surface definitions

Do not use this directory for:
- implementation notes tied to one refactor
- temporary audits
- developer scratch notes

## Recommended Reading Order

1. `ADR-001-project-vision.md`
   Project vision and long-term architectural direction.

2. `REPOSITORY_CLASSIFICATION.md`
   Canonical vs transitional vs legacy repository structure.

3. `ENGINE_RULES.md`
   Rules for engine builders, intelligence modules, and UI boundaries.

4. `CONSUMER_SURFACE_GOVERNANCE.md`
   Rules for authoritative surfaces, reporting projections, and consumer boundaries.

5. `SPATIAL_PROJECTION_CONTRACT.md`
   Stable contract for spatial reporting projections consumed by map-first interfaces.

6. `AZIMUTH_DISTANCE_CONTRACT.md`
   Contract for the azimuth-distance RF matrix primitive and its future projections.

7. `AZIMUTH_DISTANCE_PROJECTION_CONTRACT.md`
   Stable contract for the azimuth-distance reporting projection consumed by external consumers.

8. `RF_METRIC_CONTRACT.md`
   Runtime contract for typed network metrics.

9. `RUNTIME_API_MIGRATION.md`
   Rules for migrating from legacy `ctx[...]` usage to `results.*`.

10. `OBSERVATION_GRAPH_CONTRACT.md`
   Future canonical network-centric observation model.

11. `NETWORK_ENGINEERING_REPORT.md`
   Contract for the reporting layer built on typed results.

12. `EXECUTIVE_ARCHITECTURE_AUDIT.md`
   Current executive-level maturity, risk and effort assessment.

13. `CAPABILITY_AUDIT.md`
   Capability inventory and reconnection status.

## Status Rules

- `docs/architecture/` = canonical architectural governance
- `docs/core/` = explanatory system/domain documentation
- `docs/internal/` = working notes, audits, and non-canonical snapshots

When an architectural rule changes, update this directory first.
