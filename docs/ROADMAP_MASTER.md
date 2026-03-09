# ROADMAP MASTER — OGN / FANET RF Network Intelligence Platform

> Canonical reference for project direction, architecture, and execution rules.  
> If any document conflicts with this roadmap, **this file is the source of truth**.

## 1. Project vision
Build a **map‑centric RF and network intelligence platform** for OGN / APRS‑IS / FANET reception networks.  
This is **not** a simple APRS viewer or dashboard. The platform must:

- quantify **RF reception quality** and coverage
- diagnose **station health** and antenna/terrain effects
- analyse **network redundancy** and overlap
- support **multi‑station comparison**
- evolve toward **planning/simulation**

Target positioning: *“Network Intelligence Platform for OGN/FANET reception networks”*.

## 2. Current repository reality (fact‑based)
What exists today in the repo:

- **Collector**: `scripts/collector.py` connects to APRS‑IS, parses packets, stores into SQLite `packets` table (`igate`, `qas`, `raw`, `lat/lon`, etc.).
- **Database**: SQLite with `packets` table (single mixed source).
- **Analysis modules**: `src/ogn_tool/analysis/*` (polar, station_range, station_quality, terrain, etc.).
- **Engine**: `src/ogn_tool/engine/rf_engine.py` orchestrates analysis, builds dataset, adds network metrics (radio_events, station_reception, redundancy).
- **UI**: Streamlit under `apps/ui/pages/*` with map‑centric **Coverage Explorer** and supporting pages.
- **Map engine**: `apps/ui/map_engine/*` uses pydeck.

Current limitations:

- **APRS‑IS igate is a proxy** for RF reception (injector ≠ receiver).
- **Single mixed `packets` table** (RF vs APRS‑IS not separated).
- **Map interaction limitations** due to Streamlit + pydeck (no native click‑to‑Python).

## 3. Canonical architecture
Layered architecture (strict):

```
collector → database → analysis modules → engine → UI
```

Responsibilities:

- **collector**: ingest / parse / store only (no analysis).
- **database**: canonical storage (packets, receptions, grids).
- **analysis modules**: pure computations.
- **engine**: orchestration + dataset building.
- **UI**: visualization and interaction only.

Rule: **engine = compute, UI = visualize**.

## 4. Canonical RF data model
Target model (canonical):

**RF receptions (authoritative)**
```
rf_packets
  timestamp
  receiver_id  (station)
  aircraft_id
  lat, lon, altitude
  rssi, snr
  distance_km, bearing_deg
  source = RF
```

**APRS/OGN network traffic (proxy)**
```
aprs_packets
  timestamp
  aircraft_id
  lat, lon, altitude
  igate, path, qas
  source = APRS-IS
```

**Stations**
```
stations
  station_id, lat, lon, altitude, station_type, antenna_gain
```

**Aircraft**
```
aircraft
  aircraft_id, type, first_seen, last_seen
```

**Radio events / receptions**
```
radio_events       (unique emission)
station_reception  (event ↔ station)
```

Important limitation:
**APRS‑IS igate = station that injects into network**, not necessarily the RF receiver.

## 5. Protocol support strategy
- **APRS/OGN (APRS‑IS)**: network traffic proxy / aircraft tracking.
- **FANET**: local RF mesh, closer to “real” RF behaviour.
- **FLARM/OGN RF direct**: future ingestion (debug stream / receiver feed).

## 6. Analysis engine scope (canonical)
Minimum categories:

- **Coverage** (grid, probability, confidence)
- **Redundancy / overlap**
- **Station health / quality**
- **Propagation (RSSI vs distance, altitude vs distance)**
- **Azimuth / antenna behaviour**
- **Terrain / shadow**
- **Network topology**
- **Diagnostics / comparison**

Link to existing modules: `src/ogn_tool/analysis/*`.

## 7. UI/UX target state
UI must be **map‑centric** and question‑driven:

Views (target):

- **Overview**
- **Coverage**
- **RF Analysis**
- **Network**
- **Station Diagnostics**
- **Comparison**

Key rule: **no RF analysis logic in UI**.

## 8. Phased roadmap (canonical)

**Phase 0 — Stabilization / cleanup**  
Objective: remove UI inconsistencies, keep map visible, remove redundant controls.  
Deliverables: map‑centric layout, single station source, no UI analysis logic.

**Phase 1 — Canonical data model**  
Objective: separate RF receptions vs APRS traffic.  
Deliverables: rf_packets / aprs_packets or equivalent separation.

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

## 9. Non‑goals / guardrails
- Do **not** reintroduce analysis logic in UI.
- Do **not** add features outside `RF_FEATURES_INDEX` without updating roadmap.
- Do **not** split roadmap into multiple competing docs.
- Do **not** invent new data models without mapping to repo reality.

## 10. Execution rules for future Codex tasks
- Always compare changes to **ROADMAP_MASTER.md**.
- Always list modified files explicitly.
- Always state whether change is **code** or **docs**.
- Avoid large refactors unless requested.
- Enforce **engine != UI**.
- If contradictions exist, update this roadmap or flag the conflict.
