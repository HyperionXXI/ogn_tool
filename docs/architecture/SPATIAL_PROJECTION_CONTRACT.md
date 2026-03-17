> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

# Spatial Projection Contract

Status: ACTIVE
Date: 2026-03-15

## Purpose

This document defines the stable contract for spatial reporting
projections consumed by map-first interfaces and other spatial
consumers.

Its purpose is to separate:

- human-oriented reporting views
- spatial reporting views
- raw analytical artifacts

Spatial consumers such as deck.gl must consume stable spatial reporting
views, not raw analytical artifacts.

## Scope

This contract applies to reporting modules that expose spatially ordered
or map-oriented projections.

Current example:

- `src/ogn_tool/reporting/directional_spatial_views.py`

Future examples may include:

- coverage grids
- visibility sectors
- azimuth-distance heatmaps
- station-to-target arc projections

## Core Rule

A spatial reporting view MUST expose explicit ordering semantics.

A public field must never rely on an implicit convention such as:

- "the list is usually sorted by weight"
- "the UI happens to expect azimuth order"

If multiple orderings are useful, they must be named explicitly.

## Directional Spatial Projection

### Producer

- `build_directional_sectors(...)`

### Input

A directional histogram surface of the form:

```json
{
  "edges": [...],
  "hist": [...]
}
```

### Output

The stable directional spatial projection contains:

- `packet_count`
- `sector_count`
- `sectors_by_azimuth`
- `sectors_by_weight`
- `dominant_arc`

### Field Semantics

#### `packet_count`

Total usable packets represented by the directional histogram.

#### `sector_count`

Number of sectors represented in the projection.

#### `sectors_by_azimuth`

Canonical spatial ordering.

Properties:

- ordered by ascending azimuth
- intended for spatial consumers
- stable source for map and polar rendering

Consumers:

- deck.gl
- map layers
- polar/radial visualizations
- spatial comparison tooling

#### `sectors_by_weight`

Diagnostic full ordering.

Properties:

- ordered by descending packet weight
- intended for diagnostic consumers
- contains the full sector surface, not only a truncated top-k subset
- not the canonical spatial ordering

Consumers:

- CLI diagnostics
- ranked tables
- engineering inspection tooling

#### `dominant_arc`

Sector arc computed from the directional histogram.

Properties:

- wrap-around aware
- stable interpretive RF primitive
- suitable for highlighting the dominant direction of observation

## Invariants

### Invariant 1

`sectors_by_azimuth` MUST be sorted by ascending sector start azimuth.

### Invariant 2

`sectors_by_weight` MUST be sorted by descending packet count.

### Invariant 3

`dominant_arc` MUST use explicit wrap-around semantics for circular
histograms.

### Invariant 4

The same histogram input MUST produce the same spatial projection.

Spatial reporting views are deterministic.

## Consumer Rules

### Allowed

Spatial consumers MAY read:

- `sectors_by_azimuth`
- `dominant_arc`
- future stable spatial projections in `src/ogn_tool/reporting/`

### Forbidden

Spatial consumers MUST NOT derive their primary contract from:

- `azimuth_histogram.json`
- exploratory matrices
- ad-hoc scripts
- runtime snapshots

## Relationship To Human Views

Human-oriented reporting views and spatial reporting views serve
separate purposes.

Example:

- `directional_views.py` -> human summary
- `directional_spatial_views.py` -> spatial projection

A consumer must choose the surface appropriate to its role.

## Relationship To `report.json`

Spatial projections may be too detailed for `report.json`.

Therefore:

- `report.json` remains compact
- large or dense spatial payloads should remain outside `report.json`
- if exported, spatial artifacts must derive from reporting spatial views

## Evolution Rule

When adding a new spatial capability, the required sequence is:

1. compute the analytical truth in runtime/analysis
2. define a stable spatial reporting projection
3. test ordering and shape invariants
4. only then connect UI, map, or deck.gl consumers

Consumer-specific ordering must never be left implicit.
