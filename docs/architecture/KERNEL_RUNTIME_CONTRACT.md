# Kernel Runtime Contract

This document defines the stable runtime outputs produced by the RF
network analysis pipeline.

The kernel stage is:

- `run_network_graph_stage()`

Its output structure is:

```python
network = {
    "graph": GraphResult,
    "metrics": dict,
    "timeseries": dict,
    "events": dict,
    "evolution": dict,
    "station_suggestions": DataFrame,
}
```

---

## Canonical Runtime Surface

The only stable runtime surface intended for downstream consumers is:

- `network["metrics"]`

This surface is mirrored into:

- `results.network_metrics`

Consumers such as:

- reporting
- UI dashboards
- scripts

must use:

- `results.network_metrics`

and must not depend on other kernel outputs unless those outputs are
explicitly added to the runtime contract.

---

## Auxiliary Outputs

The following kernel outputs are currently considered auxiliary:

- `network["events"]`
- `network["timeseries"]`
- `network["evolution"]`
- `network["station_suggestions"]`

These outputs may evolve without stability guarantees.

If any of them becomes a public runtime surface, this contract must be
updated.

---

## Validation Rule

The kernel must validate `network["metrics"]` before exposing it to
runtime consumers.

This validation is currently enforced by:

- `validate_network_metrics(...)`

The purpose of this validation is to detect contract drift early, before
reporting, UI, or scripts consume an invalid runtime surface.
