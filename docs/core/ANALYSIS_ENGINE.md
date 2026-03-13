STATUS: explanatory
REFERENCE: docs/architecture/ADR-001-project-vision.md

# Analysis Engine

This document describes the current analysis-engine structure at a high
level.

For canonical contracts and architecture rules, see:
- `docs/architecture/RF_METRIC_CONTRACT.md`
- `docs/architecture/RUNTIME_API_MIGRATION.md`
- `docs/core/SYSTEM_ARCHITECTURE.md`

## RF Intelligence Pipeline

The analysis engine processes raw observations into typed analytical
outputs.

```text
Raw packets / receptions
  ↓
Normalization
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
  ↓
Reporting / UI
```

## Analysis Module Types

### Pipeline stages
- `RFCoverageStage`
- `VisibilityModelStage`
- `BlindZoneDetectionStage`
- `RFDiagnosticsStage`

### Analysis domains
- `src/ogn_tool/analysis/normalization/`
- `src/ogn_tool/analysis/rf_metrics/`
- `src/ogn_tool/analysis/rf_models/`
- `src/ogn_tool/analysis/network_metrics/`
- `src/ogn_tool/analysis/network_graph/`
- `src/ogn_tool/analysis/intelligence/`

## Engine structure

The core engine is `src/ogn_tool/engine/rf_engine.py`.

It:
- builds typed analytical datasets
- executes RF stages
- runs network graph orchestration
- exposes typed results for runtime and UI consumers

The engine remains separate from UI components.

## RF Analysis Levels

### L0 Transport
- APRS / OGN packets

### L1 RF events
- RF receptions per station

### L2 Aircraft states
- unique aircraft positions extracted from observations

### L3 RF observations
- geometry derived from aircraft position vs station

### L4 Station diagnostics
- coverage, range, shadow zones, antenna diagnostics

### L5 Network intelligence
- overlap, redundancy, robustness, placement, dependency

### L6 Reporting / operator diagnostics
- operator-facing summaries and engineering reports

## Dependency Architecture

```text
models
  ↓
analysis
  ↓
pipeline
  ↓
engine
  ↓
runtime / services
  ↓
UI
```

No reverse dependency is allowed.

## Current status

The analysis engine is now centered on:
- typed contracts in `src/ogn_tool/models/`
- canonical analytics in `src/ogn_tool/analysis/`
- orchestration in `src/ogn_tool/pipeline/`
- typed runtime consumption through `results.*`

This document is explanatory only and should not be treated as a
contract source.
