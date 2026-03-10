This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Altitude-Distance Model

Altitude-dependent propagation extends the log-distance model by adding an
altitude term to capture line-of-sight transitions.

## Model

SNR(d, h) = a − b log(d) + c h

Where:

- d is distance (km)
- h is aircraft altitude (km or m, consistent with data normalization)
- a is the reference SNR at unit distance
- b is the path loss exponent (slope)
- c models altitude gain (line-of-sight benefit)

## Interpretation

As altitude increases, the probability of line-of-sight improves, often
increasing effective SNR at a given distance. The altitude coefficient c
captures this effect and is fitted using multi-variable regression.

## Implementation

src/ogn_tool/analysis/signal_distance.py

Description:
Altitude-aware distance analysis is derived from reception observations and is
integrated into the RF propagation metric pipeline.
