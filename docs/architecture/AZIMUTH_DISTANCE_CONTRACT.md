> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

See also:
  - [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
  - [INDEX.md](INDEX.md)

# Azimuth Distance Contract

Status: DRAFT
Date: 2026-03-15

## Purpose

This document defines the contract for azimuth-distance analytical and
reporting surfaces.

Its purpose is to prevent a common architectural failure mode:

- analysis primitives drifting toward UI-specific rendering needs
- consumers depending on implicit binning assumptions
- different layers interpreting matrix cell values differently

The azimuth-distance matrix is a core RF analytical primitive.

It must be defined as an analytical contract first, and only later be
projected into consumer-facing reporting or visualization surfaces.

## Scope

This contract applies to:

- future azimuth-distance analysis primitives
- future azimuth-distance reporting views
- future artifacts derived from those views

This contract does not define visualization behavior.

Visualization is a consumer concern.

## Layer Separation

### Analysis Layer

The analysis layer computes the azimuth-distance matrix as analytical
truth.

It may define:

- azimuth bins
- distance bins
- matrix cell values
- packet count
- deterministic aggregation

It must not define:

- colors
- visual thresholds
- display-oriented interpolation
- deck.gl-specific structures
- UI labels tied to one consumer

### Reporting Layer

The reporting layer may project the analytical matrix into stable
consumer-facing structures.

It may define:

- named fields
- stable metadata
- deterministic summaries
- compact spatial projections

It must not change the analytical meaning of matrix cells.

### UI / Spatial Consumers

Spatial consumers may:

- render the matrix
- choose color scales
- interpolate visually
- add interaction and tooltips

They must not redefine the matrix semantics.

## Canonical Analytical Surface

The canonical azimuth-distance analytical primitive SHOULD expose:

- `azimuth_bins`
- `distance_bins_km`
- `matrix`
- `packet_count`

Example shape:

```json
{
  "azimuth_bins": [0, 10, 20, 30],
  "distance_bins_km": [0, 10, 20, 30],
  "matrix": [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
  "packet_count": 36
}
```

## Required Decisions

The following semantics must be fixed before implementation.

### 1. Azimuth Convention

The matrix MUST use a documented azimuth convention.

Recommended default:

- degrees in `[0, 360)`
- increasing clockwise
- north-aligned reference

### 2. Distance Convention

Distance bins MUST be documented in kilometers.

Recommended default field name:

- `distance_bins_km`

Distance must represent radial distance from the observing station.

### 3. Cell Semantics

Each matrix cell MUST have one explicit meaning.

Allowed examples:

- raw packet count
- unique aircraft count
- normalized packet share

The first implementation SHOULD use:

- raw packet count

because it is the simplest, least ambiguous analytical primitive.

Normalization, if needed later, should be added as a separate reporting
projection, not baked implicitly into the analytical primitive.

### 4. Binning Rule

Bin edges MUST be explicit and deterministic.

Consumers must not infer bin widths from undocumented assumptions.

### 5. Empty Cell Semantics

A zero-valued cell MUST mean:

- no usable observations fell into that azimuth-distance bin

It must not implicitly mean:

- missing data
- invalid observation
- filtered consumer state

### 6. Bin Edge Semantics

`azimuth_bins` and `distance_bins_km` represent **bin edges**, not bin
centers.

The number of bins along a dimension equals:

`len(edges) - 1`

Example:

`azimuth_bins = [0, 10, 20, 30]`

represents the following azimuth sectors:

- `[0, 10)`
- `[10, 20)`
- `[20, 30)`

Consumers must not interpret these values as bin centers.

## Invariants

### Invariant 1

`len(matrix)` MUST equal `len(azimuth_bins) - 1`.

### Invariant 2

Each row of `matrix` MUST have length `len(distance_bins_km) - 1`.

### Invariant 3

Matrix generation MUST be deterministic for identical analytical input.

### Invariant 4

Cell values MUST preserve the documented cell semantics.

### Invariant 5

The analytical surface MUST remain independent from any specific UI or
rendering library.

### Invariant 6

The total number of observations represented in the matrix MUST equal
`packet_count`.

Formally:

`sum(matrix) == packet_count`

This invariant guarantees that the azimuth-distance matrix is a lossless
aggregation of the underlying analytical observations.

## Reporting Projection Rule

A future reporting projection such as:

- `azimuth_distance_views.py`

may add:

- stable metadata
- compact summaries
- consumer-friendly field naming

It must not:

- change the matrix meaning
- reorder bins implicitly
- normalize values without explicit naming

## Artifact Rule

A future exported artifact such as:

- `azimuth_distance_matrix.json`

must derive from the reporting or analysis contract explicitly chosen
for export.

The artifact must document whether it represents:

- analytical truth
- reporting projection

These two must not be conflated.

## Consumer Rule

Consumers such as deck.gl must read a stable projection derived from
this contract.

They must not infer semantics from:

- ad-hoc scripts
- exploratory notebooks
- raw intermediate structures

## Recommended Implementation Order

1. define the analytical primitive contract
2. implement the analysis primitive
3. test matrix invariants
4. define the reporting projection
5. test the reporting projection contract
6. only then connect UI or map consumers

## Immediate Guidance

For the first implementation, prefer the narrowest correct primitive:

- raw packet count matrix
- explicit azimuth bin edges
- explicit distance bin edges in kilometers
- deterministic shape
- no UI-specific semantics

This keeps the analytical core reusable across OGN, FANET, Meshtastic,
LoRa, APRS, ADS-B, and future RF observation networks.

## Implementation Note (Reference Binning Method)

To avoid binning drift, the recommended bin assignment method is:

`numpy.searchsorted(edges, value, side="right") - 1`

Example:

```python
az_idx = np.searchsorted(azimuth_bins, azimuth_deg, side="right") - 1
dist_idx = np.searchsorted(distance_bins_km, distance_km, side="right") - 1
```

This ensures:

- deterministic bin assignment
- strict compatibility with explicit bin edges
- absence of implicit step division

Implementations must avoid deriving bin indices via implicit division
such as:

`int(value / bin_step)`

because this can introduce edge inconsistencies.
