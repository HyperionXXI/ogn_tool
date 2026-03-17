
Source of truth: docs/core/SYSTEM_ARCHITECTURE.md

This document describes the current RF and network analysis
architecture.

Primary governance lives in:
- `docs/architecture/ADR-001-project-vision.md`
- `docs/architecture/REPOSITORY_CLASSIFICATION.md`
- `docs/architecture/RF_METRIC_CONTRACT.md`

# RF Architecture

## 1. Architecture Layers

### 1. Data ingestion
Purpose:
- load packet and reception records from SQLite
- apply time-window and station filters

Current implementation:
- `src/ogn_tool/data/packets_repository.py`
- `src/ogn_tool/data/receptions_repository.py`
- `src/ogn_tool/data/db_repository.py`

### 2. RF normalization
Purpose:
- convert heterogeneous packet/reception rows into a stable observation contract
- normalize key fields such as station, aircraft, timestamp, and coordinates

Current implementation:
- `src/ogn_tool/analysis/normalization/rf_normalization.py`
- `src/ogn_tool/analysis/normalization/aircraft_states.py`
- `src/ogn_tool/analysis/normalization/observation_builder.py`
- `src/ogn_tool/analysis/normalization/observation_rows.py`

### 3. RF analysis engine
Purpose:
- build the analysis dataset
- run RF stages and network stage orchestration
- expose typed outputs for downstream consumers

Current implementation:
- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/pipeline/rf_analysis_pipeline.py`
- `src/ogn_tool/pipeline/network_graph_stage.py`

### 4. Network analysis / intelligence
Purpose:
- derive multi-station metrics and graph-level intelligence
- compute overlap, redundancy, robustness, planning, and diagnostics

Current implementation:
- `src/ogn_tool/analysis/network_metrics/`
- `src/ogn_tool/analysis/network_graph/`
- `src/ogn_tool/analysis/intelligence/`

### 5. Reporting and UI
Purpose:
- assemble operator-facing summaries
- render typed outputs for exploration and diagnostics

Current implementation:
- `src/ogn_tool/reporting/`
- `apps/dashboard.py`
- `apps/ui/pages/*`

## 2. Canonical Pipeline

```text
raw packets / receptions
  -> normalization
  -> RFAnalysisDataset
  -> RFAnalysisPipeline
  -> RFAnalysisResults
  -> network metrics / intelligence
  -> reporting / UI
```

## 3. Canonical Engine Container

`RFAnalysisDataset` (`src/ogn_tool/models/rf_analysis_dataset.py`) is the
canonical typed container for engine inputs and staged results.

`RFAnalysisResults` (`src/ogn_tool/models/rf_analysis_results.py`) is the
canonical typed output surface.

## 4. Architecture Violations To Avoid

- UI reading raw packet transport schemas as source of truth
- engine builder modules becoming analytical logic containers
- intelligence modules recomputing RF or network metrics
- reporting modules recalculating analytics instead of assembling them

## 5. RF Analysis Levels

### L0 Transport
- raw APRS / OGN packets

### L1 RF events
- station-level receptions

### L2 Aircraft states
- normalized aircraft positions

### L3 RF observations
- distance, bearing, geometry, context

### L4 Station diagnostics
- coverage, range, pattern, blind zones

### L5 Network intelligence
- overlap, redundancy, robustness, placement, SPOF, gaps

### L6 Reporting
- network engineering report and operator summaries
