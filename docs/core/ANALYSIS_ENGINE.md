STATUS: derived
REFERENCE: docs/core/ROADMAP_MASTER.md

# Analysis Engine

This document describes the RF analysis engine architecture and data flow.

## RF Intelligence Pipeline

The analysis engine processes RF/AIS packet data into a structured dataset and diagnostics.

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

Packet sources:

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

Derived radio observations added by the engine:

```
distance_km
bearing_deg
relative_altitude
```

### Metrics

Computed statistics available in the engine dataset:

```
coverage_grid
azimuth_histogram
distance_distribution
RSSI_vs_distance
```

### RF diagnostics

Diagnostics derived from metrics:

```
shadow_sectors
terrain_masking
antenna_orientation
coverage_degradation
```

### Network intelligence

Multi-station analysis products:

```
station_overlap
coverage_redundancy
network_blind_zones
critical_stations
```

## Engine structure

The core engine is `src/ogn_tool/engine/rf_engine.py`. It:

- builds a dataset from raw packet records
- computes geometric metrics (distance/bearing)
- computes per-station and network metrics
- exposes a single dataset for UI consumption

The engine is intentionally separate from UI components; the UI should only visualize the dataset.


## RF Analysis Levels

The analysis engine operates across explicit RF analysis levels.

### L0 Transport
- APRS packets.

### L1 RF events
- RF receptions per station.

### L2 Aircraft states
- Unique aircraft positions extracted from packets.

### L3 RF observations
- Geometry derived from aircraft position vs station.

### L4 Station diagnostics
- Coverage, range, shadow zones.

### L5 Network intelligence
- Station overlap, redundancy, network coverage.

### L6 Flight intelligence
- Flight patterns and altitude layers (free-flight analysis).

Clarification:
- **RF receptions ≠ aircraft states**.
- Multiple RF receptions may correspond to the same aircraft position.
