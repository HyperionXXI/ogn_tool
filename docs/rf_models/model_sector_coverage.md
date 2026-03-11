STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Sector Coverage Model

Sector-based modeling captures directional effects in RF reception by
conditioning on bearing.

## Model

SNR(d, θ)

Where:

- d is distance
- θ is azimuth (bearing)

## Rationale

Directional patterns are driven by:

- antenna radiation characteristics
- mounting and obstructions
- terrain shadowing

By estimating SNR distributions per sector, the model can identify
anisotropy and weak directions that are not visible in distance-only
analysis.

## Implementation

src/ogn_tool/analysis/polar.py
src/ogn_tool/analysis/polar_coverage.py

Description:
Sector-based RF coverage estimation using azimuth binning.
