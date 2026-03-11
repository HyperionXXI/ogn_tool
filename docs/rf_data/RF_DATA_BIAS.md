STATUS: derived
REFERENCE: docs/core/ROADMAP_MASTER.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Data Bias

## Problem

RF datasets such as `rf_receptions` contain only successful receptions.

This creates a selection bias when estimating RF coverage.

Observed distribution:

P(distance | received)

Desired model:

P(received | distance)

## Implication

Using reception-only data overestimates coverage probability.

## Mitigation strategies

1. Transmission rate estimation
2. Multi-station inference
3. SNR threshold modeling

## Future work

Introduce a module:

analysis/reception_probability_inference.py

This module will estimate reception probability
using multi-station comparisons.

