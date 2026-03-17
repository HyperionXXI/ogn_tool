> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

# OGN Tool — Operational Handoff Note

## 1. Core Product

The core product is the RF network intelligence engine, not the
Streamlit dashboard.

The analytical core lives in:

- `src/ogn_tool/models/`
- `src/ogn_tool/analysis/`
- `src/ogn_tool/pipeline/`

The Streamlit dashboard is only a consumer UI.

## 2. System Architecture

The architecture must remain layered.

```text
ingestion
normalization
analysis
intelligence
reporting
UI
```

Responsibilities:

### ingestion
- data acquisition

### normalization
- schema harmonization

### analysis
- computes measurable RF and network facts
- examples: distance, visibility, coverage, packet statistics, geometry,
  signal horizon

### intelligence
- interprets metrics and produces judgments, scenarios, and priorities
- examples: station health, network redundancy, coverage gaps, single
  point of failure, station placement suggestion

### reporting
- assembles operator-level reports

### UI
- visualizes results

## 3. Runtime Contract

The official runtime surface is:

- `results.*`

The most important surface is:

- `results.network_metrics`

Legacy access patterns such as:

- `ctx[...]`

are transitional and must not be expanded.

All downstream components must consume `results.*` surfaces.

## 4. Existing Intelligence Layer

The following modules already exist:

- `station_health`
- `network_summary`
- `station_dependency`
- `station_removal_simulation`
- `station_redundancy_planner`
- `network_single_point_of_failure_detector`
- `coverage_gap_detector`
- `coverage_gap_prioritizer`
- `station_addition_simulation`

These modules produce the current network intelligence layer.

## 5. Reporting Layer

Reporting already exists:

- `src/ogn_tool/reporting/models.py`
- `src/ogn_tool/reporting/network_engineering_report.py`

The next step is to feed reporting directly from `results.network_metrics`.

Reporting must not recompute RF or network metrics.

## 6. Documentation Structure

Documentation is structured as follows.

Entry point:
- `docs/ARCHITECTURE.md`

Canonical rules:
- `docs/architecture/`

Explanatory documentation:
- `docs/core/`

Internal notes:
- `docs/internal/`

New architectural rules must go into:
- `docs/architecture/`

## 7. Rules That Must Not Be Broken

### Layer separation
- analysis -> compute
- intelligence -> interpret
- reporting -> assemble
- UI -> display

### No recomputation
Analysis and intelligence must not:
- recompute RF
- rebuild network structures ad hoc
- access raw dataset paths as primary inputs when typed analytical
  surfaces exist

They must consume analytical surfaces.

### UI must remain thin
The UI may:
- format
- filter
- sort

The UI must not:
- recompute
- classify
- reinterpret analytical results

## 8. Engine Freeze Strategy

Transitional modules still exist:

- `rf_engine_dataset_builder.py`
- `rf_dataset_builder.py`
- `rf_engine_network.py`

These modules must not receive new analytical logic.

## 9. Immediate Priorities

1. Complete the typed surface:
   - `results.network_metrics`
2. Fully connect reporting to this surface.
3. Freeze the analytical core:
   - `v1.1-network-intelligence-core`
4. Only after this milestone:
   - UI improvements
   - mobility
   - weather as observation context
   - new simulations

## 10. Project Status

The project is already a functional RF network intelligence engine.

The current priority is not adding modules, but stabilizing and exposing
existing analytical results.
