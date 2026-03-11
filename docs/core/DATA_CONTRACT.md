STATUS: canonical
SOURCE_OF_TRUTH: docs/core/DATA_CONTRACT.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# Data Contract

This document defines the actual and canonical RF datasets used by the project.

## 1. Dataset Usage Map (current code)

| dataset_name | source_module | fields (main) | used_by |
| --- | --- | --- | --- |
| `packets_window` | `src/ogn_tool/data/packets_repository.py` via `load_packets_window(...)` | `ts_epoch`, `ts_utc`, `src`, `dst`, `igate`, `qas`, `lat`, `lon`, `raw` | `apps/dashboard.py`, UI pages through `ui_ctx["packets_window"]` |
| `receptions_window` | `src/ogn_tool/data/receptions_repository.py` via `load_rf_receptions(...)` | If `rf_receptions` exists: `packet_id`, `receiver`, `snr`, `freq_offset`, `bit_errors`, `altitude`, `ts_epoch`, joined packet fields (`src`, `dst`, `igate`, `qas`, `lat`, `lon`, `raw`). Fallback path (no table): packet subset (`packet_id`, `src`, `igate`, `lat`, `lon`, `raw`, `ts_epoch`) | `apps/dashboard.py` input to `RFAnalysisEngine(...)` |
| `dataset` | `src/ogn_tool/engine/rf_engine.py` via `build_analysis_dataset(...)` | `observations`, `packets_all`, `packets_rf`, `packets_filtered`, `rf_receptions`, `coverage_grid`, `station_metrics`, `network_metrics`, `azimuth_histogram`, `directional_balance`, `shadow_map`, `network_blind_zones`, `dataset_mode`, etc. | `apps/dashboard.py`, all major pages via `ui_ctx["dataset"]` |
| `rf_packets` | `apps/dashboard.py` from `dataset["rf_receptions"]` | reception-like frame used by UI, commonly including `src`, `igate`, `lat`, `lon`, `ts_epoch`, optional `snr`, `freq_offset`, `bit_errors`, `distance_km`, `bearing_deg` | `station_intelligence`, `coverage_explorer`, `rf_map`, `diagnostics`, `network_intelligence`, etc. |
| `rf_packets_global` | `apps/dashboard.py` from `dataset["packets_rf"]` | RF-filtered packets (`QAR/QAO` or station mode selection) | KPI blocks and some pages through `ui_ctx` |
| `aircraft_packets` | `apps/dashboard.py` from `packets_window` with non-null `lat/lon` | aircraft position subset | aircraft visualizations / map views |

## 2. Actual Packet Schema (as loaded today)

Primary packet select used by repository loaders:

- `ts_epoch`
- `ts_utc`
- `src`
- `dst`
- `igate`
- `qas`
- `lat`
- `lon`
- `raw`

Observed variants in analysis/engine code:

- `altitude` and/or `altitude_m`
- `receiver` (mapped to `igate` when needed)
- `rssi` / `rssi_db`
- `snr` / `snr_db`
- `ts_utc` as fallback when `ts_epoch` is missing

## 3. Receptions Schema (current operational)

### 3.1 When `rf_receptions` table exists

- `packet_id`
- `receiver`
- `snr`
- `freq_offset`
- `bit_errors`
- `altitude`
- `ts_epoch`
- joined packet fields: `src`, `dst`, `igate`, `qas`, `lat`, `lon`, `raw`

### 3.2 Fallback when `rf_receptions` table is absent

- `packet_id` (from `packets.id`)
- `src`
- `igate`
- `lat`
- `lon`
- `raw`
- `ts_epoch`

This fallback is currently active in part of deployments and keeps the dashboard operational.

## 4. Canonical RF Reception Schema (target for stabilization)

Canonical fields:

- `station_id`
- `aircraft_id`
- `timestamp`
- `lat`
- `lon`
- `altitude`
- `snr`
- `freq_offset`
- `bit_errors`

Optional derived fields (engine-level, not raw storage):

- `distance_km`
- `bearing_deg`
- `protocol`
- `packet_id`

## 5. Field Mapping (code -> canonical)

| code_field | canonical_field | notes |
| --- | --- | --- |
| `igate` | `station_id` | Used in packet-centric paths |
| `receiver` | `station_id` | Used in `rf_receptions` table path |
| `src` | `aircraft_id` | Aircraft/transmitter ID |
| `ts_epoch` | `timestamp` | Preferred canonical timestamp source |
| `ts_utc` | `timestamp` | Fallback if `ts_epoch` unavailable |
| `lat` | `lat` | Numeric normalization required |
| `lon` | `lon` | Numeric normalization required |
| `altitude` | `altitude` | Already canonical name in reception table |
| `altitude_m` | `altitude` | Canonicalized to meters |
| `snr` / `snr_db` | `snr` | Unify naming to `snr` |
| `freq_offset` | `freq_offset` | Already canonical |
| `bit_errors` | `bit_errors` | Already canonical |
| `raw` | *(no canonical RF field)* | Keep as protocol payload for parsing/traceability |
| `dst` | *(no canonical RF field)* | Protocol routing metadata |
| `qas` | *(no canonical RF field)* | APRS transport class metadata |
| `id` / `packet_id` | `packet_id` | Traceability key |

## 6. Recommended Migration Path (documentation-level)

1. Normalize all engine/UI RF inputs to canonical names at load boundary:
   - `station_id`, `aircraft_id`, `timestamp`, `lat`, `lon`, `altitude`, `snr`, `freq_offset`, `bit_errors`.
2. Keep packet transport fields (`raw`, `dst`, `qas`) in a separate packet payload contract.
3. Make `rf_receptions` the preferred source; keep packet fallback explicitly marked as compatibility mode.
4. Keep derived fields (`distance_km`, `bearing_deg`) as computed analysis fields, not required raw schema.
## 7. RF Analysis Levels

The data contract is interpreted across the following RF analysis levels.

### L0 Transport
- APRS packets.
- Transport-level fields (`raw`, `qas`, `dst`, packet timestamps).

### L1 RF events
- RF receptions per station.
- Event semantics: one station receives one aircraft transmission.

### L2 Aircraft states
- Unique aircraft positions extracted from packets.
- Position/time state independent from reception multiplicity.

### L3 RF observations
- Geometry derived from aircraft position vs station.
- Derived fields include station-relative distance and bearing.

### L4 Station diagnostics
- Coverage, range, shadow zones.
- Station-centric health and quality outputs.

### L5 Network intelligence
- Station overlap, redundancy, network coverage.
- Multi-station network-level metrics.

### L6 Flight intelligence
- Flight patterns and altitude layers (free-flight analysis).

Semantic clarification:
- **RF receptions ≠ aircraft states**.
- Multiple RF receptions may correspond to the same aircraft position.
