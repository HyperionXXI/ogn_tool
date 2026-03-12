STATUS: canonical
SOURCE_OF_TRUTH: docs/core/RF_DATASET_SCHEMA.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# RF Dataset Schema (Free-Flight Oriented)

This document defines the dataset schema produced by `RFAnalysisEngine` with explicit support for free-flight analysis workflows.

Primary producer:
- `src/ogn_tool/engine/rf_engine.py`

Related contract:
- `docs/core/DATA_CONTRACT.md` (canonical field naming and normalization intent)

Note:
- This file documents current engine outputs and the free-flight datasets derived from them.

## 1. Engine Outputs (current)

`RFAnalysisEngine.build_analysis_dataset(...)` currently produces a dataset dictionary containing:

- `observations`
- `packets_all`
- `packets_rf`
- `packets_filtered`
- `rf_receptions`
- `radio_events`
- `station_reception`
- `coverage_grid`
- `coverage_redundancy_grid`
- `station_metrics`
- `network_metrics`
- `azimuth_histogram`
- `directional_balance`
- `rf_diagnosis`
- `shadow_map`
- `station_overlap_matrix`
- `blind_cells`
- `network_blind_zones`
- `stations`
- `dataset_mode`

`RFAnalysisEngine.run()` returns `RFAnalysisResults` with:

- `feature_matrix`
- `coverage`
- `visibility`
- `blind_zones`
- `antenna_pattern`
- `antenna_shadow_sectors`
- `network_graph`
- `network_metrics`
- `network_timeseries`
- `network_events`
- `network_evolution`
- `station_suggestions`
- `metrics`

## 2. Flight-Relevant Datasets

Required for free-flight analysis:

- `rf_receptions`
- `aircraft_tracks`
- `station_metrics`
- `coverage_grid`
- `network_overlap`
- `network_graph`

Current engine mapping:

- `rf_receptions`: explicit dataset key.
- `aircraft_tracks`: not a dedicated key yet; currently represented by `observations`/`radio_events`/`distance_df` depending view.
- `station_metrics`: explicit dataset key.
- `coverage_grid`: explicit dataset key.
- `network_overlap`: currently represented by `station_overlap_matrix`.
- `network_graph`: explicit typed result key in `RFAnalysisResults`.

## 3. Canonical Schema Definitions

### 3.1 `rf_receptions`

Producer module:
- `src/ogn_tool/engine/rf_engine.py` (currently sourced from `packets_filtered` semantics)

Expected fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `station_id` (current alias often `igate`/`receiver`) | `string` | stable | canonical target from DATA_CONTRACT |
| `aircraft_id` (current alias often `src`) | `string` | stable | canonical target from DATA_CONTRACT |
| `timestamp` (current alias often `ts_epoch`/`ts_utc`) | `int64` or `datetime-like` | stable | canonical target from DATA_CONTRACT |
| `timestamp_ns` | `int64` | experimental | high-resolution timestamp when ingestion path provides it |
| `lat` | `float64` | stable | WGS84 latitude |
| `lon` | `float64` | stable | WGS84 longitude |
| `altitude` (`altitude`/`altitude_m`) | `float64` | experimental | may be absent in packet fallback mode |
| `snr` (`snr`/`snr_db`) | `float64` | experimental | available only when source provides RF metrics |
| `freq_offset` | `float64` | experimental | mostly from `rf_receptions` table path |
| `bit_errors` | `int64` | experimental | mostly from `rf_receptions` table path |
| `distance_km` | `float64` | stable | derived in engine |
| `bearing_deg` | `float64` | stable | derived in engine |
| transport fields (`raw`,`qas`,`dst`, etc.) | mixed | internal | packet transport metadata, not canonical RF contract |

### 3.2 `aircraft_tracks`

Producer module:
- Target: `src/ogn_tool/engine/rf_engine.py` (not yet explicit as dedicated dataset key)
- Current source equivalents: `observations`, `radio_events`, `distance_df`

Canonical free-flight fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `aircraft_id` | `string` | stable | canonical flight entity |
| `timestamp` | `int64` or `datetime-like` | stable | event time |
| `lat` | `float64` | stable | track coordinate |
| `lon` | `float64` | stable | track coordinate |
| `altitude` | `float64` | experimental | may be sparse |
| `station_count` | `int64` | experimental | multi-station hearing richness |
| `packet_count` | `int64` | experimental | per-event aggregation |
| `distance_km` | `float64` | experimental | station-relative when needed |

### 3.3 `station_metrics`

Producer module:
- `src/ogn_tool/engine/rf_engine.py`

Typical fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `igate` (canonical target `station_id`) | `string` | stable | station key |
| `packet_count` | `int64` | stable | packets attributed to station |
| `aircraft_count` | `int64` | stable | unique aircraft |
| `max_distance` | `float64` | stable | max observed range |
| `p95_distance` | `float64` | stable | robust range indicator |
| `coverage_cells` | `int64` | stable | spatial footprint proxy |
| `unique_packets` | `int64` | experimental | contribution analysis |
| `shared_packets` | `int64` | experimental | overlap analysis |
| `redundant_packets` | `int64` | experimental | overlap analysis |
| `contribution_score` | `float64` | experimental | contribution quality |

### 3.4 `coverage_grid`

Producer module:
- `src/ogn_tool/engine/rf_engine.py`
- via probability-field builder

Typical fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `lat` | `float64` | stable | grid cell latitude |
| `lon` | `float64` | stable | grid cell longitude |
| `packets` and/or `packet_count` | `int64` | stable | cell activity |
| `max_distance` and/or `max_distance_km` | `float64` | stable | range proxy |
| `cell_size_deg` | `float64` | experimental | depends on producer path |
| probability/confidence columns | `float64` | experimental | model-dependent |
| `mean_altitude` | `float64` | experimental | optional enrichment |

### 3.5 `network_metrics`

Producer module:
- `src/ogn_tool/analysis/network_metrics/*`
- attached by `src/ogn_tool/engine/rf_engine.py`

Fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `station_count` | `int64` | stable | stations in analyzed dataset |
| `coverage_cells` | `int64` | stable | occupied coverage cells |
| `redundancy_cells` | `int64` | stable | cells with >1 station hearing |
| `blind_cells` | `int64` | stable | low-redundancy cells |
| `network_resilience_score` | `float64` | stable | redundancy/coverage ratio |

### 3.6 `network_overlap` (canonical free-flight view)

Producer module:
- current key: `station_overlap_matrix`
- metrics-side logic: `src/ogn_tool/analysis/network_metrics/station_metrics.py`

Fields (matrix form):

| field | type | stability | notes |
| --- | --- | --- | --- |
| index: `station_id` (current often callsign/igate) | `string` | stable | row station |
| columns: `station_id` | `string` | stable | column station |
| cell value overlap count | `int64` | stable | shared event count |

### 3.7 `network_graph`

Producer modules:
- `src/ogn_tool/analysis/network_graph/rf_graph_builder.py`
- `src/ogn_tool/engine/network_graph_engine.py`

Canonical typed model:
- `src/ogn_tool/models/network_graph_model.py`

Typed objects:

| object | fields | stability | notes |
| --- | --- | --- | --- |
| `NetworkNode` | `id`, `type`, `lat`, `lon`, `altitude`, `attributes` | stable | `lat`/`lon` remain optional for backward compatibility |
| `NetworkEdge` | `source`, `target`, `relation`, `weight`, `attributes` | stable | `relation`: `reception` / `coverage` / future graph relations |
| `NetworkGraph` | `nodes`, `edges`, `metrics` | stable | canonical graph container |

Node types:
- `station`
- `aircraft`
- `grid_cell`

Edge relations:
- `reception`
- `coverage`
- future: `overlap`

Compatibility rule:
- `NetworkGraph` is intentionally mapping-friendly for current callers.
- Existing usage patterns remain valid:
  - `graph.get("nodes")`
  - `"nodes" in graph`
  - `graph["edges"]`

### 3.8 `network_timeseries`

Producer modules:
- `src/ogn_tool/analysis/network_graph/network_timeseries.py`
- attached by `src/ogn_tool/pipeline/network_graph_stage.py`

Typical content:
- station activity time series
- network load time series
- coverage time series

Stability:
- experimental

### 3.9 `network_events`

Producer modules:
- `src/ogn_tool/analysis/network_graph/network_events.py`
- attached by `src/ogn_tool/pipeline/network_graph_stage.py`

Typical content:
- station outages
- coverage regressions
- network anomalies

Stability:
- experimental

### 3.10 `network_evolution`

Producer modules:
- `src/ogn_tool/analysis/network_graph/network_metrics.py`
- attached by `src/ogn_tool/pipeline/network_graph_stage.py`

Fields:

| field | type | stability | notes |
| --- | --- | --- | --- |
| `coverage_growth` | `int64` | experimental | change in covered grid-cell count |
| `station_importance_change` | `dict[str, float]` | experimental | per-station delta |
| `redundancy_change` | `float64` | experimental | mean coverage redundancy delta |
| `blind_zone_change` | `int64` | experimental | blind zone count delta |

## 4. Stability Model

Definitions:
- **stable**: safe for UI/API integration.
- **experimental**: available but schema may evolve.
- **internal**: debug/compatibility only, not public contract.

### Stable integration surface (recommended)

- `rf_receptions` (canonical fields)
- `station_metrics`
- `coverage_grid`
- `network_metrics`
- `station_overlap_matrix` (as `network_overlap` view)
- `network_graph`
- `rf_diagnosis`
- `metrics["rf_models"]`

### Experimental surface

- `observations`
- `radio_events`
- `station_reception`
- `coverage_redundancy_grid`
- `azimuth_histogram`
- `directional_balance`
- `shadow_map`
- `blind_cells`
- `azimuth_df`
- `terrain_mask`
- `network_timeseries`
- `network_events`
- `network_evolution`
- `station_suggestions`

### Internal surface

- `packets_all`
- `packets_rf`
- `packets_filtered`
- transport metadata columns used for compatibility (`raw`, `qas`, `dst`) in analysis-facing tables

## 5. Relationship with DATA_CONTRACT

`docs/core/DATA_CONTRACT.md` defines:
- canonical RF reception naming and field mapping.

This document (`RF_DATASET_SCHEMA.md`) defines:
- the concrete engine-produced datasets,
- how free-flight datasets map onto current outputs,
- and which fields are stable vs experimental.

Contract alignment rule:
- canonical names from `DATA_CONTRACT.md` should be considered the target vocabulary,
- while this schema records current operational aliases and producer behavior.
