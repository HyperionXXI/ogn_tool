# Consumer Surface Governance

Status: ACTIVE
Date: 2026-03-15

## Purpose

This document defines which project surfaces are authoritative, which
consumers may read them, and how they may evolve.

Its purpose is to prevent drift between:

- `results.*`
- analysis artifacts
- reporting views
- `report.json`
- runtime snapshots

Without this governance, the same analytical meaning can silently diverge
across CLI, UI, notebooks, exported reports, and ad-hoc scripts.

## Core Principle

External consumers MUST read stable reporting projections.

They MUST NOT derive their own semantics from raw analysis artifacts or
runtime snapshots.

Canonical flow:

`analysis/results -> reporting views -> consumer artifacts -> consumers`

## Surface Taxonomy

### 1. Runtime Results

Authoritative analytical runtime surfaces exposed by the engine.

Examples:

- `results.network_metrics`
- future typed runtime surfaces under `results.*`

Properties:

- typed analytical truth
- canonical runtime source for reporting
- may be rich or nested
- not intended as the direct long-term UI contract

Authorized consumers:

- reporting layer
- internal orchestration
- architecture-level tests

Not authorized as the default source for:

- UI widgets
- deck.gl layers
- notebooks intended as stable consumers
- exported report artifacts

### 2. Analysis Artifacts

Outputs produced directly from analysis modules or exploratory exports.

Examples:

- `azimuth_histogram.json`
- `directional_balance.json`
- `shadow_risk_scores.json`
- dense matrices or exploratory diagnostic payloads

Properties:

- close to raw analytical computation
- may be large
- structure is not guaranteed stable for external consumers
- useful for debugging, validation, and scientific inspection

Authorized consumers:

- validation scripts
- exploratory diagnostics
- internal debugging
- tests that verify analytical behavior

Not authorized for direct long-term consumption by:

- production UI
- deck.gl UI layers
- API contracts
- stable notebook interfaces

### 3. Reporting Views

Stable consumer-facing projections built from runtime analytical surfaces.

Implemented in:

- `src/ogn_tool/reporting/`

Examples:

- `report_views`
- `run_comparison_views`
- `run_evolution_views`
- `directional_views`
- future `directional_spatial_views`

Properties:

- stable consumer contract
- deterministic
- documented
- testable in isolation
- small enough to support CLI/UI/API usage

Authorized consumers:

- CLI
- UI
- deck.gl
- API
- stable notebooks
- export builders

Rules:

- reporting views MUST NOT recompute RF or network metrics
- reporting views MUST derive from runtime analytical surfaces
- reporting views MUST be deterministic for identical inputs
- reusable interpretation logic MUST live here, not in scripts or UI

### 4. `report.json`

Stable exported run summary.

Defined by:

- reporting export modules

Properties:

- compact
- versioned
- portable
- intended for archival, exchange, and run comparison

Rules:

- `report.json` MUST be derived from official reporting views
- `report.json` MUST NOT invent a second interpretation layer
- `report.json` MUST remain small; heavy payloads must stay outside it

Authorized consumers:

- export readers
- archival workflows
- run comparison tooling
- lightweight external integrations

### 5. Runtime Snapshots / Analysis Snapshots

Full or partial captures of runtime execution state.

Purpose:

- reproducibility
- debugging
- migration validation
- kernel inspection

Properties:

- internal diagnostic surface
- may expose low-level structure
- not a stable consumer API

Not authorized for direct use by:

- UI
- deck.gl
- public API layers
- stable downstream tooling

## Consumer Rules

### Rule 1

External consumers MUST consume reporting views or artifacts derived from
reporting views.

### Rule 2

Analysis artifacts MAY change structure when analytical needs evolve.

They are not a stable public contract.

### Rule 3

`report.json` MUST be derived only from official reporting projections.

### Rule 4

Runtime snapshots MUST NOT be used as a UI or API contract.

### Rule 5

Interpretation logic MUST NOT be duplicated across:

- scripts
- UI
- export builders
- notebook helpers

If the interpretation is reusable, it belongs in `src/ogn_tool/reporting/`.

### Rule 6

Reporting views MUST be deterministic.

For the same analytical inputs, they must return the same output.

### Rule 7

Heavy payloads MUST live under artifact-oriented outputs, not inside
`report.json`.

This includes large matrices, dense point clouds, and exploratory
spatial payloads.

## Builder Rule

Export builders are consumers of reporting views.

They may:

- assemble
- serialize
- version
- persist

They must NOT:

- redefine metric meaning
- add ad-hoc interpretation logic
- bypass reporting views to read analytical internals directly when an
  official view exists

## Scripts Rule

Scripts are wrappers and adapters.

They may:

- load files
- call reporting views
- persist outputs
- format terminal output

They must NOT become the canonical home of reusable interpretation
logic.

If logic is worth reusing across multiple consumers, it must move into
`src/ogn_tool/reporting/`.

## Spatial Consumer Rule

Spatial consumers such as deck.gl must consume stable spatial reporting
views, not raw analytical artifacts.

Example pattern:

- analysis artifact: `azimuth_histogram.json`
- reporting spatial view: `directional_sectors.json`
- consumer: deck.gl polar or sector layer

This keeps visualization logic decoupled from analytical internals.

## Recommended Consumer Mapping

- CLI -> reporting views
- dashboard UI -> reporting views
- deck.gl -> reporting spatial views
- run export -> `report.json` derived from reporting views
- exploratory notebooks -> reporting views by default, analysis
  artifacts only when doing research/debug work

## Evolution Rule

When adding a new analytical capability, the expected sequence is:

1. implement analytical truth in runtime/analysis surfaces
2. expose a stable reporting view
3. test the reporting view contract
4. optionally export a compact artifact
5. let consumers read that stable view or artifact

Consumer-first development that bypasses these steps is forbidden.

## Immediate Consequence For Current Work

For directional RF diagnostics:

- raw directional outputs remain analysis artifacts
- `directional_views.py` defines the stable human-oriented projection
- future map/deck.gl layers must consume a stable spatial reporting view
  rather than raw directional artifacts

This preserves protocol-agnostic growth toward a distributed RF network
intelligence platform.
