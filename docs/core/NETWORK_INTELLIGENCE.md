STATUS: canonical
SOURCE_OF_TRUTH: docs/NETWORK_INTELLIGENCE.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Network Intelligence

## Coverage inference limitations

Aircraft tracks do not represent RF coverage.

Coverage must be inferred from RF reception events (rf_receptions) and
signal statistics, not from raw APRS/APRS-IS traffic alone. Using only
aircraft position tracks can overstate coverage and hide blind zones.


## Network Coverage Optimization

The RF analysis engine can be used to evaluate the impact of new OGN stations and support network planning decisions.

Potential capabilities include:

- detection of RF coverage gaps
- station redundancy analysis
- blind zone detection
- simulation of candidate station locations
- network coverage gain estimation

### Conceptual Planning Pipeline

```
coverage_grid
  ↓
blind_cells
  ↓
candidate_station_locations
  ↓
coverage_simulation
  ↓
optimal_station_positions
```
