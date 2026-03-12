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

## 3. RF Analysis Pipeline

Pipeline stage order:

1. `FeatureMatrixStage`
2. `RFCoverageStage`
3. `VisibilityModelStage`
4. `BlindZoneDetectionStage`
5. `AntennaPatternStage`
6. `RFDiagnosticsStage`

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
- `rf_visibility_model`: horizon/visibility-oriented RF interpretation
- `rf_blind_zone_detection`: blind-zone inference from observation-derived distributions
- `rf_antenna_pattern`: directional reception probability and shadow-sector estimation
- `rf_metrics`: shared RF metric summarization helpers

Responsibility:
- implement RF domain analysis logic
- consume normalized observation-level inputs
- produce analysis outputs for pipeline stages

### Observation Pipeline Boundary

`ogn_tool.analysis.observation_pipeline` is the normalization boundary between packet-shaped rows and analysis-ready observation vectors.

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

Primary orchestrator: `ogn_tool.engine.rf_engine`

Responsibility:
- build the initial `RFAnalysisDataset`
- execute the `RFAnalysisPipeline`
- return consolidated analysis results for services/UI

The engine is the runtime integration point between normalized observations, staged analytics, and final outputs.

## 8. Service Layer

Service modules are located under `ogn_tool.services`:

- `data_service`
- `rf_analysis_service`
- `rf_analysis_pipeline`

Responsibility:
- orchestrate application use-cases
- provide stable callable interfaces to UI/API
- bridge data access and engine outputs

Services should not duplicate low-level RF analysis algorithms.

## 9. UI Layer

UI modules are under `ogn_tool.ui`.

Responsibility:
- consume service/engine-produced results
- render metrics, maps, diagnostics, and views
- avoid recomputing RF analysis logic in UI code

UI is a presentation layer over analysis results.

## 10. Architectural Rules

- Analysis modules must not import UI modules.
- RF primitive modules must not depend on analysis modules.
- Pipeline stages must declare `requires` / `produces`.
- `RFAnalysisDataset` is the canonical dataset contract between pipeline and engine.
- UI should consume service-layer interfaces (target architecture), not bypass contracts.
- Service layer must not implement RF primitive algorithms.
- Data access layer must not contain RF analysis logic.
