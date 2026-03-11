STATUS: canonical
SOURCE_OF_TRUTH: docs/PROJECT_VISION.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

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
