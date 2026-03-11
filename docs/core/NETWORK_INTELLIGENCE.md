STATUS: canonical
SOURCE_OF_TRUTH: docs/NETWORK_INTELLIGENCE.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Network Intelligence

## Coverage inference limitations

Aircraft tracks do not represent RF coverage.

Coverage must be inferred from RF reception events (rf_receptions) and
signal statistics, not from raw APRS/APRS-IS traffic alone. Using only
aircraft position tracks can overstate coverage and hide blind zones.
