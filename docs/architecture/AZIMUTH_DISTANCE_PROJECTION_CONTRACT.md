# Azimuth Distance Projection Contract

Status: ACTIVE
Date: 2026-03-15

## Purpose

This document defines the stable reporting projection built on the
azimuth-distance analytical primitive.

Its purpose is to ensure that consumers such as CLI, UI, APIs, and
future spatial tooling read a deterministic projection rather than
recomputing semantics from the analytical matrix directly.

This contract complements:

- `AZIMUTH_DISTANCE_CONTRACT.md`
- `SPATIAL_PROJECTION_CONTRACT.md`
- `CONSUMER_SURFACE_GOVERNANCE.md`

## Scope

This contract applies to reporting-layer projections derived from the
azimuth-distance analytical primitive.

Current producer:

- `src/ogn_tool/reporting/azimuth_distance_views.py`

Current public function:

- `build_azimuth_distance_summary(...)`

## Relationship To The Analytical Primitive

The analytical primitive defines:

- `azimuth_bins`
- `distance_bins_km`
- `matrix`
- `packet_count`

The reporting projection may add summaries and stable field naming.

It must not change:

- cell semantics
- bin semantics
- matrix dimensions
- packet conservation semantics

## Output Contract

The stable reporting projection currently contains:

- `packet_count`
- `azimuth_bin_count`
- `distance_bin_count`
- `nonzero_cell_count`
- `total_cell_count`
- `max_cell_count`
- `dominant_cell`
- `azimuth_bins`
- `distance_bins_km`
- `azimuth_profile`
- `distance_profile`
- `rf_signature`
- `matrix`

## Field Semantics

### `packet_count`

Number of represented observations in the analytical matrix.

### `azimuth_bin_count`

Number of azimuth bins, equal to `len(azimuth_bins) - 1`.

### `distance_bin_count`

Number of distance bins, equal to `len(distance_bins_km) - 1`.

### `nonzero_cell_count`

Number of matrix cells with a strictly positive count.

### `total_cell_count`

Total number of cells in the matrix.

### `max_cell_count`

Maximum raw packet count contained in a single cell.

### `dominant_cell`

The cell with the highest raw count.

When present, it must contain:

- `azimuth_start_deg`
- `azimuth_end_deg`
- `distance_start_km`
- `distance_end_km`
- `count`

When the matrix is empty or contains no positive cells, `dominant_cell`
MUST be `null` / `None`.

### `azimuth_bins`

Explicit azimuth bin edges copied from the analytical primitive.

### `distance_bins_km`

Explicit distance bin edges copied from the analytical primitive.

### `azimuth_profile`

A deterministic one-dimensional profile derived by summing the matrix
along the distance axis.

Each entry must contain:

- `azimuth_start_deg`
- `azimuth_end_deg`
- `count`
- `share`

`share` is defined as `count / packet_count` when `packet_count > 0`,
otherwise `0.0`.

### `distance_profile`

A deterministic one-dimensional profile derived by summing the matrix
along the azimuth axis.

Each entry must contain:

- `distance_start_km`
- `distance_end_km`
- `count`
- `share`

`share` is defined as `count / packet_count` when `packet_count > 0`,
otherwise `0.0`.

### `rf_signature`

A compact deterministic RF summary derived from `azimuth_profile` and
`distance_profile`.

Current fields:

- `packet_count`
- `dominant_corridor_start_deg`
- `dominant_corridor_end_deg`
- `corridor_width_deg`
- `dominant_corridor_share`
- `dominant_distance_band_km`
- `dominant_distance_band_share`
- `nonzero_distance_band_count`
- `distance_spread_index`
- `anisotropy_index`
- `interpretation`

All numeric fields must remain machine-readable. Human formatting belongs
outside this projection.

### `matrix`

Matrix cell values copied from the analytical primitive without changing
cell semantics.

## Invariants

### Invariant 1

`azimuth_bin_count == len(azimuth_bins) - 1`

### Invariant 2

`distance_bin_count == len(distance_bins_km) - 1`

### Invariant 3

`total_cell_count == azimuth_bin_count * distance_bin_count`

### Invariant 4

`nonzero_cell_count <= total_cell_count`

### Invariant 5

If `max_cell_count == 0`, then `dominant_cell` MUST be `null` / `None`.

### Invariant 6

`sum(entry['count'] for entry in azimuth_profile) == packet_count`

### Invariant 7

`sum(entry['count'] for entry in distance_profile) == packet_count`

### Invariant 8

If `rf_signature` is present, `rf_signature['packet_count'] == packet_count`.

### Invariant 9

If `rf_signature` is present, `rf_signature['corridor_width_deg'] > 0`.

### Invariant 10

If `rf_signature` is present, `0.0 <= rf_signature['distance_spread_index'] <= 1.0`.

### Invariant 11

The projection MUST remain deterministic for identical input surfaces.

## Consumer Rules

Consumers MAY use this projection for:

- CLI summaries
- stable notebook usage
- UI-side inspection
- future spatial summaries

Consumers MUST NOT reinterpret `matrix` as anything other than the
analytical cell semantics defined by `AZIMUTH_DISTANCE_CONTRACT.md`.

Consumers MUST NOT assume any UI-specific rendering semantics from this
projection.

## Relationship To UI

This projection is stable enough for consumer use, but it is not yet a
specialized visualization payload.

Future spatial consumers may require an additional reporting projection
optimized for map-first or polar rendering.

That future projection must derive from the same analytical primitive
without changing its semantics.

## Evolution Rule

Future additions are allowed only when they remain:

- deterministic
- semantically explicit
- derived from the analytical primitive
- independent from any one rendering framework

UI-specific concepts such as palettes, interpolation, and hover labels
must remain outside this projection.
