# PROJECT_STATE

Date: 2026-03-12
Branch: main
Scope: repository-wide architectural snapshot

## ACTIVE ARCHITECTURE

### Engine Core (active)
- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/pipeline/rf_analysis_pipeline.py`
- `src/ogn_tool/pipeline/rf_stages.py`
- `src/ogn_tool/models/rf_analysis_dataset.py`
- `src/ogn_tool/models/rf_analysis_results.py`
- `src/ogn_tool/models/rf_observation_vector.py`

### Analysis Layer (active)
- `src/ogn_tool/analysis/rf_feature_matrix.py`
- `src/ogn_tool/analysis/rf_visibility_model.py`
- `src/ogn_tool/analysis/rf_blind_zone_detection.py`
- `src/ogn_tool/analysis/rf_antenna_pattern.py`
- `src/ogn_tool/analysis/observation_pipeline.py`

### RF Primitives (active)
- `src/ogn_tool/rf/geometry.py`
- `src/ogn_tool/rf/azimuth.py`
- `src/ogn_tool/rf/signal_distance.py`
- `src/ogn_tool/rf/propagation.py`

### Network Intelligence (active)
- `src/ogn_tool/network/network_intelligence.py`
- `src/ogn_tool/network/station_range.py`
- `src/ogn_tool/network/station_quality.py`
- `src/ogn_tool/network/station_compare.py`

### UI Runtime (active)
- `apps/dashboard.py`
- `apps/ui/pages/*`
- `apps/ui/sections.py`

## SUPPORT LAYERS

### Services (partially active)
- `src/ogn_tool/services/data_service.py`
- `src/ogn_tool/services/rf_analysis_service.py`
- `src/ogn_tool/services/rf_analysis_pipeline.py`

### Data Access (active)
- `src/ogn_tool/data/db_repository.py`
- `src/ogn_tool/data/packets_repository.py`
- `src/ogn_tool/data/receptions_repository.py`
- `src/ogn_tool/data/stations_repository.py`

### Scripts / Tests / Benchmarks (active)
- `scripts/run_rf_analysis.py`
- `scripts/run_network_analysis.py`
- `tests/*` (contract + pipeline + architecture checks)
- `benchmarks/*` (RF state engine performance)

## LEGACY / TRANSITION

### Legacy module paths (moved or removed)
- `src/ogn_tool/analysis/azimuth.py` -> moved to `src/ogn_tool/rf/azimuth.py`
- `src/ogn_tool/analysis/signal_distance.py` -> moved to `src/ogn_tool/rf/signal_distance.py`
- `src/ogn_tool/analysis/station_range.py` -> moved to `src/ogn_tool/network/station_range.py`
- `src/ogn_tool/analysis/station_quality.py` -> moved to `src/ogn_tool/network/station_quality.py`
- `src/ogn_tool/analysis/station_compare.py` -> moved to `src/ogn_tool/network/station_compare.py`

### Transitional behavior still present
- UI pages still read `ctx["dataset"]` / `dataset.get(...)` directly.
- Engine still exposes compatibility surfaces for legacy callers.

## CURRENT MIGRATION STATUS

- PR1 Pipeline stabilization: done
- PR2 Engine API stabilization (`run(dataset) -> RFAnalysisResults`): done
- PR2.5 Repository stabilization: in progress
- PR3 UI contract (`UIAnalysisView`) and page-by-page migration: pending

## NEXT FOCUS (SHORT TERM)

1. Introduce `UIAnalysisView` under `src/ogn_tool/ui/view_models/`.
2. Migrate one UI page at a time away from direct `dataset.get(...)` usage.
3. Remove remaining legacy compatibility fields after UI migration is complete.
