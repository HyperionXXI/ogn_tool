# Implemented vs Represented Features (Gap Audit)

## Scope
This audit identifies features that are implemented in computation/reporting layers but are not represented in the current canonical output and/or UI projection.

Date: 2026-03-21

## Legend
- Implemented: computed by pipeline/kernel/intelligence or report builder
- Represented in `report.json`: present in canonical report contract
- Represented in UI payload: available in `build_dashboard_payload()` / `build_ui_projection()`

## Table

| Feature Block | Implemented | In report.json | In UI payload | Notes |
|---|---:|---:|---:|---|
| `network_metrics.network_summary` | Yes | Yes | Yes | Canonical core summary. |
| `network_metrics.station_health` | Yes | Yes | Yes | Used by inspector and station map points. |
| `network_metrics.station_dependency` | Yes | Yes | No (direct) | Preserved in report contract but not projected into map/UI metrics. |
| `network_metrics.network_robustness` | Yes | Yes | Indirect | Consumed by intelligence diagnostics/recommendations, not directly displayed as a block. |
| `network_metrics.station_placement` | Yes | Yes | No | Stored in contract, not yet projected in UI. |
| `coverage_score` (root) | Yes | Yes | Yes | Exposed in `network_summary.coverage_score`. |
| `network_confidence` | Yes | No | No | Built in report builder layer, dropped by canonical contract. |
| `station_dominance` | Yes | No | No | Built in report builder layer, dropped by canonical contract. |
| `temporal_observability` | Yes | No | No | Computed in builder, not exported in canonical contract. |
| `recommended_actions` (builder-level) | Yes | No | No | Builder creates it, contract excludes it. |
| `input_warnings` / pipeline warnings | Yes | No | No | Available internally, not in canonical contract/UI. |
| `rf_signature` (surface-based via intelligence) | Yes | No (contract) | Yes | Derived during payload build through artifact enrichment. |
| `rf_directional_gaps` | Yes | No (contract) | Yes | Computed in `report_intelligence`, shown in inspector section. |
| `rf_gap_structure` | Yes | No (contract) | Yes | Computed in intelligence; usable in tooling. |
| `rf_shadow_analysis` | Yes | No (contract) | Yes | Computed in intelligence; shown in inspector section. |
| `links` map layer | Placeholder | n/a | Empty list | UI projection returns empty list currently. |
| `coverage` map layer | Placeholder | n/a | Empty list | UI projection returns empty list currently. |
| `blind_zones` map layer | Placeholder | n/a | Empty list | UI projection returns empty list currently. |
| `risk_zones` map layer | Yes | n/a | Yes | Derived from intelligence alerts + station coordinates. |
| `report_views.get_rf_signature()` | Placeholder | n/a | No | Returns `{}` currently. |
| `report_views.get_recommended_actions()` | Placeholder | n/a | No | Returns `[]` currently. |

## Key Gap Categories

1. Contract narrowing gaps
- Several computed report features exist before export but are intentionally excluded by canonical contract (`network_confidence`, `station_dominance`, temporal block, warnings, builder recommendations).

2. Intelligence-only (runtime projection) gaps
- RF analysis blocks are available in payload generation, but not persisted in canonical `report.json`.

3. UI projection placeholders
- `links`, `coverage`, `blind_zones` are structurally present but not populated.

4. View-layer placeholders
- `report_views.get_rf_signature()` and `report_views.get_recommended_actions()` are stubbed.

## Current Interpretation
- The system is intentionally strict around a minimal canonical report contract.
- Representation gaps are now primarily product-surface decisions (what to project/persist), not kernel capability gaps.

## Next Safe Step (no kernel change)
- Decide which non-kernel blocks should be promoted from “implemented but not represented” to either:
  - canonical contract fields, or
  - deterministic UI payload fields.

