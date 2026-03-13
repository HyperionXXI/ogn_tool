STATUS: canonical
SOURCE_OF_TRUTH: docs/core/RF_DATASET_SCHEMA.md

This document defines the current dataset and result surfaces used by the
RF engine.

Primary producer:
- `src/ogn_tool/engine/rf_engine.py`

Related contracts:
- `docs/core/DATA_CONTRACT.md`
- `docs/architecture/RF_METRIC_CONTRACT.md`
- `docs/architecture/NETWORK_ENGINEERING_REPORT.md`

# RF Dataset Schema

## 1. Current typed output surface

`RFAnalysisEngine.run(...)` returns `RFAnalysisResults` with the current
canonical fields:

- `feature_matrix`
- `coverage`
- `visibility`
- `blind_zones`
- `antenna_pattern`
- `antenna_shadow_sectors`
- `network_graph`
- `network_metrics`
- `network_timeseries`
- `network_events`
- `network_evolution`
- `station_suggestions`
- `metrics`

`feature_matrix` remains an intermediate/debug surface.
`metrics` remains a summary/compatibility container only.

## 2. Legacy dataset dictionary

`RFAnalysisEngine.build_analysis_dataset(...)` still exists as a legacy
compatibility path.

It may expose a dataset dictionary containing keys such as:
- `observations`
- `packets_all`
- `packets_rf`
- `packets_filtered`
- `rf_receptions`
- `radio_events`
- `station_reception`
- `coverage_grid`
- `coverage_redundancy_grid`
- `station_metrics`
- `network_metrics`
- `azimuth_histogram`
- `directional_balance`
- `rf_diagnosis`
- `shadow_map`
- `station_overlap_matrix`
- `blind_cells`
- `network_blind_zones`
- `stations`
- `dataset_mode`

This dictionary is transitional and should not be treated as the primary
future-facing contract.

## 3. Network metrics surface

`results.network_metrics` is the current typed runtime container for
network and intelligence outputs.

Current notable keys include:
- `visibility`
- `station_influence`
- `station_anomalies`
- `network_robustness`
- `station_placement`
- `station_health`
- `network_summary`
- `station_dependency`

Additional engineering or intelligence outputs may be added through the
same typed surface if documented in:
- `docs/architecture/RF_METRIC_CONTRACT.md`

## 4. Network graph surface

Canonical graph model:
- `src/ogn_tool/models/network_graph_model.py`

Typed result field:
- `results.network_graph`

## 5. Reporting surface

Reporting is not part of the analytical kernel output yet.

The reporting contract is defined in:
- `docs/architecture/NETWORK_ENGINEERING_REPORT.md`

Current reporting builder:
- `src/ogn_tool/reporting/network_engineering_report.py`

## 6. Stability rule

Use this document to understand the current produced surfaces.

Use `docs/architecture/*` documents for:
- governance
- contracts
- runtime rules
- reporting rules
