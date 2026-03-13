# RF Analysis Capability Audit

This document tracks analytical capabilities implemented in the project
and their current integration status after the architecture refactor.

It is intended to answer a simple question:

Which capabilities are already implemented, which are fully connected to
the typed runtime, and which still remain legacy or only partially
integrated?

## Core Network Metrics (current)

| Capability | Module | Status |
|------------|--------|--------|
| Visibility matrix | `analysis/network_metrics/visibility.py` | ACTIVE |
| Station influence | `analysis/network_metrics/station_influence.py` | ACTIVE |
| Station anomalies | `analysis/network_metrics/station_anomaly.py` | ACTIVE |
| Network robustness | `analysis/network_metrics/network_robustness.py` | ACTIVE |
| Station placement | `analysis/network_metrics/station_placement.py` | ACTIVE |

These capabilities are currently exposed through typed network metrics and
are part of the active network intelligence surface.

## Additional RF Capabilities Already Present

| Capability | Current location | Current status |
|------------|------------------|----------------|
| Coverage probability field / heatmap | `analysis/rf_metrics/probability_field.py` | ACTIVE |
| Blind zone detection | `analysis/rf_metrics/blind_zone_detection.py` | ACTIVE |
| Antenna pattern estimation | `analysis/rf_metrics/antenna_pattern.py` | ACTIVE |
| Radio horizon modelling | `analysis/rf_models/radio_horizon.py` | ACTIVE |
| RF visibility model | `analysis/rf_models/rf_visibility_model.py` | ACTIVE |
| Terrain visibility analysis | `analysis/rf_models/terrain_visibility.py` | ACTIVE |

These capabilities remain part of the RF analysis kernel and are already
connected to the typed RF results path.

## Previously Implemented Or Transitional Capabilities

| Capability | Current / previous location | Current status |
|------------|-----------------------------|----------------|
| Coverage heatmap UI usage | `apps/ui/pages/coverage.py`, `apps/ui/pages/rf_map.py` | ACTIVE |
| RF shadow detection / shadow map | `analysis/rf_metrics/directional_analysis.py`, `analysis/shadow.py` | PARTIAL |
| Terrain horizon / station horizon summaries | `analysis/rf_models/radio_horizon.py`, `apps/ui/pages/station_intelligence.py` | ACTIVE |
| Station reliability / quality scoring | `analysis/network/station_quality.py` | PARTIAL |
| Station comparison scoring | `analysis/network/station_compare.py` | PARTIAL |
| Station planner / location suggestions | `analysis/intelligence/station_planner.py` | ACTIVE |

### Interpretation of statuses

- `ACTIVE`
  Capability exists, is implemented in the current codebase, and is still
  connected to the runtime or typed results path.

- `PARTIAL`
  Capability exists and is still useful, but remains connected through a
  transitional or legacy-oriented path. It should be reviewed before being
  treated as a stable typed metric.

- `UNKNOWN`
  Capability is suspected to exist historically, but has not yet been
  located or validated in the current codebase.

## Known Gaps After Refactor

The following gaps are currently visible:

- some RF diagnostic artifacts still surface through transitional metrics
  paths rather than fully typed result contracts
- station quality and comparison metrics remain under the older
  `analysis/network/` namespace
- shadow diagnostics are available, but their typed integration remains
  weaker than the newer network metrics

## Actions

For each `PARTIAL` or `UNKNOWN` capability:

1. Locate the canonical implementation in the current repository or in the
   repository history.
2. Decide whether to:
   - reconnect it to the typed metrics pipeline
   - rewrite it cleanly in the new architecture
   - archive it as obsolete
3. Avoid re-implementing an analytical capability before this audit has
   been checked.

## Current Architectural Reading

The project now has a stable typed network intelligence surface built around:

- visibility
- station influence
- station anomalies
- network robustness
- station placement

This means the network analysis kernel is now materially stronger than the
legacy dashboard/runtime layer.
