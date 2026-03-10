This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# UI Architecture

## 1. UI philosophy

The UI is structured in three levels:

- Level 1 – Situation awareness (Dashboard)
- Level 2 – Investigation (Propagation / Station)
- Level 3 – Scientific analysis (RF Observatory)

---

## 2. RF observation model

RF analysis is based on `rf_receptions`.

Packets are only used for APRS parsing.

---

## 3. Page roles

- Dashboard
- Network
- Stations
- Propagation
- Terrain
- RF Observatory
- Diagnostics
- Aircraft

---

## 4. Design principle

The tool is not an OGN viewer.
It is an RF analysis environment for the OGN network.
