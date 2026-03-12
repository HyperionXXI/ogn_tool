# Dead Code Audit

Date: 2026-03-11

Scope:
- src/ogn_tool
- apps
- scripts
- tests
- tools
- benchmarks

Method:
- Static import graph analysis
- `grep`/`rg`-based import scan across repository

## Core modules

These modules are part of the active architecture.

| Module | Layer |
|------|------|
| ogn_tool.engine.rf_engine | engine |
| ogn_tool.pipeline.rf_analysis_pipeline | pipeline |
| ogn_tool.pipeline.rf_stages | pipeline |
| ogn_tool.analysis.rf_feature_matrix | analysis |
| ogn_tool.analysis.rf_visibility_model | analysis |
| ogn_tool.analysis.rf_blind_zone_detection | analysis |
| ogn_tool.analysis.rf_metrics | analysis |
| ogn_tool.analysis.rf_antenna_pattern | analysis |
| ogn_tool.analysis.observation_pipeline | analysis |
| ogn_tool.models.rf_analysis_dataset | models |
| ogn_tool.models.rf_observation_vector | models |
| ogn_tool.rf.geometry | rf |
| ogn_tool.rf.azimuth | rf |
| ogn_tool.rf.signal_distance | rf |
| ogn_tool.rf.propagation | rf |

These modules constitute the RF analysis engine.

## Experimental modules

These modules are prototypes or research experiments.

| Module | Notes |
|------|------|
| ogn_tool.analysis.experimental.antenna_health | prototype RF health scoring |
| ogn_tool.analysis.experimental.azimuth | azimuth experiments |
| ogn_tool.analysis.experimental.shadow | early shadow detection model |

Recommendation:
- keep them under `analysis/experimental/`

## Benchmark modules

Used only by performance tests.

| Module | Importers |
|------|------|
| ogn_tool.analysis.rf_state_engine | benchmarks/benchmark_rf_state_engine.py, benchmarks/load_test_rf_engine.py |

Note:
- this is benchmark-only code, not dead code.

## Unused modules

Modules currently not imported anywhere in the scanned scope.

| Module | Recommendation |
|------|------|
| ogn_tool.cli | evaluate removal |
| ogn_tool.data.stations_repository | verify if legacy |
| ogn_tool.db | verify usage |
| ogn_tool.engine.observation_builder | verify if replaced |
| ogn_tool.engine.rf_dataset | probably replaced by RFAnalysisDataset |
| ogn_tool.rf_analysis | unknown legacy module |

Caution:
- do not delete immediately.

## Safe cleanup process

1. Mark candidate modules with:

```python
# DEPRECATED: candidate for removal
```

2. Wait a few commits.

3. Remove in a dedicated cleanup branch/commit:

`cleanup/remove_legacy_modules`
