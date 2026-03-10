# ROADMAP MASTER — OGN / FANET RF Network Intelligence Platform

> Canonical reference for project direction, architecture, and execution rules.  
> If any document conflicts with this roadmap, **this file is the source of truth**.

## Current capabilities

### Collector + database
- **Collector**: `scripts/collector.py` connects to APRS‑IS, parses packets, stores into SQLite `packets` table (`igate`, `qas`, `raw`, `lat/lon`, etc.).
- **Database**: SQLite with single `packets` table (mixing RF vs APRS‑IS sources).

### Analysis + engine
- **Analysis modules**: `src/ogn_tool/analysis/*` (polar, station_range, station_quality, terrain, azimuth, network, etc.).
- **Engine**: `src/ogn_tool/engine/rf_engine.py` orchestrates analysis, builds the dataset, and computes:
  - `coverage_grid`, `RF probability field`
  - `azimuth_histogram` / `directional_balance`
  - `station_metrics`, `network_metrics`
  - `radio_events`, `station_reception`, `network_blind_zones`

### UI
- **Streamlit app** under `apps/ui/pages/*` with a map‑centric **Coverage Explorer** and supporting dashboards.
- **Map engine**: `apps/ui/map_engine/*` uses pydeck.

## Missing capabilities

- **Canonical RF data model**: repository currently uses a single mixed `packets` table. A proper split into `rf_packets` vs `aprs_packets` is missing.
- **Coverage inference documentation**: current docs do not explain how reception probability is estimated from sparse packet observations.
- **Network intelligence documentation**: need clearer coverage of station overlap, redundancy, and blind-zone detection.
- **Feature roadmap**: no consolidated list of upcoming features and priorities (currently scattered).

## Feature roadmap

This project’s roadmap is built around **RF coverage intelligence**, **station health**, and **network overlap analysis**.

### High‑level feature themes
- **Coverage analysis**: probability grid, azimuth coverage, polar coverage.
- **Station diagnostics**: health scoring, antenna bias, shadow/terrain detection.
- **Network intelligence**: redundancy matrix, blind-zone detection, critical stations.
- **Dataset hygiene**: separate RF vs APRS traffic, stable filtering by station/igate.

## Implementation phases

**Phase 0 — Stabilization / cleanup**
Objective: remove UI inconsistencies, keep map visible, remove redundant controls.
Deliverables: map‑centric layout, single station source, no UI analysis logic.

**Phase 1 — Canonical data model**
Objective: separate RF receptions vs APRS traffic.
Deliverables: `rf_packets` / `aprs_packets` or equivalent separation.

**Phase 2 — Reliable station filtering**
Objective: consistent station selection via `igate` (APRS proxy).
Deliverables: igate‑based filtering across analysis.

**Phase 3 — Map readability & object semantics**
Objective: improve map visuals, layers, object inspection.
Deliverables: clear layers, readable markers, inspector semantics.

**Phase 4 — RF coverage intelligence**
Objective: stable coverage probability / confidence.
Deliverables: robust RF coverage grids & diagnostics.

**Phase 5 — Network topology & diagnostics**
Objective: station overlap / redundancy / blind zones.
Deliverables: network metrics + visualizations.

**Phase 6 — FANET integration**
Objective: FANET local RF coverage & device health.
Deliverables: FANET datasets and map overlays.

**Phase 7 — Terrain‑aware RF modelling**
Objective: terrain shadow and visibility envelopes.
Deliverables: terrain metrics tied to station health.

**Phase 8 — Simulation / planning**
Objective: virtual station placement & network impact.
Deliverables: coverage deltas, redundancy improvements.

**Phase 9 — Advanced observatory platform**
Objective: multi‑station observatory with diagnostics automation.
Deliverables: scheduling, anomaly detection, reporting.

## Coverage inference model

Aircraft traffic is **not** spatially uniform.
Absence of packets does **not** imply absence of RF coverage.

The engine estimates reception probability from observed packets using a model approximating:

```
P(reception | distance, azimuth, altitude)
```

This allows detection of:

- terrain masking
- weak stations
- antenna misalignment
- coverage holes

## RF intelligence pipeline

```
Raw packets
↓
Observations
↓
Metrics
↓
RF diagnostics
↓
Network intelligence
```

### Packets

Source of packets:

- APRS‑IS network
- OGN receiver infrastructure

Packets contain:

```
timestamp
latitude
longitude
altitude
aircraft id
receiver station
```

### Observations

Derived radio observations:

```
distance_km
bearing_deg
relative_altitude
```

### Metrics

Computed statistics:

```
coverage_grid
azimuth_histogram
distance_distribution
RSSI_vs_distance
```

### RF diagnostics

Derived diagnostics:

```
shadow_sectors
terrain_masking
antenna_orientation
coverage_degradation
```

### Network intelligence

Multi-station analysis:

```
station_overlap
coverage_redundancy
network_blind_zones
critical_stations
```

## Non‑goals / guardrails
- Do **not** reintroduce analysis logic in UI.
- Do **not** add features outside `RF_FEATURES_INDEX` without updating roadmap.
- Do **not** split roadmap into multiple competing docs.
- Do **not** invent new data models without mapping to repo reality.

## Execution rules for future Codex tasks
- If contradictions exist, update this roadmap or flag the conflict.
