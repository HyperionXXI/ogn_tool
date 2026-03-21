# RF Validation Protocol

## Scope
This protocol validates RF analysis robustness without adding new RF features.

## Canonical Inputs
- Runs directory: `data/runs/analysis_runs`
- Canonical run files:
  - `report.json`
  - `run_metadata.json`
  - local artifacts (notably `azimuth_distance_surface.json`)

## Source of Truth Rule
Do **not** trust stale `ui_artifact.json` for RF validation.
Use:
- `load_report_from_path()` + `build_dashboard_payload()`
- or scripts that already do this (`rf_stability_table.py`)

## Quality Gate
Use `scripts/run_quality_gate.py` before any RF comparison.

Default strict gate:
- `packet_count >= 500`
- `unique_aircraft >= 10`
- `temporal_coverage_ratio >= 0.5`

Command:
```powershell
python scripts/run_quality_gate.py --valid-only --top 20
```

## Stability Validation (Local)
Goal: check reproducibility under near-identical context.

Command pattern:
```powershell
python scripts/rf_stability_table.py <run1> <run2> <run3> ...
```

Primary fields:
- `corridor_center_deg`
- `dominant_corridor_share`
- `coverage_uniformity_score`
- `rf_gap_structure.largest_gap`

Interpretation:
- all `YES` on same-context runs => stable local behavior

## Robustness Validation (Inter-context)
Goal: verify the model changes when context changes.

Procedure:
1. Select one strict-valid reference run (e.g. day A).
2. Select a run from a different day/context.
3. Compare with `rf_stability_table.py`.

Interpretation:
- `NO` can be expected and healthy if context differs.
- This confirms model responsiveness rather than artificial freezing.

## Campaign Structure
Run 3 comparison sets:
1. Same day, close windows (stability)
2. Different day, valid runs (robustness)
3. Later: other station(s) (generalization)

## Current Baseline (2026-03-21)
Established:
- local stability confirmed on 5 runs from 2026-03-20
- inter-context variation observed vs 2026-03-19 run

## Non-goals During This Phase
- no new RF features
- no kernel changes
- no dashboard feature expansion
- no stability metric redesign (`--ref median` deferred)
