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
