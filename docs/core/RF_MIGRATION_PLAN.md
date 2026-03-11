STATUS: canonical
SOURCE_OF_TRUTH: docs/core/RF_MIGRATION_PLAN.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# RF Migration Plan

Objective:
Align implementation with `docs/core/RF_ARCHITECTURE.md` and `docs/core/DATA_CONTRACT.md` without changing behavior abruptly.

## 1. Normalization Boundary

Candidate modules inspected:

- `src/ogn_tool/analysis/aprs_adapter.py`
- `src/ogn_tool/analysis/observation_pipeline.py`
- `src/ogn_tool/engine/observation_builder.py`

### Decision

Canonical receptions (`rf_receptions_canonical`) should be produced at:

- **Primary boundary:** `src/ogn_tool/analysis/observation_pipeline.py`

### Why this boundary

- `aprs_adapter.py` already maps row-level packet fields to event semantics.
- `observation_builder.py` already maps events to `RFObservation` objects.
- `observation_pipeline.py` is the natural orchestration point where all sources are unified before engine analysis.

### Target boundary responsibilities

`observation_pipeline` should:

1. Accept packet/reception-like rows.
2. Normalize field names and units.
3. Produce a canonical tabular dataset (`rf_receptions_canonical`) and/or canonical `RFObservation` list with equivalent fields.
4. Emit validation status (missing fields, null-rate, coercions).

## 2. Engine Input Contract (strict target)

Engine target input:

- `rf_receptions_canonical` only.

Minimal required fields:

- `station_id`
- `aircraft_id`
- `timestamp`
- `lat`
- `lon`

Recommended RF fields (optional but strongly expected):

- `altitude`
- `snr`
- `freq_offset`
- `bit_errors`

Derived engine fields (computed, not required as input):

- `distance_km`
- `bearing_deg`

Current gap:

- `RFAnalysisEngine` still consumes packet-like columns (`igate`, `src`, `qas`, `raw`, `ts_utc`) and compatibility fallbacks.

## 3. UI Dependency Map

Classification rules:

- **SAFE:** reads stable engine outputs from `dataset` (metrics/grids/diagnostics).
- **MIGRATE_TO_ENGINE_OUTPUT:** reads `packets_window` or `rf_packets` directly.
- **REMOVE:** UI executes engine/analysis logic directly or keeps debug-only dependency in production path.

### Dashboard-level dependencies

| file | dependency | classification | note |
| --- | --- | --- | --- |
| `apps/dashboard.py` | repository loading (`packets_window`, `receptions_window`) + engine orchestration + raw frames in `ui_ctx` | MIGRATE_TO_ENGINE_OUTPUT | Keep temporarily; move toward service/engine contract as source of truth |
| `apps/dashboard.py` | debug prints (`st.write("packets_window...", ...)`) | REMOVE | debug-only noise |

### UI pages

| file | dependency observed | classification | target |
| --- | --- | --- | --- |
| `apps/ui/pages/overview.py` | `dataset` + `rf_packets` | MIGRATE_TO_ENGINE_OUTPUT | use only dataset metrics/observations |
| `apps/ui/pages/coverage_explorer.py` | `dataset` + `rf_packets` + `packets_window` | MIGRATE_TO_ENGINE_OUTPUT | move all counts/maps to engine outputs |
| `apps/ui/pages/propagation.py` | `dataset` + `rf_packets` gate | MIGRATE_TO_ENGINE_OUTPUT | use dataset observations only |
| `apps/ui/pages/network_intelligence.py` | `rf_packets` fallback `packets_window` | MIGRATE_TO_ENGINE_OUTPUT | consume engine/network outputs only |
| `apps/ui/pages/diagnostics.py` | direct `packets_window` + `rf_packets` stats | MIGRATE_TO_ENGINE_OUTPUT | source diagnostics from dataset + engine diagnostic outputs |
| `apps/ui/pages/aircraft.py` | mixed `dataset`, `rf_packets`, `packets_window` | MIGRATE_TO_ENGINE_OUTPUT | define aircraft view contract from engine |
| `apps/ui/pages/station_intelligence.py` | re-instantiates `RFAnalysisEngine` in page | REMOVE | page should consume precomputed `dataset`/analysis outputs only |
| `apps/ui/pages/network.py` | reads `dataset` for network outputs | SAFE | keep, tighten field contract |
| `apps/ui/pages/directional_rf.py` | reads `dataset` azimuth/metrics | SAFE | keep |
| `apps/ui/pages/terrain.py` | reads `dataset.shadow_map` | SAFE | keep |
| `apps/ui/pages/rf_map.py` | reads `dataset.coverage_grid` + `rf_packets` | MIGRATE_TO_ENGINE_OUTPUT | remove direct packet dependency when map dataset stabilized |
| `apps/ui/pages/debug.py` | debug visualization from `dataset` | SAFE (debug scope) | keep as debug-only page |

## 4. Refactor Phases (small PRs)

### PR1 – RF normalization layer

Goal:
- Introduce one canonical normalization output (`rf_receptions_canonical`).

Files impacted:

- `src/ogn_tool/analysis/aprs_adapter.py`
- `src/ogn_tool/analysis/observation_pipeline.py`
- `src/ogn_tool/engine/observation_builder.py`
- `docs/core/DATA_CONTRACT.md` (already aligned)

Expected changes:

- Centralized field mapping (`igate/receiver -> station_id`, `src -> aircraft_id`, `ts_epoch/ts_utc -> timestamp`).
- Validation/coercion rules documented and emitted.

Risk level:

- **Medium** (shape changes at analysis boundary).

### PR2 – Engine contract stabilization

Goal:
- Make engine accept canonical receptions and emit stable dataset schema.

Files impacted:

- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/engine/results.py` (if needed for explicit schema typing)
- `docs/core/RF_ARCHITECTURE.md`, `docs/core/DATA_CONTRACT.md`

Expected changes:

- Engine input no longer depends on packet transport fields.
- Engine outputs formalized (`rf_analysis_dataset`, `station_metrics`, `network_metrics`, `rf_models`).

Risk level:

- **High** (core orchestration path).

### PR3 – UI dataset cleanup

Goal:
- UI consumes engine outputs only; remove direct packet-window dependencies from pages.

Files impacted:

- `apps/dashboard.py`
- `apps/ui/sections.py`
- `apps/ui/pages/*` (priority: `station_intelligence`, `network_intelligence`, `coverage_explorer`, `diagnostics`, `aircraft`)

Expected changes:

- Drop `packets_window` / `rf_packets` direct usage in pages where equivalent engine output exists.
- Remove page-level engine instantiation.

Risk level:

- **Medium** (UI regressions if contracts are incomplete).

### PR4 – Remove packets fallback

Goal:
- Enforce reception-based RF model and explicit compatibility policy.

Files impacted:

- `src/ogn_tool/data/receptions_repository.py`
- `apps/dashboard.py` (status messaging)
- docs (`DATA_CONTRACT`, `RF_ARCHITECTURE`)

Expected changes:

- Remove silent fallback from `rf_receptions` to `packets`.
- If table missing: explicit compatibility mode or hard failure based on config.

Risk level:

- **Medium-High** (runtime behavior changes where DB schema is incomplete).

## 5. Execution Order and Guardrails

Recommended order:

1. PR1
2. PR2
3. PR3
4. PR4

Guardrails:

- Keep regression tests green at each phase.
- Add contract tests for canonical schema before PR2 merge.
- Do not merge PR4 until production datasets include `rf_receptions` reliably.