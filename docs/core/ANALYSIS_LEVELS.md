STATUS: canonical
SOURCE_OF_TRUTH: docs/core/ANALYSIS_LEVELS.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# Analysis Levels

This document defines analysis levels and boundaries used in the project.

## RF analysis

Focus:
- per-packet / per-reception RF behavior
- geometry and signal relationships

Typical outputs:
- distance distributions
- azimuth distributions
- propagation indicators

## Station analysis

Focus:
- one station performance and footprint

Typical outputs:
- station range
- directional balance
- station diagnostics

## Network analysis

Focus:
- relations across stations and aircraft

Typical outputs:
- station overlap
- redundancy grids
- blind-zone candidates

## Network intelligence

Focus:
- interpretation and decision-oriented observability

Typical outputs:
- critical area identification
- candidate placement suggestions
- cross-layer network diagnostics

## Data flow diagram

```
raw_packets
  -> observations
  -> rf_metrics
  -> station_analysis
  -> network_analysis
  -> network_intelligence
  -> ui_views
```

