# Import Graph Audit

Date: 2026-03-12

Scope:
- `src/ogn_tool`
- supporting references from `apps`, `scripts`, `tests`

Method:
- `pydeps src/ogn_tool --max-bacon=3 --show-cycles --show-deps --noshow`
- `vulture src/ogn_tool --min-confidence 90`
- `vulture src/ogn_tool --min-confidence 100`
- repository-wide import scan with `rg`
- `lint-imports`

## Summary

Current state:
- No blocking import cycle detected by `pydeps`.
- `lint-imports` passes (`Architecture KEPT`).
- `vulture` reports no high-confidence dead code.
- The main issue is not dead code but structural duplication and legacy compatibility wrappers.

## Core Modules

These modules form the active architecture.

| Module | Layer | Role |
|---|---|---|
| `ogn_tool.engine.rf_engine` | engine | Main RF engine orchestrator |
| `ogn_tool.engine.rf_dataset_builder` | engine | Builds canonical RF dataset inputs |
| `ogn_tool.engine.rf_pipeline_executor` | engine | Executes RF pipeline |
| `ogn_tool.pipeline.rf_analysis_pipeline` | pipeline | Canonical RF analysis pipeline |
| `ogn_tool.pipeline.rf_stages` | pipeline | RF pipeline stages |
| `ogn_tool.pipeline.network_graph_stage` | pipeline | Network intelligence stage wrapper |
| `ogn_tool.models.rf_analysis_dataset` | models | Typed RF dataset contract |
| `ogn_tool.models.rf_analysis_results` | models | Typed RF result contract |
| `ogn_tool.models.rf_observation_vector` | models | Canonical RF observation vector |
| `ogn_tool.analysis.rf_normalization` | analysis | Packet/reception normalization |
| `ogn_tool.analysis.observation_builder` | analysis | Shared observation payload builder |
| `ogn_tool.analysis.aircraft_states` | analysis | Aircraft state extraction |
| `ogn_tool.analysis.rf_feature_matrix` | analysis | Feature matrix generation |
| `ogn_tool.analysis.rf_probability_field` | analysis | RF probability / coverage field |
| `ogn_tool.analysis.network_graph.rf_graph_builder` | analysis | RF graph construction |
| `ogn_tool.analysis.network_graph.network_metrics` | analysis | Network graph metrics |
| `ogn_tool.analysis.network_graph.network_timeseries` | analysis | Network timeseries |
| `ogn_tool.analysis.network_graph.network_events` | analysis | Network event detection |
| `ogn_tool.engine.network_graph_engine` | engine | Graph engine facade |
| `ogn_tool.storage.network_graph_store` | storage | Incremental graph persistence |
| `ogn_tool.rf.geometry` | rf | Low-level RF geometry |
| `ogn_tool.rf.azimuth` | rf | Low-level azimuth primitives |
| `ogn_tool.rf.signal_distance` | rf | Low-level signal/distance primitives |
| `ogn_tool.rf.propagation` | rf | Low-level propagation primitives |

## Legacy Wrappers

These modules are still importable and therefore not dead, but they are compatibility paths rather than canonical implementations.

| Module | Redirects to / overlaps with | Recommendation |
|---|---|---|
| `ogn_tool.rf_probability_field` | `ogn_tool.analysis.rf_probability_field` | Remove after import migration |
| `ogn_tool.intelligence.__init__` | `ogn_tool.analysis.intelligence.rf_coverage_map` | Remove after external imports migrate |
| `ogn_tool.analysis.radio_horizon` | `ogn_tool.analysis.rf_models.radio_horizon` | Remove wrapper eventually |
| `ogn_tool.analysis.terrain` | `ogn_tool.analysis.rf_models.terrain` | Remove wrapper eventually |
| `ogn_tool.analysis.terrain_visibility` | `ogn_tool.analysis.rf_models.terrain_visibility` | Remove wrapper eventually |
| `ogn_tool.analysis.rf_visibility_model` | `ogn_tool.analysis.rf_models.rf_visibility_model` | Remove wrapper eventually |
| `ogn_tool.analysis.altitude_distance` | `ogn_tool.analysis.rf_models.altitude_distance` | Remove wrapper eventually |
| `ogn_tool.analysis.grid` | `ogn_tool.analysis.geo.grid` | Remove wrapper eventually |
| `ogn_tool.analysis.grid_loader` | `ogn_tool.analysis.geo.grid_loader` | Remove wrapper eventually |

## Low-Usage / Transitional Modules

These modules are not dead, but they are transitional or only lightly integrated in the current runtime.

| Module | Current status | Recommendation |
|---|---|---|
| `ogn_tool.engine.rf_engine_dataset_builder` | Transitional legacy dataset builder | Merge or retire |
| `ogn_tool.engine.rf_engine_observations` | Transitional observation adapter | Merge or retire |
| `ogn_tool.engine.rf_engine_network` | Transitional network dataframe logic | Consolidate with graph engine |
| `ogn_tool.engine.observation_builder` | Duplicate observation concept | Remove or merge |
| `ogn_tool.engine.results` | Legacy result container | Remove if no external dependency remains |
| `ogn_tool.analysis.network.network_intelligence` | Older network dataframe analysis | Clarify against graph architecture |
| `ogn_tool.analysis.network_analysis` | Legacy network analysis helpers | Clarify or retire |
| `ogn_tool.analysis.rf_state_engine` | Alternative streaming runtime | Decide canonical vs experimental |
| `ogn_tool.analysis.network_graph.network_optimization` | New module, low runtime integration | Integrate or mark experimental |
| `ogn_tool.analysis.intelligence.station_planner` | New module, low runtime integration | Integrate more deeply or mark experimental |
| `ogn_tool.storage.network_graph_store` | New persistence layer, not central yet | Integrate or keep optional |

## Structural Problems Revealed By Import Audit

### 1. UI duplication

Two UI trees still exist:
- `apps/ui/*`
- `src/ogn_tool/ui/*`

This is not an import-cycle problem, but it is a major structural ambiguity.

### 2. Dual network model

Two network analysis systems coexist:
- dataframe/network-style modules in `analysis/network/*`
- graph/network-style modules in `analysis/network_graph/*`

This increases conceptual overlap and makes the architecture harder to explain.

### 3. Transitional engine split not fully complete

The engine has been split successfully, but multiple engine-side support modules still overlap in purpose:
- `rf_dataset_builder`
- `rf_engine_dataset_builder`
- `rf_engine_observations`
- `rf_engine_network`
- `observation_builder`

### 4. Legacy compatibility kept alive by imports

`vulture` reports no dead code at high confidence largely because many wrappers are still imported, directly or indirectly.

## Cycles

Results:
- `pydeps` did not report a blocking cycle in `src/ogn_tool`.
- `lint-imports` passes.

Interpretation:
- The import architecture is currently stable enough.
- The next cleanup phase should focus on duplication and compatibility removal rather than cycle repair.

## Dead Code Findings

Results:
- `vulture --min-confidence 90`: no findings
- `vulture --min-confidence 100`: no findings

Interpretation:
- No obvious dead module remains in `src/ogn_tool` at high confidence.
- The repo’s complexity now comes more from structural overlap than from unused code.

## Simplification Order

Recommended cleanup order:

1. Choose a single canonical UI tree.
   - Keep either `apps/ui` or `src/ogn_tool/ui` as the source of truth.

2. Remove legacy wrapper imports.
   - Especially wrapper modules under `src/ogn_tool/analysis/*` and root aliases like `src/ogn_tool/rf_probability_field.py`.

3. Consolidate network analysis.
   - Decide whether `analysis/network/*` remains distinct from `analysis/network_graph/*`.

4. Finish engine cleanup.
   - Reduce the number of engine-side helper modules with overlapping roles.

5. Re-run import audit after each cleanup phase.
   - `lint-imports`
   - `pydeps`
   - `vulture`

## Practical Conclusion

The project is no longer suffering from obvious import cycles or dead code.

The architecture risk now is:
- duplicate structure
- legacy wrappers
- parallel module families
- ambiguous source-of-truth paths

The next cleanup should therefore target simplification, not rescue.
