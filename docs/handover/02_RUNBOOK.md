# 02 — Runbook (Operational Resume)

Use this runbook to reproduce the system behavior from scratch.

## Prerequisites
- Python >= 3.11
- virtualenv activated
- dependencies installed (`pip install -e .`)
- for FastAPI UI path: `pip install fastapi uvicorn`

## 1) Launch Modes

### A) Streamlit (legacy consumer UI)
```bash
streamlit run apps/dashboard.py
```

### B) FastAPI + deck.gl frontend
```bash
uvicorn apps.api_server:app --reload
```
Open:
- `http://localhost:8000`
- `http://localhost:8000/api/payload?run_id=<RUN_ID>`

## 2) Useful Scripts

### Run quality gate
```bash
python scripts/run_quality_gate.py --top 50
```

### RF stability comparison
```bash
python scripts/rf_stability_table.py <run1> <run2> <run3>
```

### Multi-station synchronized runs
```bash
python scripts/run_multistation_window.py --stations FK50887,LSPD,LSZG,SOLOTHURN --window-hours 6 --end-offset-hours 7
```

## 3) Validation Sequence (must follow order)
1. Generate/choose runs
2. Apply quality gate
3. Validate RF stability
4. Query `/api/payload`
5. Verify aircraft observation availability
6. Only then evaluate UI usefulness

## 4) Browser Debug Checklist
In browser console (on `http://localhost:8000`):
```js
const r = await fetch('/api/payload?run_id=<RUN_ID>');
const p = await r.json();
console.log('mode', p.metrics?.aircraft_positions?.length ? 'network' : 'rf-only');
console.log('aircraft_positions', p.metrics?.aircraft_positions?.length);
console.log('rf_signature', p.intelligence?.rf_analysis?.rf_signature);
```

Interpretation:
- `aircraft_positions > 0` => network mode possible
- `aircraft_positions == 0` => RF-only diagnostic mode

## 5) Known Non-Issues
- Firefox WebGL warnings (deprecated debug extension, generateMipmap) are non-blocking.
- `/favicon.ico` 404 is non-blocking.

## 6) Known Real Issues
- `localhost` vs `127.0.0.1` mixed fetch causes CORS confusion.
  - Use relative fetch (`/api/payload?...`) or `window.location.origin`.
- If map is blank and `/api/payload` not called, check first red JS error in console.

## 7) Emergency Triage
If UI seems useless:
1. Check `aircraft_positions` count.
2. If zero -> do not tweak colors/layers; fix observation data pipeline.
3. If non-zero but still unreadable -> then tune layer scales/opacity.

## 8) Acceptance Conditions
A run is accepted for network intelligence only if:
- quality gate passes
- aircraft observation layer non-empty
- station coordinates available
- RF signature present
