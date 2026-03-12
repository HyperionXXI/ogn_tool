STATUS: canonical
SOURCE_OF_TRUTH: docs/core/RF_ARCHITECTURE.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# RF Architecture

This document freezes the RF architecture definition before code refactors.
Scope: architecture analysis and documentation only.

## 1. Architecture Layers (5 layers)

### 1. Data ingestion
Purpose:
- Load packet and reception records from SQLite.
- Apply time-window and station filters.

Current implementation:
- `src/ogn_tool/data/packets_repository.py`
- `src/ogn_tool/data/receptions_repository.py`
- `src/ogn_tool/data/db_repository.py`

### 2. RF normalization
Purpose:
- Convert heterogeneous packet/reception rows into a stable reception-oriented contract.
- Normalize key fields (`station_id`, `aircraft_id`, `timestamp`, coordinates, RF metrics).

Current implementation state:
- Partial and distributed across:
  - `src/ogn_tool/analysis/observation_pipeline.py`
  - `src/ogn_tool/analysis/aprs_adapter.py`
  - `src/ogn_tool/engine/observation_builder.py`
  - `src/ogn_tool/engine/rf_engine.py` (column harmonization)

### 3. RF analysis engine
Purpose:
- Build the RF analysis dataset.
- Run station- and RF-model computations.
- Expose structured outputs for downstream consumers.

Current implementation:
- `src/ogn_tool/engine/rf_engine.py`
- Core output: `dataset` dict + `RFAnalysisResult` from `run()`.

### 4. Network analysis / intelligence
Purpose:
- Derive multi-station and topology-level metrics.
- Compute overlap, redundancy, blind-zone candidates, topology views.

Current implementation:
- `src/ogn_tool/analysis/network_analysis.py`
- `src/ogn_tool/network/network_intelligence.py`
- Partially orchestrated by `rf_engine`, partially called directly by UI pages.

### 5. UI observatory
Purpose:
- Render map-centric observability pages.
- Consume prepared datasets and metrics from dashboard context.

Current implementation:
- `apps/dashboard.py` (routing + context assembly)
- `apps/ui/sections.py`
- `apps/ui/pages/*`

## 2. Module Responsibilities

| module | layer | responsibility | input dataset | output dataset |
| --- | --- | --- | --- | --- |
| `src/ogn_tool/data/packets_repository.py` | Data ingestion | Query packet windows from SQLite | `packets` table | `packets_window` DataFrame |
| `src/ogn_tool/data/receptions_repository.py` | Data ingestion | Query `rf_receptions` or fallback station packets | `rf_receptions` + `packets` tables | `receptions_window` DataFrame |
| `src/ogn_tool/data/db_repository.py` | Data ingestion | DB meta/index/sanity/table checks | SQLite DB | metadata, status flags |
| `src/ogn_tool/analysis/aprs_adapter.py` | RF normalization | Map packet row -> RFEvent-like structure | packet row dict | event object |
| `src/ogn_tool/analysis/observation_pipeline.py` | RF normalization | Build observations from packet rows | packet rows + builder | RFObservation list |
| `src/ogn_tool/engine/observation_builder.py` | RF normalization | Convert events to RFObservation instances | RFEvent | RFObservation |
| `src/ogn_tool/engine/rf_engine.py` | RF analysis engine | Build analysis dataset, run station/network diagnostics and RF models | `receptions_window` (current), packet/reception-like rows | `dataset` dict (`rf_receptions`, `coverage_grid`, `station_metrics`, `network_metrics`, etc.) |
| `src/ogn_tool/analysis/*.py` (RF models) | RF analysis engine | Compute propagation, azimuth, terrain, diagnostics components | observation/grid DataFrames | model outputs (dict/DataFrame) |
| `src/ogn_tool/analysis/network_analysis.py` | Network analysis/intelligence | Overlap matrix, station profile, blind-zone detection helpers | packet/redundancy frames | network-level metrics/DataFrames |
| `src/ogn_tool/network/network_intelligence.py` | Network analysis/intelligence | topology, station roles, coverage redundancy | packet-like DataFrame (`src`,`igate`,`lat`,`lon`) | topology dict + role dict + redundancy DataFrame |
| `apps/dashboard.py` | UI observatory | Load datasets, run engine, build `ui_ctx`, route pages | repositories + engine outputs | `ui_ctx` passed to pages |
| `apps/ui/pages/*.py` | UI observatory | Render views/maps/tables | `ui_ctx` datasets (`dataset`, `rf_packets`, `packets_window`, etc.) | visual output |

## 3. Canonical Pipeline

Canonical target pipeline:

`raw_packets`
-> `rf_receptions_canonical`
-> `rf_analysis_dataset`
-> `station_metrics`
-> `network_metrics`

### Dataset production points

- `raw_packets`:
  - Produced by data ingestion (`packets_repository.load_packets_window`).
- `rf_receptions_canonical` (target):
  - Should be produced by RF normalization layer (currently partial/distributed).
  - Current operational source is `receptions_repository.load_rf_receptions` + fallback packets.
- `rf_analysis_dataset`:
  - Produced by `RFAnalysisEngine.build_analysis_dataset` in `src/ogn_tool/engine/rf_engine.py`.
- `station_metrics`:
  - Produced inside `build_analysis_dataset` and exposed via `dataset["station_metrics"]`.
- `network_metrics`:
  - Produced inside `build_analysis_dataset` and exposed via `dataset["network_metrics"]`.

## 4. Architecture Violations (current)

These are observed violations against strict layer boundaries.

1. UI reading packet-level datasets directly
- `apps/dashboard.py` exposes `packets_window` and `rf_packets` directly in `ui_ctx`.
- Multiple pages consume `ctx.get("packets_window")` and `ctx.get("rf_packets")` directly.

2. UI owns ingestion and engine orchestration
- `apps/dashboard.py` directly calls repository loaders and instantiates `RFAnalysisEngine`.
- This bypasses a strict service boundary.

3. Engine still works on packet-like rows (not strict canonical receptions)
- `RFAnalysisEngine` receives `receptions_window` but internally manipulates packet columns (`igate`, `qas`, `raw`, `src`, `ts_utc`).
- `dataset["rf_receptions"]` currently maps to `packets_filtered` semantics.

4. Network logic present in UI pages
- `apps/ui/pages/network_intelligence.py` computes redundancy directly using `ogn_tool.network.network_intelligence` from UI layer.
- This is functional but violates strict UI->engine->analysis flow.

5. Fallback from `rf_receptions` to packets at ingestion layer
- `receptions_repository.load_rf_receptions` falls back to station-filtered `packets` when table is absent.
- This keeps runtime working but weakens canonical RF dataset guarantees.

## 5. Migration Roadmap (small phases)

### Phase 1 – RF normalization layer
Goal:
- Introduce one explicit normalization boundary producing `rf_receptions_canonical`.
Actions:
- Consolidate mapping (`igate/receiver`, `src`, `ts_epoch/ts_utc`, RF metrics).
- Ensure canonical field names are present before engine execution.

### Phase 2 – Engine contract stabilization
Goal:
- Make engine input/output contracts explicit and stable.
Actions:
- Engine input: canonical receptions only.
- Engine output: fixed schema for `rf_analysis_dataset`, `station_metrics`, `network_metrics`.
- Keep packet transport fields out of analysis contracts.

### Phase 3 – UI data contract cleanup
Goal:
- UI consumes engine products, not ingestion artifacts.
Actions:
- Remove page dependencies on `packets_window` where equivalent engine outputs exist.
- Keep `ui_ctx` focused on analyzed datasets and view state.

### Phase 4 – Remove packets fallback
Goal:
- Enforce reception-based RF architecture.
Actions:
- Deprecate and remove `rf_receptions`-missing fallback path.
- Make missing table/state explicit via controlled error or compatibility mode banner.

## 6. Boundary Rules (target)

- Data ingestion may access SQL.
- RF normalization may transform source-specific rows to canonical receptions.
- RF engine may depend on analysis modules, not UI.
- Network intelligence may consume engine outputs or canonical receptions.
- UI must consume engine/network products, not raw SQL or packet transport schemas.
## 7. Canonical Engine Container

`RFAnalysisDataset` (`src/ogn_tool/models/rf_analysis_dataset.py`) is the canonical typed container
for engine outputs.

Role:
- Documents stable and experimental dataset attributes defined in
  `docs/core/RF_DATASET_SCHEMA.md`.
- Provides a typed bridge from the current dictionary-based engine output
  without changing runtime behavior.

Current behavior remains unchanged:
- `RFAnalysisEngine.build_analysis_dataset()` still returns a dictionary.
- `RFAnalysisDataset` is introduced as the formal contract container for
  progressive migration.

## 8. RF Analysis Levels

The RF analysis stack is organized into explicit semantic levels.

### L0 Transport
- APRS packets.
- Raw transport/protocol messages (`src`, `dst`, `qas`, `raw`, timestamps, coordinates when present).

### L1 RF events
- RF receptions per station.
- Reception events represent "station heard aircraft at time T".

### L2 Aircraft states
- Unique aircraft positions extracted from packets.
- A state represents one aircraft position/time state independent of how many stations received it.

### L3 RF observations
- Geometry derived from aircraft position vs station.
- Typical derived fields: distance, bearing, relative altitude.

### L4 Station diagnostics
- Coverage, range, shadow zones.
- Station-level quality and directional diagnostics.

### L5 Network intelligence
- Station overlap, redundancy, network coverage.
- Multi-station structure and blind-zone diagnostics.

### L6 Flight intelligence
- Flight patterns and altitude layers (free-flight analysis).
- Higher-level interpretation of trajectories and RF reception conditions.

Important semantic rule:
- **RF receptions ≠ aircraft states**.
- Multiple RF receptions may correspond to the same aircraft position.

### Pipeline Diagram

```
APRS packets
  ↓
normalization
  ↓
aircraft states
  ↓
rf receptions
  ↓
rf observations
  ↓
station metrics
  ↓
network intelligence
```
