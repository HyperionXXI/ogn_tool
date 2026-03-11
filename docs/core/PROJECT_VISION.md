STATUS: canonical
SOURCE_OF_TRUTH: docs/PROJECT_VISION.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# OGN Network Intelligence Platform

## Vision

This project aims to create a **Network Intelligence Platform for OGN / FANET reception networks**.

The system analyses:

- RF reception quality
- spatial coverage
- multi-station interactions
- network redundancy
- blind zones
- station contribution

The goal is to go beyond existing tools such as:

- GliderRadar
- OGN Range Analyzer
- Burnair visualisation tools

The platform should combine the capabilities of:

- a **GIS platform**
- a **radio propagation analysis tool**
- a **network analysis tool**

This concept can be described as:

"Palantir for the OGN network"

---

## Scientific RF exploration tool

The UI is designed as an exploratory RF analysis tool, not as a BI dashboard.

The primary interaction model is: map-driven exploration, object inspection,
and iterative hypothesis testing on RF coverage and network topology.

---

## Key Questions

The platform must allow users to answer:

### Station level

- Does my station work correctly?
- What is the real RF coverage?
- Which directions are weak?
- Does terrain limit reception?

### Network level

- What does my station contribute to the network?
- Is my station redundant or complementary?
- Where are the coverage gaps?

### Planning level

- Where should a new station be installed?
- Would it improve the network?


---

## Flight Intelligence (Free Flight)

The RF analysis architecture enables a higher-level flight intelligence layer on top of OGN reception data.

Potential capabilities include:

- thermal hotspot detection
- transition corridor analysis
- altitude layer analysis
- flight path clustering

These capabilities depend on the **aircraft state layer** defined in the architecture.

The aircraft state layer separates unique aircraft position/time states from RF reception multiplicity,
which allows flight behavior analysis without conflating transport-level reception noise.

### Flight Intelligence Pipeline

```
aircraft states
  ↓
flight tracks
  ↓
climb detection
  ↓
thermal clusters
  ↓
thermal corridors
```

---

## Network Coverage Optimization

The RF analysis engine can be used to evaluate the impact of new OGN stations before deployment.

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
