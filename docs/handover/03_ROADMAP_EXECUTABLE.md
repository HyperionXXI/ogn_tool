# 03 — Roadmap Executable (P0 / P1 / P2)

This roadmap is intended for direct execution by a coding agent.

## P0 — Network Observation Foundation (BLOCKER)

### Goal
Guarantee canonical `aircraft_observations` and a stable UI projection (`metrics.aircraft_positions`).

### Scope
- Build observation extraction from real run window + station scope
- Correlate `seen_by` from multi-station packet evidence
- Expose projection in payload additively
- Preserve existing payload keys

### Definition of Done
- `metrics.aircraft_positions` exists for target runs
- each item has `src|aircraft_id`, `lat`, `lon`, `seen_by[]`
- no heuristic-only `seen_by`
- run mode is explicit (`RF-only` vs `Network intelligence`)

### Non-goals
- no UI redesign
- no new intelligence metrics yet

---

## P1 — Spatial Network Features

### Goal
Produce actionable spatial features from canonical observations.

### Scope (backend/reporting only)
- `coverage_density`
- `unique_coverage`
- `shared_coverage`
- `blind_zones`
- `grid_meta`

### Definition of Done
- features are present in payload on network-valid runs
- reproducible on same run input
- bounded and documented value ranges
- no computation moved to frontend

### Non-goals
- avoid adding scenario/counterfactual engine here

---

## P2 — Decision UI

### Goal
Render network value in < 3 seconds.

### Scope (frontend only)
- unique heatmap = primary
- shared heatmap = secondary
- blind overlay = high contrast
- RF cone/gaps = contextual, non-primary
- compact verdict card

### Definition of Done
A new operator can answer without docs:
- where station adds value
- where station is redundant
- where network is blind
- what to prioritize

### Non-goals
- no business logic in UI
- no backend contract drift

---

## Execution Rules for Agents
1. Never start P1/P2 before P0 is validated.
2. Any run with empty observations is `RF-only` and must be labelled as such.
3. Use additive contract evolution only.
4. Verify on real run artifacts, not synthetic mocks.

---

## Suggested Delivery Sequence
1. P0 payload contract + extractor + validation tests
2. P1 spatial feature builder + contract tests
3. P2 deck.gl rendering pass + UX acceptance checklist

---

## Metrics to Track During Implementation
- `% runs with non-empty aircraft_observations`
- median `aircraft_positions` count per valid run
- `% UI sessions in RF-only mode`
- time-to-insight (manual stopwatch, <= 3s target)
