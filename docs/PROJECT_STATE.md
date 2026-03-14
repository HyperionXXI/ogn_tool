# PROJECT_STATE

Date: 2026-03-14
Branch: main
Scope: repository-wide architectural snapshot
Status: transitional snapshot, not canonical source of truth

Canonical governance documents:
- `docs/architecture/ADR-001-project-vision.md`
- `docs/architecture/REPOSITORY_CLASSIFICATION.md`
- `docs/architecture/ENGINE_RULES.md`

## ACTIVE ARCHITECTURE

### Core typed contracts
- `src/ogn_tool/models/rf_analysis_dataset.py`
- `src/ogn_tool/models/rf_analysis_results.py`
- `src/ogn_tool/models/rf_observation_vector.py`
- `src/ogn_tool/models/network_graph_model.py`

### Analysis layer
- `src/ogn_tool/analysis/normalization/`
- `src/ogn_tool/analysis/observation_schema.py`
- `src/ogn_tool/analysis/observation_views.py`
- `src/ogn_tool/analysis/rf_metrics/`
- `src/ogn_tool/analysis/rf_models/`
- `src/ogn_tool/analysis/network_metrics/`
- `src/ogn_tool/analysis/network_metric_registry.py`
- `src/ogn_tool/analysis/network_metric_views.py`
- `src/ogn_tool/analysis/network_graph/`
- `src/ogn_tool/analysis/intelligence/`

### Intelligence layer (active)
- `station_health.py`
- `network_summary.py`
- `station_dependency.py`
- `station_dominance.py`
- `network_redundancy_score.py`
- `network_confidence.py`
- `coherence.py`
- `station_removal_simulation.py`
- `station_redundancy_planner.py`
- `network_single_point_of_failure_detector.py`
- `coverage_gap_detector.py`
- `coverage_gap_prioritizer.py`
- `station_addition_simulation.py`

### Pipeline layer
- `src/ogn_tool/pipeline/rf_analysis_pipeline.py`
- `src/ogn_tool/pipeline/rf_stages.py`
- `src/ogn_tool/pipeline/network_graph_stage.py`

### Engine / runtime layer
- `src/ogn_tool/engine/rf_engine.py`
- `src/ogn_tool/runtime/`
- `src/ogn_tool/services/rf_analysis_service.py`

### Reporting layer
- `src/ogn_tool/reporting/network_engineering_report.py`
- `src/ogn_tool/reporting/report_builder.py`

### UI layer
- `apps/dashboard.py`
- `apps/ui/pages/`
- `apps/ui/view_models/`
- `apps/ui/map_engine/`

## CURRENT STABLE MILESTONES

- `v0.4-network-intelligence`
- `v0.5-network-diagnostics`
- `v0.6-network-engineering`
- `v0.7-spof-detection`
- `v0.8-coverage-gap-analysis`
- `v0.9-station-addition-simulation`
- `v1.0-network-reporting-foundation`

## KNOWN TRANSITIONAL AREAS

- `src/ogn_tool/engine/rf_engine_dataset_builder.py`
- `src/ogn_tool/engine/rf_dataset_builder.py`
- `src/ogn_tool/engine/rf_engine_network.py`
- some UI/runtime compatibility paths still reading `ctx[...]`

## RECOMMENDED USE OF THIS DOCUMENT

Use this file as a dated snapshot only.

Do not use it as the primary source of truth for:
- contracts
- architecture rules
- repository classification
- runtime migration policy
