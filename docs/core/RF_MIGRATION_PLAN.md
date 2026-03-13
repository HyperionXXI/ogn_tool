STATUS: historical
REFERENCE: docs/core/RF_ARCHITECTURE.md

# RF Migration Plan

This document is retained as a historical migration note.

The original migration described here has largely been completed.
The current canonical architecture is described in:
- `docs/core/RF_ARCHITECTURE.md`
- `docs/core/SYSTEM_ARCHITECTURE.md`
- `docs/architecture/REPOSITORY_CLASSIFICATION.md`
- `docs/architecture/RUNTIME_API_MIGRATION.md`

## Historical intent

The original migration goals were:
- introduce a clear normalization boundary
- stabilize typed engine contracts
- reduce direct UI dependence on legacy dataset structures
- remove silent compatibility fallbacks over time

## Current outcome

Most of this migration has already happened through:
- `src/ogn_tool/analysis/normalization/`
- `src/ogn_tool/models/rf_analysis_dataset.py`
- `src/ogn_tool/models/rf_analysis_results.py`
- `src/ogn_tool/runtime/`
- typed-first UI migration in selected pages

## Recommendation

Do not use this file as a current implementation guide.
Use it only as historical context for why the architecture was changed.
