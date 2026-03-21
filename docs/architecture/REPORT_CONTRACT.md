# Report Contract

Canonical report structure consumed by reporting views and dashboard payload mapping.

```json
{
  "run_id": "string",
  "metadata": {},
  "network_metrics": {
    "network_summary": {},
    "station_health": [],
    "station_dependency": [],
    "network_robustness": {},
    "station_placement": {}
  },
  "coverage_score": null
}
```

## Rules

- `run_id` is always present and typed as string.
- `metadata` is always present and typed as object.
- `network_metrics` is always present and typed as object.
- `network_metrics.network_summary` is always present and typed as object.
- `network_metrics.station_health` is always present and typed as `list[object]`.
- `network_metrics.station_dependency` is always present and typed as `list[object]`.
- `network_metrics.network_robustness` is always present and typed as object.
- `network_metrics.station_placement` is always present and typed as object.
- `coverage_score` is always present and typed as `float | null`.

## Constraints

- No duplicate locations for the same metric.
- No optional nesting ambiguity.
- Views must not require fallback extraction paths.
- Pipeline produces raw analysis data only; reporting owns projection into this contract.
