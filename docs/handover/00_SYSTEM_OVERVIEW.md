# 00 — System Overview (Standalone Handover)

This document is the entry point for an AI that must resume `ogn_tool` **without full repository context**.

## Product Mission
`ogn_tool` is an **OGN Network Intelligence Engine**.
It is not a flight tracker UI. It must answer quickly:
- where the network receives reliably
- where the network is blind
- what a station contributes uniquely vs redundantly
- what operational action should be prioritized

## Architecture (Current, enforced)
- `kernel`: deterministic computation only
- `domain`: semantic contracts / schemas
- `intelligence`: inference, diagnostics, recommendations
- `reporting`: canonical report assembly + projections
- `ui`: display-only projection layer

Hard rule: UI must not recompute business/network logic.

## Runtime Surfaces
- Streamlit app: `apps/dashboard.py`
- FastAPI + static frontend dev server: `apps/api_server.py`
  - `GET /api/payload?run_id=<RUN_ID>`
  - serves `frontend/index.html`
- Vanilla deck.gl frontend:
  - `frontend/app.js`
  - `frontend/rf_layers.js`
  - `frontend/aircraft_layers.js`

## Project Inventory (Top-level)
- `src/ogn_tool/`: main package
  - key subpackages: `data`, `domain`, `intelligence`, `kernel`, `pipeline`, `reporting`, `runtime`, `ui`
- `apps/`: application entrypoints (Streamlit + FastAPI)
- `scripts/`: operational scripts (run generation, quality gate, stability analysis)
- `tests/`: 87 test files at handover time
- `docs/`: extensive architecture and RF docs
- `frontend/`: deck.gl MVP visualization
- `data/runs/analysis_runs/`: generated run artifacts (report.json etc.)

## Current State (Important)
1. RF analytical pipeline works (`rf_signature`, gaps, structure, shadow).
2. UI rendering works technically (deck.gl layers, overlays).
3. Main blocker for decision-grade UI is **data grounding**, not rendering:
   - many runs provide no usable aircraft positions in payload
   - result: abstract "RF pizza" visualization without network insight

## Known Truths
- A run can be valid for RF diagnostics but invalid for network intelligence.
- `aircraft_positions` is required for spatial network reasoning.
- Warnings like Firefox WebGL deprecation are non-blocking.
- CORS confusion appears when mixing `localhost` and `127.0.0.1` manually.

## Non-Goals (for resuming AI)
- Do not redesign frontend before data foundation is fixed.
- Do not add new metrics in UI.
- Do not reintroduce legacy fallback/multi-path report parsing.

## Immediate Resume Rule
Treat project status as:
- `RF diagnostics`: operational
- `Network intelligence`: partially blocked by missing canonical observation layer
