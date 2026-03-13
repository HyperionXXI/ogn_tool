STATUS: canonical
SOURCE_OF_TRUTH: docs/core/SYSTEM_ARCHITECTURE.md

This document describes the current runtime and package-layer system
architecture.

The canonical governance rules live in:
- `docs/architecture/ADR-001-project-vision.md`
- `docs/architecture/REPOSITORY_CLASSIFICATION.md`
- `docs/architecture/ENGINE_RULES.md`

# System Architecture

The system follows a layered architecture with a typed analytical core.

```text
data ingestion
  -> data access
  -> analysis
  -> pipeline
  -> engine
  -> runtime/services
  -> UI
```

## Data ingestion

Responsible for:
- APRS / OGN packet collection
- persistence into SQLite
- preserving raw observations and timestamps

Primary implementation:
- `scripts/collector.py`
- `src/ogn_tool/data/db_repository.py`

## Data access

Responsible for:
- loading packet windows
- loading receptions and stations
- schema migration and repository access

Primary implementation:
- `src/ogn_tool/data/packets_repository.py`
- `src/ogn_tool/data/receptions_repository.py`
- `src/ogn_tool/data/stations_repository.py`

## Analysis

Responsible for all analytical computation:
- normalization
- RF models and RF metrics
- network metrics
- network graph
- intelligence layer

Primary implementation:
- `src/ogn_tool/analysis/normalization/`
- `src/ogn_tool/analysis/rf_metrics/`
- `src/ogn_tool/analysis/rf_models/`
- `src/ogn_tool/analysis/network_metrics/`
- `src/ogn_tool/analysis/network_graph/`
- `src/ogn_tool/analysis/intelligence/`

Analysis must not depend on UI or runtime state.

## Pipeline

Responsible for orchestration of analytical stages only.

Primary implementation:
- `src/ogn_tool/pipeline/rf_analysis_pipeline.py`
- `src/ogn_tool/pipeline/rf_stages.py`
- `src/ogn_tool/pipeline/network_graph_stage.py`

Pipeline must not become a second analysis layer.

## Engine

Responsible for execution and compatibility orchestration.

Primary implementation:
- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/engine/rf_pipeline_executor.py`

Transitional builder modules may still exist, but they are not canonical
sources of analytical semantics.

## Runtime and services

Responsible for exposing typed runtime entry points and migration away
from legacy `ctx[...]` consumers.

Primary implementation:
- `src/ogn_tool/runtime/`
- `src/ogn_tool/services/rf_analysis_service.py`

## UI

Responsible only for:
- visualization
- filtering
- sorting
- operator interaction

Primary implementation:
- `apps/dashboard.py`
- `apps/ui/pages/`

UI must not recalculate RF or network metrics.
