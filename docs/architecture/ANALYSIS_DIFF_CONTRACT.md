# Analysis Diff Contract

## Purpose

The analysis diff compares two analysis snapshots and exposes meaningful,
JSON-safe metric deltas.

Its role is to provide a stable comparison surface for downstream
consumers such as anomaly detection, reporting, and future observability
components.

The diff is not a dump of internal analytical state.

---

## Inputs

The diff compares two snapshots:

- `baseline_snapshot`
- `current_snapshot`

These snapshots are expected to follow the public snapshot contract.

---

## Output Schema (v1)

```text
{
  baseline_run_id: str | None
  current_run_id: str | None

  metric_diffs: {
    network_summary: {
      metric_name: {
        baseline
        current
        delta | changed
      }
    }

    spof: {
      station_count: {
        baseline
        current
        delta
      }
      stations_added: [station_id]
      stations_removed: [station_id]
    }

    coverage_gaps: {
      gap_count: {
        baseline
        current
        delta
      }
      gaps_added: [(lat, lon)]
      gaps_removed: [(lat, lon)]
    }
  }
}
```

---

## Covered Metrics (v1)

Version 1 covers only:

- `network_summary`
- `spof`
- `coverage_gaps`

Additional metric sections may be added explicitly in future versions.

---

## Evolution Rules

- new sections may be added explicitly
- existing sections must remain backward compatible
- field names must not be renamed implicitly
- field semantics must not change silently
- JSON-safe output is required

---

## Architectural Rule

The diff contract is a public runtime-facing structure.

It must remain independent from internal engine refactors.

Internal analytical changes may require adaptation in the diff builder,
but must not silently break the public diff schema.
