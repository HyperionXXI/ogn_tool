# RF Analysis Architecture

## 1. System Overview

The RF analysis engine follows a layered, observation-centric flow:

Packets
→ Data access
→ Observation pipeline
→ RFAnalysisDataset
→ RFAnalysisPipeline
→ Stages
→ Metrics / Diagnostics
→ NetworkGraph
→ Engine outputs
→ Services
→ UI

At runtime, raw packet inputs are loaded through repository/data access modules, transformed into structured RF observations, enriched through pipeline stages, and exposed as stable outputs for UI consumption.

## 2. Core Data Models

### RFObservationVector

`RFObservationVector` is the canonical observation unit used by the pipeline.
It represents one station-aircraft RF observation with geometry-aware attributes (distance, bearing, horizon context).

Role:
- normalized input unit for RF analytics
- decouples low-level packet shape from analysis logic
- enables vectorized stage processing

### RFAnalysisDataset

`RFAnalysisDataset` is the canonical container passed between pipeline stages.
It carries:
- input observations
- intermediate products (feature matrix, coverage, visibility, blind zones, antenna pattern)
- final diagnostics/metrics

Role:
- single source of truth across stages
- explicit contract between engine and pipeline
- stable handoff object for service/UI layers

### NetworkGraph

`NetworkGraph` is the canonical typed container for RF network topology.
It is defined in:
- `src/ogn_tool/models/network_graph_model.py`

It contains:
- `nodes: list[NetworkNode]`
- `edges: list[NetworkEdge]`
- `metrics: dict`

Role:
- formalize RF network topology as a first-class model
- provide a stable contract for graph analytics, storage and engine outputs
- avoid ad hoc graph dictionaries as the long-term architecture

Important compatibility rule:
- `NetworkGraph` remains mapping-friendly for current callers.
- Existing usage still works:
  - `graph.get("nodes")`
  - `"nodes" in graph`
  - `graph["edges"]`

### NetworkNode

Represents a graph node.

Current node types:
- `station`
- `aircraft`
- `grid_cell`

Fields:
- `id`
- `type`
- `lat`
- `lon`
- `altitude`
- `attributes`

Note:
- `lat` / `lon` remain optional by design.
- This preserves compatibility with current code paths where some nodes are not fully geo-populated yet.

### NetworkEdge

Represents a graph relation.

Fields:
- `source`
- `target`
- `relation`
- `weight`
- `attributes`

Current edge relations:
- `reception`
- `coverage`

Future relation types may include:
- `overlap`
- routing/topology relations

## 3. RF Analysis Pipeline

Pipeline stage order:

1. `FeatureMatrixStage`
2. `RFCoverageStage`
3. `VisibilityModelStage`
4. `BlindZoneDetectionStage`
5. `AntennaPatternStage`
6. `RFDiagnosticsStage`
7. `network_graph_stage` (complementary network intelligence stage)

Each stage declares `requires` and `produces` to support pipeline validation.

### FeatureMatrixStage
- inputs (`requires`): `observations`
- outputs (`produces`): `feature_matrix`
- purpose: convert observation vectors to numerical arrays used by downstream RF analysis.

### RFCoverageStage
- inputs (`requires`): `feature_matrix`
- outputs (`produces`): `coverage`
- purpose: estimate directional/distance RF coverage products from observation-derived data.

### VisibilityModelStage
- inputs (`requires`): `coverage`
- outputs (`produces`): `visibility`
- purpose: derive station visibility and propagation-oriented summary metrics.

### BlindZoneDetectionStage
- inputs (`requires`): `visibility`
- outputs (`produces`): `blind_zones`
- purpose: identify weak/under-covered regions using coverage/visibility outputs.

### AntennaPatternStage
- inputs (`requires`): `feature_matrix`
- outputs (`produces`): `antenna_pattern`, `antenna_shadow_sectors`
- purpose: estimate azimuthal reception behavior and detect potential directional shadow sectors.

### RFDiagnosticsStage
- inputs (`requires`): `coverage`, `visibility`
- outputs (`produces`): `metrics`
- purpose: aggregate model outputs into final diagnostics and engine-facing metrics.

### network_graph_stage
- inputs: observation payload, coverage outputs, previous graph (optional)
- outputs: `network_graph`, `network_metrics`, `network_timeseries`, `network_events`, `network_evolution`, `station_suggestions`
- purpose: build and analyze RF network topology as a graph-oriented layer on top of RF observations

## 4. RF Computation Layer

Low-level RF primitives are located under `ogn_tool.rf`:

- `geometry`
- `azimuth`
- `signal_distance`
- `propagation`

Responsibility:
- provide foundational RF geometry/propagation operations
- remain reusable and independent of high-level analysis orchestration

These modules are treated as primitive utilities for higher analysis stages.

## 5. Analysis Layer

Analytical modules transform observations into domain metrics:

- `rf_feature_matrix`: vectorized feature extraction from observations
- `rf_blind_zone_detection`: blind-zone inference from observation-derived distributions
- `rf_antenna_pattern`: directional reception probability and shadow-sector estimation
- `rf_metrics`: shared RF metric summarization helpers

RF model modules are now grouped under:
- `ogn_tool.analysis.rf_models`
  - `radio_horizon`
  - `altitude_distance`
  - `terrain`
  - `terrain_visibility`
  - `rf_visibility_model`

Network analytics are split by concern:
- `ogn_tool.analysis.network_metrics`
  - tabular/statistical network metrics
  - station metrics
  - coverage metrics
  - redundancy and blind-zone metrics
- `ogn_tool.analysis.network_graph`
  - graph construction
  - connectivity/topology metrics
  - time series and events
  - network optimization helpers

Network intelligence helpers are grouped under:
- `ogn_tool.analysis.intelligence`
  - `rf_coverage_map`
  - `station_planner`

Responsibility:
- implement RF and network analysis logic
- consume normalized observation-level inputs
- produce analysis outputs for pipeline stages and engine integration

### Observation Pipeline Boundary

`ogn_tool.analysis.observation_builder` is the normalization boundary between packet-shaped rows and analysis-ready observation vectors/payloads.

Responsibility:
- transform packet-level data to `RFObservationVector`
- preserve compatibility adapters where required
- provide canonical observation inputs to the engine/pipeline

## 6. Data Access Layer

Data access modules are located under `ogn_tool.data`:

- `packets_repository`
- `receptions_repository`
- `stations_repository`
- `db_repository`

Responsibility:
- load and persist data from/to storage
- encapsulate SQL and DB-specific concerns
- avoid RF analytics logic

This layer provides raw/structured inputs to service and engine orchestration.

## 7. Engine Layer

Primary orchestrators:
- `ogn_tool.engine.rf_engine`
- `ogn_tool.engine.network_graph_engine`

Responsibility:
- build the initial `RFAnalysisDataset`
- execute the `RFAnalysisPipeline`
- build and expose `NetworkGraph` results
- return consolidated analysis results for services/UI

The engine is the runtime integration point between normalized observations, staged analytics, graph intelligence and final outputs.

## 8. Service Layer

Service modules are located under `ogn_tool.services`:

- `data_service`
- `rf_analysis_service`

Responsibility:
- orchestrate application use-cases
- provide stable callable interfaces to UI/API
- bridge data access and engine outputs

Services should not duplicate low-level RF analysis algorithms.

## 9. Storage Layer

Graph persistence lives under `ogn_tool.storage`:

- `network_graph_store`

Responsibility:
- persist `NetworkGraph`
- reload prior graph state
- support incremental graph updates from new observations

This layer is intentionally separated from analysis logic.

## 10. UI Layer

The canonical UI now lives under:
- `apps/ui`
- `apps/dashboard.py`

Responsibility:
- consume engine/service-produced results
- render metrics, maps, diagnostics, and views
- avoid recomputing RF analysis logic in UI code

UI is a presentation layer over analysis results.

## 11. Architectural Rules

- Analysis modules must not import UI modules.
- RF primitive modules must not depend on analysis modules.
- Pipeline stages must declare `requires` / `produces` when they participate in the RF pipeline contract.
- `RFAnalysisDataset` is the canonical dataset contract between pipeline and engine.
- `NetworkGraph` is the canonical graph contract for RF network topology.
- UI should consume service-layer interfaces or engine outputs, not recompute analysis logic.
- Service layer must not implement RF primitive algorithms.
- Data access layer must not contain RF analysis logic.
- Storage must persist typed graph state, not define analysis logic.
