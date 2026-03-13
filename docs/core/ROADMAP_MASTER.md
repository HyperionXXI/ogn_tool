STATUS: planning
REFERENCE: docs/architecture/ADR-001-project-vision.md

# Roadmap Master

This document is a planning roadmap, not the primary source of truth for
architecture contracts.

Use this file for:
- product direction
- implementation phases
- milestone sequencing
- future feature planning

Do not use this file as the canonical source for:
- runtime contracts
- architectural layer rules
- repository classification
- reporting contracts

Canonical architecture sources are now:
- `docs/architecture/ADR-001-project-vision.md`
- `docs/architecture/REPOSITORY_CLASSIFICATION.md`
- `docs/architecture/ENGINE_RULES.md`
- `docs/architecture/RF_METRIC_CONTRACT.md`
- `docs/architecture/RUNTIME_API_MIGRATION.md`
- `docs/architecture/NETWORK_ENGINEERING_REPORT.md`

## Current role

This roadmap records the broad product and engineering direction of the
project.

It should be used to answer:
- what major capabilities exist or are planned?
- what milestone comes next?
- what long-range themes organize the work?

It should not be used to resolve low-level architecture conflicts.

## Current trajectory

Recent milestones:
- `v0.4-network-intelligence`
- `v0.5-network-diagnostics`
- `v0.6-network-engineering`
- `v0.7-spof-detection`
- `v0.8-coverage-gap-analysis`
- `v0.9-station-addition-simulation`
- `v1.0-network-reporting-foundation`

## High-level roadmap themes

- typed analytical kernel
- network intelligence
- operator diagnostics
- reporting and product surface
- future mobility and planning extensions

## Guardrail

If this roadmap diverges from code reality, update the roadmap.
If architecture rules diverge, update the canonical documents in
`docs/architecture/` first.
