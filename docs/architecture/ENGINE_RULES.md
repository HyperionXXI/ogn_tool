# Engine Rules

This document defines architectural rules for the `engine/` layer.

Its purpose is to prevent the reintroduction of analytical logic into
transitional engine modules during the migration from the legacy runtime
to the typed analytical kernel.

## Role of the Engine Layer

The `engine/` layer is responsible for:

- orchestrating analytical execution
- assembling runtime inputs and outputs
- bridging typed runtime calls to the analytical pipeline
- maintaining compatibility during migration when strictly necessary

The `engine/` layer is not the canonical home of RF analytics,
normalization semantics, or network intelligence logic.

## Engine Builder Rule

Modules located in `engine/*builder.py` may assemble or adapt datasets,
but must not become canonical sources of analytics, normalization
semantics, or network intelligence logic.

All analytical logic belongs in:

- `src/ogn_tool/analysis/`
- `src/ogn_tool/pipeline/`
- `src/ogn_tool/models/`

## Transitional Builder Modules

The following files are considered transitional:

- `src/ogn_tool/engine/rf_engine_dataset_builder.py`
- `src/ogn_tool/engine/rf_dataset_builder.py`

These files exist to support migration and compatibility.

They must not receive:

- new analytical computations
- new RF metrics logic
- new network metrics logic
- new normalization semantics
- new business rules related to analysis

They may receive only:

- compatibility fixes
- assembly logic
- adapter logic
- deprecation-oriented cleanup

## Canonical Direction

The canonical data flow of the project is:

`normalization -> typed dataset -> analysis -> network metrics -> results`

The engine layer should progressively shrink toward orchestration-only
responsibilities as the typed runtime becomes the primary execution path.

## Intelligence Layer Rule

Modules under `analysis/intelligence/` must never recompute RF metrics
or network metrics.

They operate only on outputs of:

- `analysis/rf_metrics/`
- `analysis/network_metrics/`
- `analysis/network_graph/`

The intelligence layer is reserved for:

- interpretation
- operator-facing synthesis
- rule-based diagnostics
- explainable decision support

It must not:

- access raw datasets directly
- reconstruct network structures already produced elsewhere
- re-estimate metrics already defined in the analytical layers

## UI Rule

UI modules may:

- format values
- filter rows
- sort tables
- select subsets for display

UI modules must not:

- recompute analytical metrics
- implement operator diagnostics logic
- redefine metric semantics

## Governance

Any change that introduces new analytical logic inside `engine/`
requires an explicit architectural justification.

If a feature can be implemented in `analysis/` or `pipeline/`, it must
not be implemented in an engine builder module.
