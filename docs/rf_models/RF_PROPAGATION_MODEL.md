STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Propagation Model

## 1. RF Observation Model

The system transforms APRS packets into RFObservation objects.

Pipeline:

packets
→ RFEvent
→ RFObservation
→ RF analysis

## 2. Implemented RF models

Existing analysis modules include:

- signal_distance.py
- polar.py
- polar_coverage.py
- rf_diagnosis.py

The tool already performs:

- RSSI vs distance analysis
- polar directional coverage analysis
- station RF health diagnostics

## 3. Limitations of track-based coverage

Aircraft tracks are not RF coverage.

Coverage must be modeled as a conditional probability:

P(reception | distance, altitude, azimuth)

## 4. Proposed probabilistic RF model

Probabilistic coverage is modeled as:

P(receive) = f(distance, altitude, direction)

Based on:

- SNR measurements
- distance
- packet statistics

Clarification:
Current models are empirical and observation-driven. The probability field
model is the next step for coverage inference.

## 5. Future modules

Planned modules include:

- rf_probability_field.py
- antenna_pattern_estimator.py
- propagation_model.py
