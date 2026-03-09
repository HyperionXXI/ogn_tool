# ROADMAP GAP ANALYSIS

This document compares **docs vs repo reality** and identifies gaps.

## System architecture
- **Documented**: layered collector → DB → analysis engine → UI (SYSTEM_ARCHITECTURE.md).
- **Actual**: matches (collector in `scripts/collector.py`, analysis in `src/ogn_tool/analysis`, engine in `src/ogn_tool/engine`, UI in `apps/ui/pages`).
- **Gap**: none.
- **Action**: keep as canonical.

## Data model
- **Documented**: separate `rf_packets`, `aprs_packets`, `radio_events`, `station_reception` (DATA_MODEL.md).
- **Actual**: single `packets` table; RF vs APRS‑IS mixed; engine builds radio_events in memory.
- **Gap**: canonical tables not implemented.
- **Action**: Phase 1 data model separation.

## Map engine
- **Documented**: (MAP_ENGINE.md is empty).
- **Actual**: pydeck map engine exists in `apps/ui/map_engine/*`.
- **Gap**: documentation missing.
- **Action**: document pydeck engine in MAP_ENGINE.md (subordinate note).

## UI/UX spec
- **Documented**: (UI_UX_SPEC.md is empty).
- **Actual**: Coverage Explorer uses map‑centric layout with left/center/right panels.
- **Gap**: UI spec missing.
- **Action**: document target UX in UI_UX_SPEC.md and align with ROADMAP_MASTER.

## Analysis engine
- **Documented**: (ANALYSIS_ENGINE.md is empty).
- **Actual**: RFAnalysisEngine orchestrates analysis and dataset construction.
- **Gap**: document engine scope.
- **Action**: fill ANALYSIS_ENGINE.md with current engine API.

## Network intelligence
- **Documented**: (NETWORK_INTELLIGENCE.md is empty).
- **Actual**: engine computes radio_events, station_reception, redundancy, overlap matrix.
- **Gap**: documentation missing.
- **Action**: document current capabilities + roadmap phase.

## Feature roadmap
- **Documented**: (FEATURE_ROADMAP.md is empty).
- **Actual**: features exist in analysis modules and RF_FEATURES_INDEX.
- **Gap**: missing feature roadmap.
- **Action**: consolidate into ROADMAP_MASTER; add brief pointer in FEATURE_ROADMAP.md.

## Glossary
- **Documented**: (GLOSSARY.md is empty).
- **Actual**: terms used across UI/engine.
- **Gap**: missing definitions.
- **Action**: add minimal glossary aligned to ROADMAP_MASTER.

## RF scope guardrails
- **Documented**: RF_SCOPE_GUARDRAILS.md exists.
- **Actual**: guardrails align with feature‑indexed workflow.
- **Gap**: none.
- **Action**: reference in ROADMAP_MASTER.

## Project vision / positioning
- **Documented**: PROJECT_VISION.md, PRODUCT_POSITIONING.md (valid).
- **Actual**: consistent with repo goals.
- **Gap**: none.
- **Action**: mark subordinate to ROADMAP_MASTER.

## Priority actions (summary)
1. **Create canonical roadmap** (done in ROADMAP_MASTER).
2. **Document empty specs** (MAP_ENGINE, UI_UX_SPEC, ANALYSIS_ENGINE, NETWORK_INTELLIGENCE).
3. **Plan data model split** (Phase 1).
4. **Keep UI map‑centric and engine‑only analysis**.
