# Network Engineering Report

This document defines the contract for the network engineering reporting
layer.

The reporting layer exists to transform typed analytical outputs into a
stable, operator-facing summary without introducing new analytical logic.

## Purpose

The project already computes network diagnostics and engineering signals
through the analytical kernel.

The role of reporting is to:

- assemble these typed outputs into one operator-facing report
- keep the result stable and easy to consume
- prepare JSON export and future UI/report surfaces

Reporting is not part of the analytical kernel.

It consumes analytical outputs and presents them in a coherent product
surface.

## Architectural Position

The reporting layer sits after analysis and before UI.

```text
analysis
  -> network_metrics
  -> intelligence
  -> reporting
  -> UI
```

Rules:

- `analysis/` computes metrics and intelligence outputs
- `reporting/` assembles and summarizes
- `apps/ui/` displays only

Reporting must not recompute RF metrics, network metrics, or intelligence
logic.

## Canonical Inputs

The canonical source for reporting is the typed runtime results surface.

Current inputs must be read from:

- `results.network_metrics["station_health"]`
- `results.network_metrics["network_summary"]`
- `results.network_metrics["station_dependency"]`
- `results.network_metrics["network_robustness"]`
- `results.network_metrics["station_placement"]`

Future inputs may include other typed metrics, but they must be added to
this contract before being used by reporting consumers.

The reporting layer must not assume non-existent top-level fields such as:

- `results.station_health`
- `results.coverage_gaps`
- `results.intelligence`

unless those surfaces are explicitly introduced and documented later.

## Report Model

The reporting layer should expose a typed report object.

Recommended implementation location:

- `src/ogn_tool/reporting/models.py`

Recommended object:

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class NetworkEngineeringReport:
    network_status: str
    critical_stations: list[str]
    warning_stations: list[str]
    top_spof_stations: list[dict[str, Any]]
    top_gap_candidates: list[dict[str, Any]]
    top_redundancy_priorities: list[dict[str, Any]]
    top_station_addition_candidates: list[dict[str, Any]]
    summary_notes: list[str]
```

The exact field set may evolve, but changes to the public report surface
must be documented here.

## Builder Module

Recommended implementation location:

- `src/ogn_tool/reporting/network_engineering_report.py`

Recommended API:

```python
def build_network_engineering_report(results) -> NetworkEngineeringReport:
    ...
```

The builder must:

- consume typed result surfaces only
- assemble a stable operator-facing report
- avoid recomputing analytical signals
- remain deterministic and easy to serialize

## Initial Report Contents

The first report version should summarize at least:

- network status
- critical stations
- warning stations
- top SPOF stations
- top coverage gap candidates
- top redundancy priorities
- top station addition candidates
- summary notes

This should be enough to answer the core operator question:

- what is the current network state and what should be done next?

## Non-Goals

The reporting layer must not:

- recompute RF propagation or network metrics
- rebuild network graphs from raw observations
- read UI state or `ctx[...]`
- implement visualization logic
- replace the analytical kernel

## Change Policy

Changes to the report contract are considered important product-surface
changes.

Examples of changes that must be documented here:

- renaming report fields
- removing report sections
- changing the meaning of a report section
- switching a report field from list to table/dict or vice versa

## Implementation Sequence

Recommended sequence:

1. define this report contract
2. add `src/ogn_tool/reporting/models.py`
3. add `src/ogn_tool/reporting/network_engineering_report.py`
4. add tests for report assembly
5. only then expose JSON export or UI/report views

## Rule Of Separation

Reporting assembles.
Analysis computes.
UI displays.

This separation must remain stable.
