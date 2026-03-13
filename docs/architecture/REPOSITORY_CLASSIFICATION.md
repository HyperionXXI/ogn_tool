# Repository Classification

This document classifies the main modules of the repository
according to their architectural status.

The goal is to clarify which parts of the codebase are considered
canonical, transitional, legacy, or experimental.

This prevents architectural drift during future development.

---

## Canonical modules

These modules define the core architecture of the project and should
remain stable.

| Module | Notes |
|------|------|
| `src/ogn_tool/models` | Core typed data structures |
| `src/ogn_tool/analysis` | RF and network analytics kernel |
| `src/ogn_tool/pipeline` | Analytical pipeline orchestration |
| `src/ogn_tool/runtime` | Runtime boundary between UI and engine |
| `src/ogn_tool/services/rf_analysis_service.py` | Runtime entry point |

These modules form the **core analytical engine** of the project.

---

## Semi-canonical modules

These modules are conceptually important but still evolving.

| Module | Notes |
|------|------|
| `src/ogn_tool/analysis/network_metrics` | Core network intelligence metrics |
| `src/ogn_tool/analysis/network_graph` | Graph construction layer |
| `src/ogn_tool/analysis/intelligence` | Higher-level heuristics (scope still evolving) |

The boundaries between these modules should remain clear.

---

## Transitional modules

These modules exist mainly to maintain compatibility with previous
architectural layers.

They should not receive significant new features.

| Module | Problem | Future |
|------|------|------|
| `src/ogn_tool/engine/rf_engine_dataset_builder.py` | Legacy dataset assembly | reduce gradually |
| `src/ogn_tool/engine/rf_dataset_builder.py` | overlapping responsibility | clarify or empty |
| `src/ogn_tool/engine/rf_engine_network.py` | historical compatibility | remove eventually |
| `apps/dashboard.py` | mixed typed/legacy runtime | reduce gradually |
| `apps/ui/map_engine/layers.py` | legacy dataset assumptions | migrate later |

---

## Legacy modules

These modules have weak architectural value and should be audited.

| Module | Problem |
|------|------|
| `src/ogn_tool/engine/results.py` | unclear role after typed results |

These modules should eventually be removed or absorbed elsewhere.

---

## Documentation layers

| Directory | Status |
|------|------|
| `docs/core` | canonical documentation |
| `docs/architecture` | architectural decisions and audits |
| `docs/internal` | working notes and developer references |

Only `docs/core` and `docs/architecture` should be treated as
authoritative documentation.

---

## Local artifacts

The following files are not part of the source architecture and should
not remain in the repository.

Examples:

- `REFACTOR_WORK_LOG.txt`
- `repo_tree.txt`
- `tree.txt`
- `symbols.txt`
- `ogn_tool.svg`

These should either be removed or ignored via `.gitignore`.

---

## Architectural priorities

### Stable center

The architectural center of the project is now:

- `models`
- `analysis`
- `pipeline`
- `runtime`

This structure should remain stable.

### Transitional layers

The `engine` layer still contains legacy adapters and should gradually
shrink as the typed runtime becomes the only execution path.

### UI evolution

UI components should migrate progressively to typed data contracts
without large refactors.

---

## Governance Rule

Every architectural change must update `REPOSITORY_CLASSIFICATION.md`.
