# System Architecture

The system follows a strict layered architecture.

collector
↓
database
↓
analysis engine
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

- packets
- station information
- derived coverage grids

The database should remain simple and fast.

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