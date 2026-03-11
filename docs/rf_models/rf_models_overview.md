STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Models Overview

RF coverage in this project is modeled probabilistically based on RF reception
observations.

## Dataset

The core dataset is `rf_receptions`, which provides reception events with:

- distance
- bearing
- snr
- altitude
- receiver

These receptions are normalized into observations and fed into RF metrics and
propagation models.

## Modeling pipeline

rf_receptions
    → rf_observations
    → rf_metrics
    → propagation_model
    → probability_field

## Implemented models

- signal_distance.py
- polar.py
- polar_coverage.py
- rf_diagnosis.py

These are empirical, observation-driven models derived from reception data.

## Future models

- rf_probability_field.py
- antenna_pattern_estimator.py
- propagation_model.py

The probability field is the next step for coverage inference.

## Implementation

This document provides the conceptual overview. Model-specific implementations
are documented in the individual model files in this directory.
