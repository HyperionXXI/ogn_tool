> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

# Runtime API Migration

## Purpose

This document defines the migration policy from the legacy runtime
context (`ctx[...]`) to the canonical typed runtime API exposed through:

- `RFAnalysisResults`
- its public `results.*` surface

The objective is to eliminate the dual runtime API while maintaining
temporary compatibility during the transition period.

## Canonical Runtime API

The official runtime interface is:

- `results.*`

Examples:

- `results.coverage`
- `results.visibility`
- `results.network_graph`
- `results.network_metrics`

`RFAnalysisResults` is the authoritative source of analytical outputs.

All new runtime consumers must use this interface.

## Legacy Runtime Context

The following runtime structure exists for historical reasons:

- `ctx["dataset"]`
- `ctx["network_analysis"]`
- `ctx[...]`

These paths are legacy compatibility only.

They must not be considered authoritative definitions of analytical
results.

No new code should introduce additional `ctx[...]` consumers.

## Migration Rule

During the migration phase:

- `results.*` = official runtime API
- `ctx[...]` = legacy compatibility layer

New code:

- MUST use `results.*`
- MUST NOT introduce new `ctx[...]` accesses

Existing code:

- may temporarily read `ctx[...]`
- should be migrated when touched

## Migration Strategy

The migration is incremental and non-breaking.

Steps:

1. Audit current `ctx[...]` usages.
2. Identify the equivalent `results.*` path.
3. Update consumers module by module.
4. Remove the legacy path only when no consumers remain.

Practical rule:

When modifying a module that still uses `ctx[...]`, the consumer should
be migrated to `results.*` as part of the same change whenever this can
be done without broad refactoring.

Migration should avoid large refactors and focus on small localized
changes.

## Known Legacy Paths

Current known legacy runtime paths include:

- `ctx["dataset"]`
- `ctx["network_analysis"]`

Additional paths may exist in older UI modules or developer tooling.

These should be gradually replaced with the appropriate typed surface,
depending on the metric family, for example:

- `results.coverage`
- `results.network_metrics`
- `results.network_graph`
- `results.metrics`

## UI Consumer Policy

UI modules should treat the analytical engine as a read-only data
provider.

UI code may:

- format values
- filter rows
- sort tables
- select subsets

UI code must not:

- recompute analytical metrics
- change metric semantics
- derive incompatible data structures

All analytical logic must remain inside:

- `analysis/`
- `pipeline/`

## Deprecation Policy

Legacy runtime paths (`ctx[...]`) will be removed once:

- all known consumers are migrated
- the runtime API surface is stable

The removal will be performed in a dedicated cleanup change to avoid
breaking unrelated work.

## Summary

The runtime migration follows three simple rules:

- `results.*` is the official runtime API
- `ctx[...]` is legacy compatibility only
- no new `ctx[...]` consumers are allowed

This policy ensures that the analytical engine exposes a single,
stable runtime surface while allowing a safe incremental transition
from the legacy context model.
