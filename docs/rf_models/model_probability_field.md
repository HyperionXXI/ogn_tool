This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Probability Field Model

Probabilistic coverage expresses the likelihood that a transmission is
successfully received at a location.

## Definition

P_rx = P(SNR > SNR_min)

The SNR distribution is modeled as a function of distance, altitude, and
sector, then converted into a probability field by evaluating the tail
probability above a reception threshold.

## Diagrams

Distance

- Increasing distance → lower expected SNR

Altitude

- Higher altitude → improved line-of-sight → higher expected SNR

Coverage probability

- Locations where P_rx is high are considered reliable coverage zones
- Low P_rx indicates fragile or blind areas

## Implementation

Planned module:
src/ogn_tool/analysis/rf_probability_field.py

Description:
Future probabilistic coverage estimation using distance, altitude, SNR and
direction.
