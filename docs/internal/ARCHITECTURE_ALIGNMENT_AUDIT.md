STATUS: derived
REFERENCE: docs/core/RF_ARCHITECTURE.md, docs/core/RF_DATASET_SCHEMA.md, docs/core/DATA_CONTRACT.md, docs/core/RF_MIGRATION_PLAN.md

# Architecture Alignment Audit

Scope:
- Code audit only (no runtime refactor).
- Alignment check versus architecture and data-contract documentation.

Audited code:
- `src/ogn_tool/engine/rf_dataset.py`
- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/analysis/aprs_adapter.py`
- `src/ogn_tool/analysis/observation_pipeline.py`
- `src/ogn_tool/engine/observation_builder.py`
- `apps/dashboard.py`
- `apps/ui/pages/*`

## 1. Engine Container Integration

### Findings

1. `RFAnalysisDataset` exists but is not integrated into engine runtime paths.
- Present in `src/ogn_tool/engine/rf_dataset.py`.
- No imports/usages found in `rf_engine.py`, dashboard, or UI pages.

2. Dataset dictionaries are still produced directly by engine.
- `build_analysis_dataset()` returns `dataset = {...}` dictionary.
- Key construction observed in `rf_engine.py` around `dataset = { ... }`.

3. `run()` still returns `RFAnalysisResult`, not `RFAnalysisDataset`.
- `run()` output is `RFAnalysisResult(packets, distance_df, azimuth_df, coverage_grid, terrain_mask, metrics)`.

4. Compatibility path exists only as utility.
- `RFAnalysisDataset.from_dataset_dict(...)` provides conversion from dict.
- No call sites currently use it.

### Alignment status
- **Partial**: container defined, not wired.

## 2. Normalization Boundary Verification

### Documented target
From `RF_ARCHITECTURE.md`: normalization should be centralized before engine analysis.

### Current implementation

- `aprs_adapter.py`
  - Maps packet row -> `RFEvent` (`timestamp`, `emitter_id`, `receiver_id`, `lat`, `lon`).
  - Minimal mapping only.

- `observation_pipeline.py`
  - Orchestrates `packet_row_to_rfevent` + `ObservationBuilder.build`.
  - Produces `RFObservation` list.

- `observation_builder.py`
  - Minimal transformation `RFEvent -> RFObservation(event=event)`.
  - No enrichment or canonical RF field completion.

### Gaps and duplication

1. Canonical reception mapping is incomplete at boundary.
- Missing canonical handling for: `altitude`, `snr`, `freq_offset`, `bit_errors`.

2. Normalization logic leaks into `rf_engine.py`.
- Engine does additional harmonization (`receiver -> igate`, lat/lon/ts normalization, altitude coercion, RF metric fallbacks).

3. No explicit `rf_receptions_canonical` dataset emitted by normalization layer.
- Engine uses packet-like frames and aliases instead.

### Alignment status
- **Not aligned** with strict boundary target.

## 3. UI Dependency Boundary Audit

Classification legend:
- **SAFE**: consumes stable engine dataset outputs.
- **MIGRATE**: consumes packet/raw compatibility datasets that should move to engine outputs.
- **ARCHITECTURE_VIOLATION**: executes orchestration/analysis in UI layer or bypasses intended boundaries.

### Dashboard

| file | finding | classification |
| --- | --- | --- |
| `apps/dashboard.py` | Direct repository loading + direct `RFAnalysisEngine` orchestration in UI layer | ARCHITECTURE_VIOLATION |
| `apps/dashboard.py` | Publishes `packets_window` and `rf_packets` to `ui_ctx` for direct page consumption | MIGRATE |

### UI pages

| page | finding | classification |
| --- | --- | --- |
| `station_intelligence.py` | Instantiates `RFAnalysisEngine` inside page; also uses `rf_packets` directly | ARCHITECTURE_VIOLATION |
| `network_intelligence.py` | Uses `rf_packets`/`packets_window` and computes redundancy in page | ARCHITECTURE_VIOLATION |
| `coverage_explorer.py` | Uses `packets_window` and `rf_packets` directly | MIGRATE |
| `aircraft.py` | Uses `packets_window` and `rf_packets` directly | MIGRATE |
| `diagnostics.py` | Uses `packets_window` and `rf_packets` directly | MIGRATE |
| `rf_map.py` | Uses `rf_packets` directly (plus dataset grid) | MIGRATE |
| `propagation.py` | Uses `rf_packets` gate + dataset fragments | MIGRATE |
| `overview.py` | Uses `rf_packets` for counts/metrics | MIGRATE |
| `directional_rf.py` | Reads dataset outputs but still guards on `ctx.get("rf_packets")` | MIGRATE |
| `network.py` | Uses `network_packets` (packet-level) for top IGates | MIGRATE |
| `terrain.py` | Uses `dataset.shadow_map` / dataset metrics only | SAFE |
| `debug.py` | Dataset-focused debug view | SAFE |
| `coverage.py` | Minimal, no active packet-level processing | SAFE |

### Boundary status summary
- SAFE: 3 pages
- MIGRATE: 7 pages
- ARCHITECTURE_VIOLATION: 3 files (dashboard + 2 pages)

## 4. Dataset Schema Alignment (`rf_engine.py` vs docs)

### Confirmed aligned points

- Core keys present in engine dataset:
  - `rf_receptions`
  - `station_metrics`
  - `coverage_grid`
  - `network_metrics`
  - `station_overlap_matrix`
  - `rf_diagnosis`

- Experimental keys documented and present:
  - `coverage_redundancy_grid`
  - `azimuth_histogram`
  - `directional_balance`
  - `shadow_map`
  - `blind_cells`

### Mismatches

1. Canonical naming not enforced in runtime dataset.
- `rf_receptions` still uses packet-oriented aliases (`src`, `igate`, `ts_epoch`) instead of canonical (`aircraft_id`, `station_id`, `timestamp`).

2. Canonical free-flight datasets are implicit, not explicit.
- `aircraft_tracks` not explicitly emitted as a dataset key.
- `network_overlap` exists as `station_overlap_matrix` alias only.

3. Dual coverage-grid producers.
- `build_analysis_dataset()` computes a coverage grid path.
- `run()` also produces a coverage grid via `_run_rf_models()`.
- Potential schema divergence risk.

4. Stability labels are documentation-only.
- Code has no explicit schema version/stability tags.

5. Typed container not integrated.
- `RFAnalysisDataset` contract not used by engine outputs.

### Undocumented/compatibility-heavy keys still in dataset dict

- `packets_all`
- `packets_rf`
- `packets_filtered`
- `observations`
- `stations`
- `dataset_mode`

(These are now documented, but remain compatibility-heavy and partly internal.)

## 5. Recommended Fixes by Migration Phase (PR1–PR4)

### PR1 — RF normalization layer

Priority fixes:
- Centralize field mapping in normalization boundary (`observation_pipeline` + adapter).
- Emit canonical reception frame with target names:
  - `station_id`, `aircraft_id`, `timestamp`, `lat`, `lon`, `altitude`, `snr`, `freq_offset`, `bit_errors`.
- Reduce normalization logic inside engine.

Expected impact:
- Lower alias drift and simpler engine input assumptions.

### PR2 — Engine contract stabilization

Priority fixes:
- Make engine consume canonical receptions only.
- Wire `RFAnalysisDataset` as first-class engine output container (or provide deterministic dual output).
- Keep dict compatibility adapter for transition period.
- Define one authoritative coverage-grid generation path.

Expected impact:
- Stable schema for UI/API integration.

### PR3 — UI dataset cleanup

Priority fixes:
- Remove page-level engine instantiation (`station_intelligence.py`).
- Remove page-level network computation (`network_intelligence.py`) from raw packet frames.
- Migrate page dependencies from `packets_window`/`rf_packets` to stable dataset outputs.

Expected impact:
- UI boundary compliance and lower coupling to ingestion details.

### PR4 — Remove packets fallback

Priority fixes:
- Remove silent fallback in `receptions_repository` when `rf_receptions` table is missing.
- Replace with explicit compatibility mode or controlled failure policy.

Expected impact:
- Enforced reception-based architecture; fewer hidden data-mode changes.

## 6. Overall Alignment Verdict

Current alignment with architecture docs:
- **Partially aligned**.

What is aligned:
- Documentation now defines architecture, schema, and migration targets.
- Engine already exposes most required dataset families.

What is not aligned yet:
- Typed dataset container is not integrated.
- Normalization boundary is not canonical/complete.
- UI still depends on packet-level datasets and performs orchestration/analysis in pages.
- Fallback path still weakens canonical RF guarantees.