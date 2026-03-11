STATUS: canonical
SOURCE_OF_TRUTH: docs/SYSTEM_ARCHITECTURE.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# System Architecture

The system follows a strict layered architecture.

collector
↓
database
↓
rf_receptions
↓
rf_metrics
↓
network_intelligence
↓
ui

---

## collector

Responsible for:

- connecting to APRS-IS
- receiving packets
- parsing
- storing into SQLite

No RF analysis happens here.

---

## database

SQLite database storing:

- packets (raw APRS/APRS-IS traffic)
- rf_receptions (RF reception events)
- station information
- derived coverage grids

The database should remain simple and fast.

---

## RF reception layer

RF analysis is performed on `rf_receptions`, not on raw `packets`.

`packets` represent network traffic, while `rf_receptions` represent
receiver-level RF events used by the RF metrics pipeline.

---

## analysis engine

Responsible for all calculations:

- station RF analysis
- spatial coverage
- network analysis
- simulation

The engine must not depend on the UI.

---

## UI

Streamlit-based interface responsible only for:

- visualization
- interaction
- exploration

