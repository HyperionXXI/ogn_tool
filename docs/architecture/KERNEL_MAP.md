# Engine Kernel Map

## Facade Entrypoints

### `src/ogn_tool/engine/network_graph_analysis_facade.py`
- `assemble_network_intelligence`
- `assemble_network_metrics`
- `build_rf_graph`
- `build_shadow_observation_frame`
- `build_spatial_observation_frame`
- `check_intelligence_coherence`
- `collect_network_metric_warnings`
- `compute_graph_metrics`
- `compute_network_evolution_metrics`
- `compute_optimal_station_locations`
- `compute_shadow_risk_scores`
- `compute_station_angular_entropy`
- `compute_temporal_observability`
- `detect_coverage_gaps`
- `detect_single_points_of_failure`
- `network_confidence_level`
- `network_events`
- `network_redundancy_level`
- `network_timeseries`
- `plan_redundancy_improvements`
- `prioritize_coverage_gaps`
- `simulate_station_addition`
- `station_dependency_level`
- `suggest_station_locations`
- `validate_network_metrics`

### `src/ogn_tool/engine/rf_analysis_facade.py`
- `build_feature_matrix`
- `build_rf_probability_grid`
- `compute_network_blind_zones`
- `compute_station_quality`
- `compute_station_range`
- `estimate_antenna_pattern`
- `detect_shadow_sectors`
- `evaluate_rf_diagnosis`
- `aggregate_signal_quality`

Backward compatibility aliases kept:
- `analysis_station_quality`
- `analysis_station_range`
- `build_rf_probability_field`
- `detect_network_blind_zones`

### `src/ogn_tool/engine/multi_station_intelligence_facade.py`
- `build_candidate_station_aircraft_sets`
- `build_station_addition_evaluations`
- `evaluate_multi_station_coverage`
- `select_stations_lazy_greedy`

## Internal Canonical Modules

### `src/ogn_tool/engine/network_metrics_kernel.py`
Canonical entrypoint for network metric assembly helpers:
- build and enrich coverage metrics
- radio/station event transformations
- blind zone / overlap computations

### `src/ogn_tool/engine/rf_observation_kernel.py`
Canonical entrypoint for RF observation geometry helpers:
- RF dataset build
- packet distance/bearing
- observation row conversion

## Internal Flow
1. Packet rows are normalized and converted to observation events (`rf_dataset_builder` + `rf_observation_kernel`).
2. RF derived surfaces are built (`rf_analysis_facade`): feature matrix, probability grid, shadow sectors, blind zones.
3. Network graph metrics are assembled (`network_graph_analysis_facade` + `network_metrics_kernel`).
4. Multi-station scenarios use `multi_station_intelligence_facade` for candidate support and greedy planning.
5. Engine runtime composes outputs in `rf_engine` and `rf_engine_dataset_builder` without direct pipeline/reporting/runtime coupling.

## Duplicate Concepts Consolidated in Engine
- RF/network metric helper imports centralized via `network_metrics_kernel`.
- RF dataset/geometry helper imports centralized via `rf_observation_kernel`.
- RF diagnostic/statistics helper imports centralized via `rf_analysis_facade`.

## Canonical Kernel Surface (engine-only)
- `network_graph_analysis_facade`
- `rf_analysis_facade`
- `multi_station_intelligence_facade`
- `network_metrics_kernel`
- `rf_observation_kernel`
