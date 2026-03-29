# Module Review

## Scope
Modules flagged by the structural audit: `dead_candidate`, `overlap`, `active_with_cycle`, `structural_placeholder`.

| Module | Audit Flags | Decision | Rationale |
|---|---|---|---|
| `ogn_tool.analysis.antenna_health` | dead_candidate, overlap | **delete** | Wrapper overlap with experimental implementation; no incoming usage. |
| `ogn_tool.analysis.experimental.antenna_health` | dead_candidate, overlap | **merge** | Fold into one stable antenna-health module. |
| `ogn_tool.analysis.experimental.azimuth` | dead_candidate, overlap | **merge** | Unify with `ogn_tool.rf.azimuth` to avoid dual azimuth stacks. |
| `ogn_tool.analysis.experimental.shadow` | dead_candidate, overlap | **merge** | Unify with `ogn_tool.analysis.shadow`. |
| `ogn_tool.analysis.geo.geo` | dead_candidate, overlap | **merge** | Duplicate naming under same package (`geo.geo`). |
| `ogn_tool.analysis.geo.grid_loader` | dead_candidate | **deprecate** | No incoming usage; keep for one release window then remove. |
| `ogn_tool.analysis.intelligence.rf_coverage_map` | dead_candidate | **deprecate** | Not referenced by pipeline/apps/tests. |
| `ogn_tool.analysis.network.station_compare` | dead_candidate | **deprecate** | Unused network helper module. |
| `ogn_tool.analysis.network.station_quality` | dead_candidate | **deprecate** | Unused network helper module. |
| `ogn_tool.analysis.network.station_range` | dead_candidate | **deprecate** | Unused network helper module. |
| `ogn_tool.analysis.network_graph.network_optimization` | dead_candidate | **deprecate** | No active call path. |
| `ogn_tool.analysis.network_metrics.network_robustness` | dead_candidate | **deprecate** | No active call path. |
| `ogn_tool.analysis.network_metrics.station_anomaly` | dead_candidate | **deprecate** | No active call path. |
| `ogn_tool.analysis.network_metrics.station_influence` | dead_candidate | **deprecate** | No active call path. |
| `ogn_tool.analysis.network_metrics.visibility` | dead_candidate | **merge** | Consolidate into active network-metrics assembly path. |
| `ogn_tool.analysis.normalization.aircraft_states` | dead_candidate | **merge** | Overlap with engine-side observation/dataset build path. |
| `ogn_tool.analysis.normalization.observation_builder` | dead_candidate, overlap | **merge** | Consolidate with `ogn_tool.engine.observation_builder`. |
| `ogn_tool.analysis.normalization.observation_rows` | dead_candidate | **deprecate** | No active call path in pipeline/apps/tests. |
| `ogn_tool.analysis.normalization.rf_normalization` | dead_candidate | **deprecate** | Keep compatibility flags; phase out after downstream verification. |
| `ogn_tool.analysis.polar` | dead_candidate | **delete** | Unused utility module. |
| `ogn_tool.analysis.rf_dataset_builder` | dead_candidate, overlap | **merge** | Consolidate with `ogn_tool.engine.rf_dataset_builder`. |
| `ogn_tool.analysis.rf_diagnosis` | dead_candidate | **deprecate** | No active incoming usage. |
| `ogn_tool.analysis.rf_kernel.spatial_index` | dead_candidate | **deprecate** | Not referenced by active pipeline path. |
| `ogn_tool.analysis.rf_models.altitude_distance` | dead_candidate | **deprecate** | No active incoming usage. |
| `ogn_tool.analysis.rf_models.radio_horizon` | dead_candidate | **deprecate** | No active incoming usage. |
| `ogn_tool.analysis.rf_models.terrain` | dead_candidate | **deprecate** | No active incoming usage. |
| `ogn_tool.analysis.rf_models.terrain_visibility` | dead_candidate | **deprecate** | No active incoming usage. |
| `ogn_tool.analysis.rf_observations` | dead_candidate | **deprecate** | No incoming imports in static graph. |
| `ogn_tool.analytics.spatial.directional_analysis` | dead_candidate | **move** | Either move into active `analysis.spatial` or delete if superseded. |
| `ogn_tool.data.stations_repository` | dead_candidate | **deprecate** | Repository exists but unused in active flow. |
| `ogn_tool.db` | dead_candidate | **delete** | Legacy facade not used by current call paths. |
| `ogn_tool.domain.observation_contract` | dead_candidate | **merge** | Unify contract ownership under active dataset/result contracts. |
| `ogn_tool.domain.rf_observation` | dead_candidate | **deprecate** | No active incoming imports. |
| `ogn_tool.engine.network_graph_engine` | dead_candidate | **deprecate** | Parallel engine not used by active pipeline. |
| `ogn_tool.engine.observation_builder` | dead_candidate, overlap | **keep** | Preferred target to absorb duplicate observation-builder logic. |
| `ogn_tool.engine.results` | dead_candidate | **deprecate** | Unused engine helper module. |
| `ogn_tool.engine.station_registry` | dead_candidate | **delete** | Unused and isolated. |
| `ogn_tool.models.network_graph_model` | dead_candidate | **deprecate** | No active incoming imports in static graph. |
| `ogn_tool.models.rf.rf_model_adapter` | dead_candidate | **deprecate** | No active incoming imports. |
| `ogn_tool.models.rf_types` | dead_candidate | **deprecate** | No active incoming imports. |
| `ogn_tool.models.spatial_view_model` | dead_candidate | **deprecate** | No active incoming imports in graph. |
| `ogn_tool.pipeline.rf_analysis_service` | dead_candidate | **move** | Move/replace with `services` facade if retained. |
| `ogn_tool.rf.azimuth` | dead_candidate, overlap | **keep** | Retain as canonical azimuth utility; merge experimental variant into this. |
| `ogn_tool.rf.geometry` | dead_candidate | **keep** | Core geometry primitive module; likely foundational despite low static in-degree. |
| `ogn_tool.rf.propagation` | dead_candidate | **deprecate** | No active call path detected. |
| `ogn_tool.rf.signal_distance` | dead_candidate | **deprecate** | No active call path detected. |
| `ogn_tool.rf_analysis` | dead_candidate | **delete** | Legacy compatibility module, not on active path. |
| `ogn_tool.runtime.rf_runtime` | dead_candidate | **deprecate** | Runtime facade not used by pipeline/apps/tests. |
| `ogn_tool.storage.network_graph_store` | dead_candidate | **deprecate** | Storage adapter not used by active path. |
| `ogn_tool.models.analysis_run` | overlap | **keep** | Model object remains valid contract; naming overlaps pipeline stage only. |
| `ogn_tool.pipeline.analysis_run` | overlap | **keep** | Orchestration stage; keep as pipeline use-case entrypoint. |
| `ogn_tool.analysis.geo` | overlap | **keep** | Package root is canonical; collapse `geo.geo` into it later. |
| `ogn_tool.analysis.shadow` | overlap | **keep** | Keep as canonical shadow computation surface. |
| `ogn_tool.engine.rf_dataset_builder` | overlap | **keep** | Preferred active dataset builder in engine layer. |
| `ogn_tool.reporting.network_engineering_report` | active_with_cycle | **merge** | Break cycle by collapsing builder/report dependency direction. |
| `ogn_tool.reporting.network_engineering_report_builder` | active_with_cycle | **merge** | Break cycle by extracting interfaces or one-way dependency. |
| `ogn_tool.services` | structural_placeholder | **keep** | Reserve as public service boundary; currently placeholder namespace. |
