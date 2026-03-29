# 01 — Data Contracts (Canonical + Required)

This file defines the minimum contracts an AI must follow to avoid architectural regression.

## 1) Current Payload Contract (as consumed by frontend)
`GET /api/payload?run_id=...` returns a payload with these top-level keys:
- `network_summary`
- `stations`
- `metrics`
- `intelligence`
- `debug`

Current `metrics` usually contains:
- `stations`
- `links`
- `coverage`
- `blind_zones`
- `risk_zones`
- `aircraft_positions` (may be empty)

Current `intelligence.rf_analysis` contains:
- `rf_signature_version`
- `rf_signature`
- `rf_directional_gaps`
- `rf_gap_structure`
- `rf_shadow_analysis`

## 2) Canonical Observation Unit (Mandatory)
Network intelligence must not use raw packets directly.

```python
aircraft_observation = {
  "aircraft_id": str,
  "lat": float,
  "lon": float,
  "timestamp": datetime,
  "seen_by": [station_id, ...]
}
```

Rules:
- `seen_by` comes from real multi-station correlation in a shared time window.
- no heuristic `seen_by` inference.
- no mono-station fallback to claim network behavior.
- UI projection fields are derived from this source only.

## 3) UI Projection Contract
Allowed UI-facing simplification:

```python
metrics.aircraft_positions = projection(aircraft_observations)
```

Suggested projection schema:
```json
{
  "src": "ABC123",
  "lat": 47.33,
  "lon": 7.27,
  "seen_by": ["FK50887", "LSPD"],
  "timestamp": "2026-03-21T12:18:04Z"
}
```

## 4) Run Modes
Two explicit modes must be represented in payload semantics:

### A) RF-only diagnostic
- RF signature/gaps/shadow available
- aircraft observation layer missing or empty
- no network uniqueness/redundancy claim

### B) Network intelligence
- aircraft observations present (non-empty)
- spatial network features derivable and trustworthy

A run is `Network intelligence` only if aircraft observation layer is non-empty.

## 5) Target Spatial Features (P1)
Backend/reporting output (not frontend-derived):
- `spatial_network_features.coverage_density`
- `spatial_network_features.unique_coverage`
- `spatial_network_features.shared_coverage`
- `spatial_network_features.blind_zones`
- `spatial_network_features.grid_meta`

Grid meta example:
```json
{
  "min_lat": 47.10,
  "max_lat": 47.60,
  "min_lon": 6.90,
  "max_lon": 7.80,
  "cell_size_km": 2,
  "window_start": "...",
  "window_end": "..."
}
```

## 6) Additive-Only Evolution Rule
When extending payload:
- add fields only
- do not rename/remove existing canonical keys
- no legacy compatibility branches inside core payload

## 7) Sample Files in this Bundle
- `samples/payload_rf_only.json`
- `samples/payload_network_ready_target.json`

Use these as acceptance references for P0/P1 implementation.
