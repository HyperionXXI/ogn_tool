STATUS: temporary
REFERENCE: docs/core/ROADMAP_MASTER.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Documentation Consolidation Plan

## Scope

Reduce fragmentation across RF model documentation without changing existing
content yet.

## Overlaps identified

- docs/RF_PROPAGATION_MODEL.md overlaps with docs/rf_models/rf_models_overview.md
  (pipeline, model status, and conceptual overview).

- docs/RF_MODEL_HIERARCHY.md overlaps with docs/RF_PROPAGATION_MODEL.md
  (empirical → statistical → probabilistic model hierarchy).

- docs/rf_models/rf_models_overview.md overlaps with docs/RF_PROPAGATION_MODEL.md
  (implemented vs planned models).

## Proposed merges

1) Merge docs/RF_MODEL_HIERARCHY.md into docs/RF_PROPAGATION_MODEL.md.
   - Move hierarchy sections into RF_PROPAGATION_MODEL.md.

2) Merge docs/rf_models/rf_models_overview.md into docs/RF_PROPAGATION_MODEL.md.
   - Keep model status (implemented/future) in the canonical doc.

3) Keep docs/rf_models/* as model reference sheets only.
   - Remove rf_models_overview.md after content is migrated.

4) Optionally merge docs/rf_models/rf_pipeline.md into docs/RF_PROPAGATION_MODEL.md.

## Reduced documentation structure

- docs/RF_PROPAGATION_MODEL.md
  - Vision + pipeline + hierarchy + implementation status

- docs/rf_models/
  - model_log_distance.md
  - model_altitude_distance.md
  - model_sector_coverage.md
  - model_probability_field.md

- docs/RF_PROPAGATION_MODEL.md absorbs the overview and hierarchy content.

## Execution notes

- No content changes in this plan.
- Actual merges should be done in a follow-up change set.

