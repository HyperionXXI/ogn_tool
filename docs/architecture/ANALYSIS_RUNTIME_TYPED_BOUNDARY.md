# Analysis Runtime Typed Boundary

## Purpose

This document defines a typed boundary between `analysis` and `runtime`.

`pandas` DataFrames remain valid internal structures inside `analysis` modules,
but they must not act as implicit runtime contracts.

## Rule

- `analysis` may use `DataFrame` internally for computation
- `runtime` must consume typed evaluation models at module boundaries
- silent fallback on missing DataFrame output columns is forbidden at the
  analysis/runtime boundary

## First Migrated Surface

The first typed boundary is the station addition evaluation surface.

Current target:

- `simulate_station_addition(...)` remains DataFrame-based internally
- `build_station_addition_evaluations(...)` converts that DataFrame into
  `list[StationAdditionEvaluation]`
- `runtime` station addition and multi-station modules consume the typed
  evaluations instead of raw DataFrame columns

## Rationale

This prevents silent schema drift such as renaming:

- `coverage_gain`
- `redundancy_gain`
- `aircraft_supported`
- `priority_score`

without breaking runtime consumers loudly.

## Boundary Principle

Preferred flow:

```text
analysis -> DataFrame -> typed evaluation model -> runtime
```

Not preferred:

```text
analysis -> DataFrame -> runtime
```

## Status

Typed boundary introduced first for station addition evaluations.

> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.
