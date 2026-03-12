# Documentation Map

This document defines the role of each architecture document.

Its goal is to prevent documentation drift and overlapping responsibilities.

---

## Documentation hierarchy

ARCHITECTURE.md
  ↓
ARCHITECTURE_OVERVIEW.md
  ↓
SYSTEM_ARCHITECTURE.md
  ↓
RF_ARCHITECTURE.md
  ↓
RF_ANALYSIS_ARCHITECTURE.md
  ↓
RF_DATASET_SCHEMA.md

---

## Architecture entrypoint

ARCHITECTURE.md

Answers:
What is this system and how is it structured at a high level?

Must not contain:
Detailed module design
Dataset definitions
Implementation details

---

## Architecture overview

core/ARCHITECTURE_OVERVIEW.md

Answers:
What are the main subsystems of the project?

Must not contain:
Detailed engine implementation
Module-by-module descriptions

---

## System architecture

core/SYSTEM_ARCHITECTURE.md

Answers:
How the runtime system is structured.

Includes:
layers
packages
runtime boundaries

Must not contain:
RF-specific algorithms

---

## RF conceptual architecture

core/RF_ARCHITECTURE.md

Answers:
How the RF analysis system works conceptually.

Includes:
RF pipeline
analysis levels
network model

Must not contain:
module-by-module implementation details

---

## RF engine architecture

docs/RF_ANALYSIS_ARCHITECTURE.md

Answers:
How the RF engine is implemented.

Includes:
modules
packages
pipeline stages
engines
storage

Must not redefine:
dataset vocabulary

---

## RF dataset schema

core/RF_DATASET_SCHEMA.md

Answers:
What datasets are produced by the RF engine.

Includes:
rf_dataset
network_graph
network_timeseries
network_events
network_evolution

Must not define:
field semantics independently of DATA_CONTRACT.md

---

## Data contract

core/DATA_CONTRACT.md

Answers:
What fields mean and how they map canonically.

Includes:
field naming
units
normalization

Must not describe:
complete datasets or pipeline behavior
