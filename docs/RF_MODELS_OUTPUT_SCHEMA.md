This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Models Output Schema

RF model results are normalized by `run_rf_model()` and exposed through
`RFAnalysisEngine.run()` via `metrics["rf_models"]`.

## Normalized output structure

```
{
  "implemented": bool,
  "summary": dict | None,
  "data": any,
  "binned_data": any | None
}
```

## Access patterns

The following model results are exposed under `metrics["rf_models"]`:

- `metrics["rf_models"]["signal_distance"]`
- `metrics["rf_models"]["radio_horizon"]`
- `metrics["rf_models"]["terrain"]`
- `metrics["rf_models"]["terrain_visibility"]`
- `metrics["rf_models"]["altitude_distance"]`

## Example

```json
{
  "rf_models": {
    "signal_distance": {
      "implemented": true,
      "summary": {
        "packet_total": 15432,
        "max_distance_km": 162.4
      },
      "data": "<scatter_dataframe>",
      "binned_data": "<binned_dataframe>"
    }
  }
}
```
