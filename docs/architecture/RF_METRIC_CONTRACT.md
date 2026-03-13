# RF Metric Contract

This document defines the current contract between the analytical engine
and its runtime consumers for typed network metrics.

The goal is to prevent contract drift between:

- the analytical engine
- runtime adapters
- UI pages
- scripts and developer tooling

The canonical typed surface is:

- `RFAnalysisResults`
- `RFAnalysisResults.network_metrics`

The legacy runtime context (`ctx[...]`) is compatibility-only and must
not be treated as the source of truth.

---

## Canonical Rule

`results.*` is the official runtime API.

`ctx[...]` is legacy compatibility only.

Any change to keys, types, DataFrame columns, or semantic meaning in
`results.network_metrics` must be treated as an architectural change.

---

## Network Metrics Container

Typed network metrics are exposed through:

- `results.network_metrics`

Current canonical keys:

- `visibility`
- `station_influence`
- `station_anomalies`
- `network_robustness`
- `station_placement`

Additional keys may exist for transitional reasons, but the keys above
represent the current typed network intelligence surface.

---

## Metric Stability Levels

| Metric | Stability |
|--------|-----------|
| `visibility` | stable |
| `station_influence` | stable |
| `station_anomalies` | experimental |
| `network_robustness` | experimental |
| `station_placement` | experimental |

Stable metrics should not change shape or meaning without explicit
architectural review.

Experimental metrics may evolve, but any change must still be documented
in this contract before being treated as part of the runtime API.

---

## Metric Families

### `visibility`

Type:
- `dict`

Keys:
- `matrix`
- `overlap`
- `dependency`
- `redundancy`
- `summary`

The keys listed above represent the current canonical visibility
surface.

Additional keys must be documented before being exposed to runtime
consumers.

#### `visibility["matrix"]`

Type:
- `pandas.DataFrame`

Required columns:
- `src`
- `igate`
- `packets`

Optional passthrough columns may exist depending on the observation
source, including:
- `lat`
- `lon`
- `altitude_m`

Semantic meaning:
- incidence-style aircraft-to-station visibility summary
- one row per `(aircraft, station)` pair with aggregated packet count

#### `visibility["overlap"]`

Type:
- `pandas.DataFrame`

Shape:
- station x station matrix

Semantic meaning:
- station overlap / co-visibility surface

#### `visibility["dependency"]`

Type:
- `pandas.DataFrame`

Columns:
- `aircraft_id`
- `station_count`
- `single_station`
- `critical_station_id`

Semantic meaning:
- aircraft dependency on one or very few stations

#### `visibility["redundancy"]`

Type:
- implementation-defined redundancy summary
- currently produced from `aircraft_redundancy(...)`

Semantic meaning:
- aircraft-level station redundancy view

#### `visibility["summary"]`

Type:
- `dict`

Keys:
- `aircraft_count`
- `station_count`
- `mean_stations_per_aircraft`
- `single_station_aircraft_count`
- `single_station_ratio`
- `max_overlap`
- `mean_overlap`

Semantic meaning:
- compact summary of the network visibility state

---

### `station_influence`

Type:
- `pandas.DataFrame`

Columns:
- `station_id`
- `aircraft_seen`
- `unique_aircraft_count`
- `single_station_aircraft_count`
- `mean_overlap`
- `graph_importance`
- `redundancy_penalty`
- `influence_score`

Semantic meaning:
- synthetic ranking of how structurally important each station is in the
  current RF observation network

Notes:
- this is a heuristic metric
- larger `influence_score` means higher structural importance

---

### `station_anomalies`

Type:
- `pandas.DataFrame`

Columns:
- `station_id`
- `anomaly_type`
- `severity`
- `description`
- `metric_value`

Current anomaly types:
- `critical_single_station`
- `high_redundancy`
- `weak_station`

Semantic meaning:
- lightweight anomaly surface derived from existing metrics
- intended for diagnostics and operator attention

---

### `network_robustness`

Type:
- `pandas.DataFrame`

Columns:
- `station_id`
- `aircraft_lost`
- `redundancy_lost`
- `coverage_loss_ratio`
- `impact_score`

Semantic meaning:
- simulated impact of removing each station from the observed network

Notes:
- this is a station removal impact heuristic
- larger `impact_score` means a more critical station

---

### `station_placement`

Type:
- `pandas.DataFrame`

Columns:
- `lat`
- `lon`
- `coverage_gain`
- `redundancy_gain`
- `aircraft_supported`
- `critical_aircraft_supported`
- `nearest_station_distance_km`
- `placement_score`

Semantic meaning:
- candidate locations where a new station would most improve network
  coverage and redundancy under the current heuristic model

Notes:
- v1 is heuristic only
- no RF propagation model is implied by this metric
- larger `placement_score` means more promising candidate placement

---

## UI Rule

UI consumers may:

- format values
- filter rows
- sort tables
- choose display subsets

UI consumers must not:

- redefine metric semantics
- recompute analytical metrics already present in `results.network_metrics`
- silently transform one metric family into another incompatible shape

---

## Compatibility Rule

Legacy paths such as:

- `ctx["network_analysis"]`
- `ctx["dataset"]`

are transitional compatibility paths only.

They must not be treated as the authoritative definition of network
metrics.

Any new runtime consumer should prefer:

- `results.network_metrics[...]`

---

## Change Policy

The following changes are considered breaking unless explicitly
announced and reviewed:

- renaming a canonical metric key
- changing a metric from `DataFrame` to `dict` or the reverse
- removing required columns
- changing the semantic meaning of a metric field

Any such change must update this document.
