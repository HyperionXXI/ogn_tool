# Architecture Cleanup Plan

Date: 2026-03-12

Scope:
- `src/ogn_tool`
- `apps/ui`
- architecture simplification only

Goal:
Reduce structural duplication without changing RF behaviour.

---

## Phase 0 — Architecture freeze

Objective:
Capture a stable baseline before cleanup.

Recommended action:
- create a git tag before structural cleanup
- export the current import graph
- export the current repository tree
- keep the audit documents as reference points

Suggested commands:
- `git tag architecture-pre-cleanup`
- import graph export
- repo tree export

Success criteria:
- a known-good baseline exists
- cleanup can always be compared against a frozen reference

---

## Phase 1 — UI source of truth

Objective:
Choose a single canonical UI tree.

Current problem:
Two UI trees coexist:
- `apps/ui/*`
- `src/ogn_tool/ui/*`

Risks:
- duplicated routing
- duplicated rendering logic
- ambiguous ownership of pages and layout

Target:
Keep one canonical UI implementation.

Recommended action:
- decide whether `apps/ui` or `src/ogn_tool/ui` is canonical
- convert the non-canonical tree into thin compatibility wrappers only
- remove duplicated page logic after migration is complete

Files to review first:
- `src/ogn_tool/ui/dashboard.py`
- `src/ogn_tool/ui/sections.py`
- `apps/dashboard.py`
- `apps/ui/pages/*`

Success criteria:
- one UI tree owns routing
- one UI tree owns page implementation
- compatibility wrappers, if kept, are explicit and temporary

---

## Phase 2 — Remove legacy wrapper paths

Objective:
Reduce fake module depth and historical aliases.

Current problem:
Many legacy compatibility wrappers are still importable.

Examples:
- `src/ogn_tool/rf_probability_field.py`
- `src/ogn_tool/intelligence/__init__.py`
- `src/ogn_tool/analysis/radio_horizon.py`
- `src/ogn_tool/analysis/terrain.py`
- `src/ogn_tool/analysis/terrain_visibility.py`
- `src/ogn_tool/analysis/rf_visibility_model.py`
- `src/ogn_tool/analysis/altitude_distance.py`
- `src/ogn_tool/analysis/grid.py`
- `src/ogn_tool/analysis/grid_loader.py`

Risks:
- multiple valid import paths for the same concept
- documentation drift
- higher refactor cost

Target:
All imports must resolve to canonical package locations only.

Recommended action:
- replace remaining imports to wrapper modules with canonical paths
- keep wrappers only during migration
- remove wrappers in a dedicated cleanup pass

Canonical destinations:
- `analysis/rf_models/*`
- `analysis/geo/*`
- `analysis/intelligence/*`
- `analysis/rf_probability_field.py`

Success criteria:
- no production import uses a legacy wrapper path
- wrappers are either deleted or clearly marked compat-only

---

## Phase 3 — Consolidate network and engine support modules

Objective:
Remove overlapping internal module families.

Current problem:
Two network analysis families coexist:
- `analysis/network/*`
- `analysis/network_graph/*`

Several engine helpers also overlap:
- `rf_dataset_builder`
- `rf_engine_dataset_builder`
- `rf_engine_observations`
- `rf_engine_network`
- `observation_builder`

Risks:
- same concept implemented at two abstraction levels
- dataset and graph logic split across multiple support modules
- future refactors become expensive and brittle

Target:
A single clear path for:
- RF observation production
- network analysis
- engine support logic

Recommended action:
- define whether `analysis/network/*` remains a dataframe-oriented layer
  or is fully absorbed by `analysis/network_graph/*`
- merge or retire duplicated engine helpers
- keep `rf_engine.py` as orchestrator only

Files to review first:
- `src/ogn_tool/engine/rf_dataset_builder.py`
- `src/ogn_tool/engine/rf_engine_dataset_builder.py`
- `src/ogn_tool/engine/rf_engine_observations.py`
- `src/ogn_tool/engine/rf_engine_network.py`
- `src/ogn_tool/analysis/network/network_intelligence.py`
- `src/ogn_tool/analysis/network_analysis.py`
- `src/ogn_tool/analysis/network_graph/*`

Success criteria:
- one network analysis model is canonical
- one observation builder path is canonical
- engine helper module count is reduced

---

## Validation After Each Phase

Run after every cleanup step:

- `pytest -q`
- `python -m compileall src apps`
- `lint-imports`
- `pydeps src/ogn_tool --show-cycles --noshow`
- `vulture src/ogn_tool --min-confidence 90`

---

## Final Expected State

Architecture should converge toward:

- one UI tree
- one canonical import path per concept
- one network analysis family
- one engine support path per responsibility
- compatibility wrappers reduced to zero or near zero

This cleanup is structural only.
It should not alter RF algorithms or dashboard behaviour.
