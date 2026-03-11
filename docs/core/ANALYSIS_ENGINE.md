STATUS: derived
REFERENCE: docs/core/ROADMAP_MASTER.md

# Analysis Engine

This document describes the RF analysis engine architecture and data flow.

## RF Intelligence Pipeline

The analysis engine processes transport packets into RF observations, metrics, diagnostics and network intelligence outputs.

```
Raw packets
↓
Aircraft states
↓
RF observations
↓
RFAnalysisPipeline
   ├─ Coverage stage
   ├─ Visibility stage
   ├─ Blind zone stage
   ├─ Diagnostics stage
↓
Network intelligence
```

## RF Analysis Pipeline

RF analysis is executed as a sequence of pipeline stages implementing a common stage contract.

Each stage:
- consumes a dataset
- enriches it with additional RF metrics or diagnostics
- returns the dataset

Pipeline intent:
- deterministic execution order
- explicit metric ownership per stage
- composable extension for new RF models

## Analysis Module Types

### Pipeline stages
- `RFCoverageStage`
- `VisibilityModelStage`
- `BlindZoneDetectionStage`
- `RFDiagnosticsStage`

### Analysis primitives
- `geometry`
- `signal_distance`
- `radio_horizon`
- `azimuth`
- `rf_visibility_model`

## Packets

Packet sources:
- APRS‑IS network
- OGN receiver infrastructure

Core packet transport fields typically include:
- timestamp
- latitude
- longitude
- altitude
- aircraft id
- receiver station

## Observations

Derived RF observations added by the engine include:
- `distance_km`
- `bearing_deg`
- `relative_altitude`

## Metrics

Computed statistics available in the engine dataset include:
- `coverage_grid`
- `azimuth_histogram`
- `distance_distribution`
- `RSSI_vs_distance`
- `coverage_probability_field` (estimated by `RFCoverageMap`)
- `polar_coverage_grid`
- `distance_exposure_distribution`

## RF diagnostics

Diagnostics derived from metrics include:
- `shadow_sectors`
- `terrain_masking`
- `antenna_orientation`
- `coverage_degradation`

## Network intelligence

Multi-station analysis products include:
- `station_overlap`
- `coverage_redundancy`
- `network_blind_zones`
- `critical_stations`

## Engine structure

The core engine is `src/ogn_tool/engine/rf_engine.py`. It:
- builds an observation-centric dataset
- computes geometric and RF metrics
- executes staged RF diagnostics
- exposes a single dataset for UI/service consumption

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

## Dependency Architecture

Dependency flow rule:

```
models
↓
analysis primitives
↓
pipeline stages
↓
pipeline runner
↓
engine
↓
services
↓
network
```

No reverse dependency is allowed between these layers.

## RF Module Status Matrix

| Module | Layer | Type | Status |
|---|---|---|---|
| `src/ogn_tool/models/rf_types.py` | L0-L3 | model contract | implemented |
| `src/ogn_tool/analysis/rf_kernel/geometry.py` | L3 | analysis primitive | implemented |
| `src/ogn_tool/analysis/rf_kernel/spatial_index.py` | L3 | analysis primitive | implemented |
| `src/ogn_tool/analysis/aircraft_states.py` | L2 | analysis primitive | implemented |
| `src/ogn_tool/analysis/rf_normalization.py` | L1 | analysis primitive | implemented |
| `src/ogn_tool/analysis/observation_pipeline.py` | L3 | pipeline stage support | implemented |
| `src/ogn_tool/analysis/rf_state_engine.py` | L3-L4 | pipeline runner support | implemented |
| `src/ogn_tool/intelligence/rf_coverage_map.py` | L4 | pipeline stage (`RFCoverageStage`) | implemented |
| `src/ogn_tool/analysis/rf_visibility_model.py` | L4 | pipeline stage (`VisibilityModelStage`) | implemented |
| `src/ogn_tool/analysis/rf_blind_zone_detection.py` | L4-L5 | pipeline stage (`BlindZoneDetectionStage`) | implemented |
| `src/ogn_tool/analysis/rf_diagnosis.py` | L4 | pipeline stage (`RFDiagnosticsStage`) | experimental |
| `src/ogn_tool/analysis/signal_distance.py` | L4 | analysis primitive | implemented |
| `src/ogn_tool/analysis/radio_horizon.py` | L4 | analysis primitive | implemented |
| `src/ogn_tool/analysis/azimuth.py` | L4 | analysis primitive | implemented |
| `src/ogn_tool/engine/rf_engine.py` | L4-L5 | engine orchestrator | implemented |
| `src/ogn_tool/services/rf_analysis_pipeline.py` | L4-L5 | service pipeline runner | implemented |
| `src/ogn_tool/services/rf_analysis_service.py` | L4-L5 | service facade | implemented |
| `src/ogn_tool/network/network_intelligence.py` | L5 | network analysis | implemented |
| `src/ogn_tool/rf_probability_field.py` | L4-L5 | analysis primitive | experimental |
| `src/ogn_tool/analysis/experimental/azimuth.py` | L4 | analysis primitive | experimental |
| `src/ogn_tool/analysis/propagation_model.py` | L4 | analysis primitive | planned |
| `src/ogn_tool/analysis/antenna_pattern_estimator.py` | L4 | analysis primitive | planned |
| `src/ogn_tool/analysis/reception_probability_inference.py` | L5 | analysis primitive | planned |
| `src/ogn_tool/analysis/rf_probability_field.py` | L4-L5 | analysis primitive | planned |
