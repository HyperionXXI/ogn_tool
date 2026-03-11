STATUS: canonical
SOURCE_OF_TRUTH: docs/core/ARCHITECTURE_OVERVIEW.md

This document is subordinate to docs/core/ROADMAP_MASTER.md.
If contradictions exist, docs/core/ROADMAP_MASTER.md is the canonical source.

# Architecture Overview

This document provides a compact architecture view for the RF observatory stack.

## Diagram

```
DATA SOURCES
  -> raw_packets
  -> rf_receptions
  -> RF engine
  -> network analysis
  -> UI
```

## Layer intent

- DATA SOURCES: packet and reception inputs from collectors/databases
- RF engine: orchestration and analytical dataset construction
- network analysis: station/network metrics and topology outputs
- UI: map-centric visualization and inspection

