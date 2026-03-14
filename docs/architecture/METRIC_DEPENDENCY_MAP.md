# Metric Dependency Map

This document describes the analytical metrics currently produced by the
RF network analysis pipeline.

It provides visibility into:

- metric origin
- runtime exposure
- implicit dependencies
- current computation order
- primary consumers

The purpose is to preserve architectural clarity without introducing a
formal metric registry prematurely.

---

## Runtime Surface

The canonical runtime metric surface is:

- `network["metrics"]`
- mirrored into `results.network_metrics`

This surface is serialized through:

- `src/ogn_tool/runtime/analysis_snapshot.py`

The metrics listed below are the current runtime contract surface.

---

## Core Network Metrics

| Metric | Source Module | Runtime Key | Dependencies | Status | Primary Consumers |
|--------|---------------|-------------|--------------|--------|-------------------|
| visibility | `src/ogn_tool/analysis/network_metrics/visibility.py` | `visibility` | normalized observations | stable | analysis / runtime |
| station_influence | `src/ogn_tool/analysis/network_metrics/station_influence.py` | `station_influence` | visibility, graph importance | stable | analysis / runtime |
| station_anomalies | `src/ogn_tool/analysis/network_metrics/station_anomaly.py` | `station_anomalies` | station influence, visibility | experimental | diagnostics / UI |
| network_robustness | `src/ogn_tool/analysis/network_metrics/network_robustness.py` | `network_robustness` | visibility matrix | experimental | analysis / intelligence |
| station_placement | `src/ogn_tool/analysis/network_metrics/station_placement.py` | `station_placement` | visibility dependency, candidate grid | experimental | analysis / runtime |

---

## Intelligence Metrics

| Metric | Source Module | Runtime Key | Dependencies | Status | Primary Consumers |
|--------|---------------|-------------|--------------|--------|-------------------|
| station_health | `src/ogn_tool/analysis/intelligence/station_health.py` | `station_health` | station influence, network robustness, anomalies | exposed | reporting / UI |
| network_summary | `src/ogn_tool/analysis/intelligence/network_summary.py` | `network_summary` | station health, network robustness, visibility summary | exposed | reporting / UI |
| station_dependency | `src/ogn_tool/analysis/intelligence/station_dependency.py` | `station_dependency` | visibility overlap, station influence, network robustness | exposed | reporting / UI |
| spof | `src/ogn_tool/analysis/intelligence/network_single_point_of_failure_detector.py` | `spof` | visibility matrix, station removal simulation | exposed | reporting / UI |
| coverage_gaps | `src/ogn_tool/analysis/intelligence/coverage_gap_detector.py` | `coverage_gaps` | normalized observations with `lat`, `lon`, `station_id` | exposed | reporting / UI |
| coverage_gap_priorities | `src/ogn_tool/analysis/intelligence/coverage_gap_prioritizer.py` | `coverage_gap_priorities` | coverage gaps | exposed | reporting / planning |
| station_redundancy_planner | `src/ogn_tool/analysis/intelligence/station_redundancy_planner.py` | `station_redundancy_planner` | visibility matrix, station removal simulation | experimental | reporting / planning |
| station_addition_simulation | `src/ogn_tool/analysis/intelligence/station_addition_simulation.py` | `station_addition_simulation` | candidate locations, normalized observations | experimental | reporting / planning |

---

## Internal / Non-Canonical Analytical Functions

The following analytical functions exist in the codebase but are not
currently exposed as canonical runtime metric surfaces:

| Function | Source Module | Reason |
|----------|---------------|--------|
| station_removal_simulation | `src/ogn_tool/analysis/intelligence/station_removal_simulation.py` | scenario function, not stable global runtime surface |

These functions may support runtime metrics, but are not themselves part
of the public runtime contract.

---

## Current Computation Order

The current computation order is enforced directly in:

- `src/ogn_tool/pipeline/network_graph_stage.py`

Current order:

```text
dataset observations
  -> visibility
  -> station_influence
  -> station_anomalies
  -> network_robustness
  -> station_placement
  -> station_health
  -> network_summary
  -> station_dependency
  -> spof
  -> station_redundancy_planner
  -> coverage_gaps
  -> coverage_gap_priorities
  -> station_addition_simulation
```

This order is currently implicit in the pipeline implementation.

---

## Architectural Rule

The runtime metric surface is defined only by:

- `network["metrics"]`
- `results.network_metrics`

Metrics not exposed through this surface are not considered delivered
runtime capabilities.

If metric dependencies grow substantially in complexity, the project may
introduce a formal metric registry in the future.

Until that threshold is reached, the dependency map acts as the current
architectural reference.
