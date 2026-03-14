# Analysis Snapshot Contract

## Purpose

The analysis snapshot provides a stable, JSON-serializable
representation of the RF network analysis state.

Snapshots allow:

- reproducible analysis results
- historical comparison of network states
- regression detection
- reporting and observability

Snapshots are not a dump of internal engine structures.

They are a public, versioned interface.

---

## Architectural Principle

The project distinguishes two schemas:

```text
engine schema      -> internal runtime structures
snapshot schema    -> public serialized representation
```

The engine schema is free to evolve.

The snapshot schema must remain stable and versioned.

---

## Snapshot Adapter Layer

The file:

- `src/ogn_tool/runtime/analysis_snapshot.py`

defines the snapshot schema and acts as the adaptation layer between
engine and snapshot.

Responsibilities:

- convert internal runtime metrics
- ensure JSON-safe serialization
- expose a stable schema

No other module should write snapshot structures directly.

---

## Snapshot Structure (v1)

Snapshot version 1 exposes the following structure:

```json
{
  "snapshot_version": "1",
  "engine_version": "...",
  "created_at": "...",
  "dataset_summary": {"...": "..."},
  "network_metrics": {"...": "..."}
}
```

### `dataset_summary`

Contains minimal dataset context:

- `observation_count`
- `station_count` when available
- `aircraft_count` when available
- `time_min`
- `time_max`

### `network_metrics`

Contains the serialized analytical surfaces derived from:

- `network["metrics"]`

Metrics must be serialized to JSON-safe structures.

Examples:

- `DataFrame` -> `list[dict]`
- `numpy` scalar -> Python scalar
- `pd.NA` / `NaN` -> `null`
- `datetime` -> ISO-8601 string

---

## Snapshot Stability Rules

The snapshot schema is treated as a public contract.

Therefore:

- existing keys must not be renamed
- field semantics must remain stable
- historical snapshots must remain readable
- engine refactoring must not break the snapshot format

---

## Schema Evolution

When the snapshot schema must change:

- a new version must be introduced
- `snapshot_version = "2"`
- version 1 snapshots must remain readable
- schema changes must be documented
- schema changes must never occur implicitly

---

## Explicit Prohibition

The following pattern is forbidden:

```python
snapshot = network["metrics"]
```

or any direct dump of engine runtime structures.

All snapshot generation must pass through:

- `build_analysis_snapshot()`

---

## Design Rationale

This contract ensures:

- reproducible analysis
- long-term snapshot compatibility
- independence between engine refactoring and data persistence

It also enables future capabilities:

- snapshot history
- analysis diff
- RF network evolution tracking

---

## Status

Snapshot contract introduced in engine version 1.1.
