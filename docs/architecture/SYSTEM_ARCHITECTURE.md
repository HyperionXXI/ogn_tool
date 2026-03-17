# System Architecture (Canonical Pivot)
Status: Canonical Architecture Specification

This document is the central reference for the ogn_tool system architecture. All architectural decisions, contracts, and module boundaries must be consistent with this document.

## Table of Contents
1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Canonical Data Artifacts](#canonical-data-artifacts)
4. [Analytics Engines](#analytics-engines)
5. [Reporting and UI](#reporting-and-ui)
6. [Specialized Architecture Documents](#specialized-architecture-documents)

---

## Overview
- Defines the layered architecture of ogn_tool
- Ensures separation of concerns and clear module boundaries
- All other architecture documents must reference this as the source of truth

---


## Architecture Layers

```
APRS / OGN data
   ↓
Data repositories
   ↓
RF Engine
   ↓
Analysis primitives (src/ogn_tool/analysis/)
   ↓
Analytics Engines (network_intelligence, spatial_intelligence, temporal_intelligence, scenario_intelligence)
   ↓
report.json (canonical artifact)
   ↓
Reporting (src/ogn_tool/reporting/)
   ↓
UI / dashboards (apps/)
```

---

## Canonical Data Artifacts
- **report.json**: The central contract between analytics engines and reporting
- [See NETWORK_ANALYTICS_ENGINE.md for details](NETWORK_ANALYTICS_ENGINE.md)

---


## Analytics Engines
- Four main engines: network_intelligence, spatial_intelligence, temporal_intelligence, scenario_intelligence
- Each engine has a clear API and responsibility
- scenario_intelligence is responsible for network planning, scenario simulation, station addition/removal, scenario ranking, and optimization
- [See NETWORK_ANALYTICS_ENGINE.md for APIs, contracts, and dependency rules](NETWORK_ANALYTICS_ENGINE.md)

---

## Reporting and UI
- Reporting layer consumes analytics engine outputs
- UI/dashboard consumes reporting outputs
- No direct dependency from UI to analytics engines or analysis primitives

---

## Specialized Architecture Documents
- [NETWORK_ANALYTICS_ENGINE.md](NETWORK_ANALYTICS_ENGINE.md): Analytics engine architecture, APIs, and contracts
- ENGINE_RULES.md: Rules for engine builders, module boundaries, and migration
- DATA_CONTRACT.md: Canonical data schemas and versioning

---

## Status
This document is the single source of truth for ogn_tool system architecture. All changes to architecture must be reflected here and referenced by specialized documents.
