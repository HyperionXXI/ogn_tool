STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Log-Distance Model

The classical log-distance path loss model is used to describe the expected
signal-to-noise ratio (SNR) as a function of distance.

## Model

SNR(d) = a − b log(d)

Where:

- d is distance (km)
- a is the reference SNR at unit distance
- b is the path loss exponent (slope)

## Fitting procedure

- Bin receptions by distance.
- Compute median or mean SNR per bin.
- Fit a linear model in log-distance space to estimate a and b.

This model provides a simple baseline for propagation and is used to build
probability fields when additional predictors are not available.

## Implementation

src/ogn_tool/analysis/signal_distance.py

Description:
The RSSI vs distance analysis estimates propagation behavior empirically using
packet observations.
