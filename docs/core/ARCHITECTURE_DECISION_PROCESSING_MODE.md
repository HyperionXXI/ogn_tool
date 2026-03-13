# ADR — Processing Mode

Status: accepted
Date: 2026-03-13

## Context

The OGN RF analysis engine must support both historical analysis and
future real-time monitoring.

The current codebase processes packet windows and produces analytical
snapshots consumed by the UI.

Streaming components exist but are not yet mature enough to serve as
the canonical execution mode.

## Decision

The canonical processing mode of the system is **batch / snapshot**.

The analysis kernel operates on a finite dataset snapshot:

raw_packets
→ RFObservationVector
→ RFAnalysisDataset
→ RFAnalysisEngine
→ RFAnalysisResults
→ NetworkGraph

Streaming support is treated as an **adapter layer** that produces
snapshots compatible with the canonical batch engine.

## Kernel contracts

Canonical input:
- `RFObservationVector`
- `RFAnalysisDataset`

Canonical output:
- `RFAnalysisResults`
- `NetworkGraph`

## Adapters

Streaming adapter:
- `analysis/rf_state_engine.py`

Graph persistence:
- `storage/network_graph_store.py`

Future service:
- `services/stream_snapshot_builder.py`

## Consequences

Advantages:
- deterministic analysis
- reproducible tests
- stable UI snapshots
- simpler architecture

Tradeoffs:
- real-time updates require snapshot generation
- incremental updates are handled outside the kernel
