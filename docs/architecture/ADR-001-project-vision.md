# ADR-001 — Project Vision

Status: ACCEPTED
Date: 2026-03-13

## Context

This project originated as an experimental tool to ingest and analyse
Open Glider Network (OGN) observations.

Early development focused on data collection and simple visualisation,
mainly through Streamlit dashboards.

While useful for debugging and quick inspection, these dashboards
proved inadequate for analysing spatial RF networks and their
structural properties.

During development the project evolved into a broader ambition:

to build a **network intelligence platform capable of analysing
distributed RF sensing infrastructures.**

Without a clearly documented architectural vision, discussions tend
to repeatedly drift toward UI design or ad-hoc visualisation tools.

This ADR establishes the official architectural direction of the project.

---

## Decision

The project SHALL evolve as a:

**Distributed RF Network Intelligence Platform**

The system analyses networks composed of:

• RF observers (stations, gateways, receivers)  
• targets (aircraft, nodes, devices)  
• visibility relationships between them  

The platform MUST support analysis across multiple RF ecosystems,
including but not limited to:

- OGN / FLARM
- Meshtastic
- LoRaWAN
- APRS
- ADS-B

The system is **protocol-agnostic** and models RF observation networks
as a general class of distributed sensing systems.

---

## Architectural Layers

The architecture follows three clearly separated layers.

### 1 — Data Ingestion

Responsible for collecting RF observations.

Examples:

- OGN APRS streams
- Meshtastic node telemetry
- LoRaWAN gateways
- ADS-B feeds

This layer normalizes observations into a common internal format.

---

### 2 — Analysis Engine

The analytical core of the system.

Responsibilities include computing network intelligence metrics such as:

- visibility matrices
- station influence
- station anomaly detection
- network robustness
- station placement optimisation
- RF coverage modelling

The analysis engine is the **primary product of the project**.

All analytics must remain independent from the UI layer.

---

### 3 — Exploration Interface

An interactive spatial interface named:

**RF Network Explorer**

This interface allows exploration of RF networks and their behaviour.

The interface MUST be:

- map-first
- spatially oriented
- network-centric

The UI is designed for **exploration and understanding of RF systems**,
not for traditional dashboard reporting.

---

## Non-Goals

The project is NOT intended to be:

- a simple aircraft tracking dashboard
- a Streamlit visualization tool
- a UI-driven project
- a protocol-specific monitoring tool

Streamlit MAY be used for:

- debugging
- validation tools
- developer inspection interfaces

but it is **not the intended production UI.**

---

## Consequences

This decision implies:

• the analysis engine is the core of the system  
• UI layers must remain decoupled from analytics  
• development prioritizes RF network intelligence  
• the platform remains protocol-agnostic  

Future architectural discussions MUST assume this vision unless a
new ADR supersedes this document.

---

## Strategic Vision

The long-term goal is to build an exploration platform for RF networks
similar in spirit to:

• **Palantir** (data intelligence platforms)  
• **Starlink network monitoring tools** (large distributed RF systems)

but focused on **open RF sensing infrastructures.**
