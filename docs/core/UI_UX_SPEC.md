STATUS: canonical
SOURCE_OF_TRUTH: docs/core/UI_UX_SPEC.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# UI / UX Specification

This document defines the user interface for the RF Network Observatory.

The interface is map-centric and object-driven.

## CURRENT IMPLEMENTATION

Current pages found in `apps/dashboard.py` navigation:

- Station Intelligence
- Overview
- Coverage Explorer
- Propagation
- Network
- Diagnostics
- Network Intelligence

Current layout behavior:

- global sidebar filters/navigation
- center content rendering for selected view
- right inspector placeholder in dashboard layout

## TARGET UI

Target UI is an RF Observatory interface built around a three-panel design.

LEFT PANEL

navigation and filters.

CENTER PANEL

interactive map and overlays.

RIGHT PANEL

object inspector with contextual analytics.

Target map layers:

- stations
- aircraft
- reception points
- coverage grid
- blind zones
- network redundancy
- propagation model

Target view families:

- Overview
- Coverage Explorer
- Station Intelligence
- Network Intelligence
- Aircraft Explorer
- Station Lab

Target RF model exposure in UI:

- rf_visibility_model
- rf_blind_zone_detection
- station_placement_optimizer

