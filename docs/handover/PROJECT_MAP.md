# Project Map (High-Level)

This map summarizes all major repository surfaces for external takeover.

## Top-Level Directories
- `.github/`: CI/workflow config
- `apps/`: runtime entry points (Streamlit + FastAPI + app UI modules)
- `benchmarks/`: performance/load experiments
- `data/`: local datasets and generated run artifacts
- `docs/`: architecture and domain docs
- `experiments/`: non-production exploratory work
- `frontend/`: deck.gl vanilla frontend (served by FastAPI)
- `scripts/`: operational scripts (run generation, quality, validation)
- `src/`: Python package source (`ogn_tool`)
- `tests/`: test suite
- `tools/`: utility scripts

## `src/ogn_tool` Package Map
- `data/`: repositories and DB loading primitives
- `domain/`: schemas/contracts and semantic models
- `intelligence/`: inference and network-level reasoning
- `kernel/`: deterministic RF/network computations
- `models/`: typed model adapters/types
- `pipeline/`: orchestration stages and services
- `reporting/`: report builders, normalizers, views, export
- `runtime/`: runtime execution surfaces
- `services/`: reserved external orchestration layer
- `storage/`: persistence helpers
- `ui/`: adapter/view-model layer

## Operational Entry Points
- `apps/dashboard.py` (Streamlit)
- `apps/api_server.py` (FastAPI + static frontend)
- `scripts/run_quality_gate.py`
- `scripts/rf_stability_table.py`
- `scripts/run_multistation_window.py`

## Critical Artifacts
- Run directory structure: `data/runs/analysis_runs/<run_id>/`
  - `report.json`
  - `run_metadata.json`
  - optional RF artifacts (e.g. `azimuth_distance_surface.json`)

## Current Transition Zone
- UI is functional but only decision-grade when aircraft observation layer is populated.
- Main active gap is data grounding for network intelligence, not rendering.
