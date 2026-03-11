STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Model Hierarchy

## Empirical RF models

Observation-driven analyses derived directly from reception data, such as
signal vs distance and azimuth sector coverage. These models summarize
measured behavior without explicit propagation assumptions.

## Statistical propagation models

Models that fit propagation parameters (e.g., log-distance slope and
altitude effects) to explain SNR trends as a function of distance and
altitude. These act as intermediate layers between raw observations and
probabilistic coverage.

## Probabilistic coverage models

Models that estimate the probability of reception at a location:

P(receive) = f(distance, altitude, direction)

These models enable coverage probability fields, blind zone inference, and
network-level reliability metrics.
