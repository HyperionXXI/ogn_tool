# Shadow Coverage Illusion

## Problem

In mountainous RF environments, a station may observe aircraft only through
narrow propagation corridors such as valleys, ridge openings, or high-altitude
paths.

This creates the illusion of wide coverage although the coverage geometry is
fragile and highly directional.

## Impact on Analysis

A planner based only on observation presence may treat such stations as strong
coverage providers even when the effective coverage is concentrated in a very
small angular sector.

## Proposed Metric (v1)

Directional diversity of observations measured using normalized angular entropy.

## Interpretation

- high entropy -> robust omnidirectional coverage
- low entropy -> possible shadow / corridor coverage

## Future Work

- terrain-aware modelling
- multi-station geometric coverage
- propagation corridor detection
