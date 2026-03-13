# Architecture Guardrails

This document defines the architectural invariants of the project.

These guardrails must be respected by:

- developers
- automated refactoring tools
- AI coding agents

This file complements the architecture documents referenced in `docs/core/DOC_MAP.md`.
It does not replace them. Its role is to define the rules that protect the architecture over time.

# Relationship to Existing Documentation

Architecture description is provided by:

- `docs/core/ARCHITECTURE_OVERVIEW.md`
- `docs/core/SYSTEM_ARCHITECTURE.md`
- `docs/core/RF_ARCHITECTURE.md`
- `docs/RF_ANALYSIS_ARCHITECTURE.md`

Data contracts are defined in:

- `docs/core/RF_DATASET_SCHEMA.md`
- `docs/core/DATA_CONTRACT.md`

This document defines the architectural rules and invariants that govern how those documents must be applied in code.

# Canonical Domain Model

The RF analysis kernel is defined by the following canonical model entities:

- `RFObservationVector`
- `RFAnalysisDataset`
- `RFAnalysisResults`
- `NetworkGraph`

These objects form the stable interface between analysis, engine orchestration, storage, and UI-facing consumers.

They are the core domain contracts of the system and must remain coherent across refactors.

# Canonical RF Analysis Pipeline

The conceptual RF pipeline is:

Packets
? Normalization
? Observations
? RF Dataset
? RF Metrics
? Network Metrics
? Network Graph
? Intelligence / Diagnostics

This is the canonical analytical flow of the project.

Detailed module-level behavior is described in `docs/RF_ANALYSIS_ARCHITECTURE.md`.

# Layering Rules

The project uses a layered architecture with explicit responsibilities.

`models/`

- contains canonical data contracts
- must remain as stable domain-facing structures

`analysis/`

- contains domain algorithms
- owns RF logic, metric computation, graph logic, normalization, and intelligence logic

`engine/`

- orchestrates pipelines
- assembles datasets
- coordinates analysis modules
- must not become a second analysis layer

`services/`

- provides access/adaptation boundaries
- may coordinate input/output flows around the engine

`storage/`

- contains persistence logic
- must not implement analytical logic

`apps/ui/`

- contains visualization and UI runtime code
- must consume results, not re-implement analysis


# Import Direction Rules

Allowed dependency direction:

models
?
analysis
?
engine
?
services
?
apps/ui

Allowed examples:

- nalysis -> models
- ngine -> nalysis
- services -> ngine
- pps/ui -> services

Forbidden reverse dependencies must not be introduced.

These rules exist to prevent circular imports and architectural drift.
# Forbidden Dependencies

The following dependencies are forbidden.

`analysis/` MUST NOT import:

- `engine`
- `services`
- `apps/ui`

`engine/` MUST NOT implement RF algorithms, propagation logic, graph metrics, or diagnostic formulas.

`models/` must remain dependency-light domain contracts and must not depend on UI or engine orchestration.

`apps/ui/` must not become an analysis layer and must not recompute RF or network intelligence logic.

`storage/` must not implement domain analytics.

# Architectural Stability Rules

The following elements are considered architecturally stable:

- canonical RF dataset schema
- `NetworkGraph` structure
- RF pipeline stage model`r`n- RF analysis pipeline stage semantics
- core domain model contracts
- canonical layering boundaries

Changes to these stable elements require an explicit architecture decision and corresponding documentation update.

The RF analysis pipeline stages are considered stable interfaces. Stage semantics must remain backward compatible.

# Usage With AI Coding Agents

AI coding agents working on this repository must respect the guardrails defined in this document.

Refactors that violate:

- canonical layering
- canonical domain contracts
- forbidden dependency rules
- stable RF pipeline structure

must be rejected or revised before integration.

This document is intended to be used as a governance layer for automated and human-driven code changes.

