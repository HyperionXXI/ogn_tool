> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

# RF Metric Contract

This document defines the current contract between the analytical engine
and its runtime consumers for typed network metrics.

The goal is to prevent contract drift between:


The canonical typed surface is:


The legacy runtime context (`ctx[...]`) is compatibility-only and must
not be treated as the source of truth.


## Canonical Rule

`results.*` is the official runtime API.

`ctx[...]` is legacy compatibility only.

Any change to keys, types, DataFrame columns, or semantic meaning in
`results.network_metrics` must be treated as an architectural change.


## Network Metrics Container

Typed network metrics are exposed through:


See also:
  - [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
  - [INDEX.md](INDEX.md)

Current canonical keys:

- `visibility`
- `station_influence`
- `station_anomalies`
- `network_robustness`
- `station_placement`
- `station_health`
- `network_summary`
- `station_dependency`
- `spof`
- `coverage_gaps`
- `coverage_gap_priorities`
- `station_redundancy_planner`
- `station_addition_simulation`

These keys represent the current typed network intelligence surface.
Any new runtime key must be documented here before being treated as part
of the public typed contract.

---

## Metric Stability Levels

| Metric | Stability | Primary Consumer |
|--------|-----------|------------------|
| `visibility` | stable | analysis / runtime |
| `station_influence` | stable | analysis / runtime |
| `station_anomalies` | experimental | diagnostics / UI |
| `network_robustness` | experimental | analysis / intelligence |
| `station_placement` | experimental | analysis / runtime |
| `station_health` | exposed | reporting / UI |
| `network_summary` | exposed | reporting / UI |
| `station_dependency` | exposed | reporting / UI |
| `spof` | exposed | reporting / UI |
| `coverage_gaps` | exposed | reporting / UI |
| `coverage_gap_priorities` | exposed | reporting / planning |
| `station_redundancy_planner` | experimental | reporting / planning |
| `station_addition_simulation` | experimental | reporting / planning |

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

### `station_health`

Type:
- `pandas.DataFrame`

Semantic meaning:
- operator-facing health classification for stations derived from
  existing network metrics

Stability:
- exposed

---

### `network_summary`

Type:
- `dict`

Semantic meaning:
- compact operator-facing summary of overall network state

Stability:
- exposed

---

### `station_dependency`

Type:
- `pandas.DataFrame`

Semantic meaning:
- structural dependency ranking between stations derived from overlap and
  station importance signals

Stability:
- exposed

---

### `spof`

Type:
- `pandas.DataFrame`

Columns:
- `station_id`
- `aircraft_lost`
- `coverage_loss_ratio`
- `spof_score`
- `network_status_after_removal`
- `spof_level`
- `notes`

Semantic meaning:
- single-point-of-failure ranking derived from station removal
  simulation

Stability:
- exposed

---

### `coverage_gaps`

Type:
- `pandas.DataFrame`

Columns:
- `lat`
- `lon`
- `station_count`
- `gap_level`
- `notes`

Semantic meaning:
- spatial cells with insufficient observed station coverage

Stability:
- exposed

---

### `coverage_gap_priorities`

Type:
- `pandas.DataFrame`

Columns:
- `lat`
- `lon`
- `station_count`
- `gap_level`
- `priority_score`
- `recommended_action`
- `notes`

Semantic meaning:
- operator-facing ranking of detected coverage gaps

Stability:
- exposed

---

### `station_redundancy_planner`

Type:
- `pandas.DataFrame`

Columns:
- `target_station`
- `coverage_loss`
- `aircraft_lost`
- `priority`
- `status_after_removal`
- `notes`

Semantic meaning:
- ranking of stations whose loss most justifies redundancy work

Stability:
- experimental

---

### `station_addition_simulation`

Type:
- `pandas.DataFrame`

Columns:
- `lat`
- `lon`
- `aircraft_supported`
- `coverage_gain`
- `redundancy_gain`
- `priority_score`
- `notes`

Semantic meaning:
- empirical simulation of candidate station additions built from the
  current observed network geometry

Stability:
- experimental

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

## Future Namespace Rule

`results.network_metrics` is currently a flat typed surface.

This is acceptable while the number of stable metric families remains
limited.

If the surface continues to grow, it must evolve toward grouped
namespaces instead of unbounded flat expansion.

Recommended future families include:

- `health`
- `topology`
- `redundancy`
- `coverage`
- `simulations`

Examples of future grouped paths:

- `results.network_metrics["health"]["station_health"]`
- `results.network_metrics["topology"]["station_dependency"]`
- `results.network_metrics["coverage"]["gaps"]`
- `results.network_metrics["simulations"]["station_removal"]`

Do not introduce this refactor prematurely.

The grouping should happen only when:

- the flat metric surface becomes too large to document clearly
- reporting depends on too many flat keys
- multiple metrics clearly belong to the same family

Until then, new metric keys must remain documented and controlled.

## Change Policy

The following changes are considered breaking unless explicitly
announced and reviewed:

- renaming a canonical metric key
- changing a metric from `DataFrame` to `dict` or the reverse
- removing required columns
- changing the semantic meaning of a metric field

Any such change must update this document.

