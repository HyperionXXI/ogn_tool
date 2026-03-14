# Observational Coverage Bias

## Problem

OGN observations are biased by:

- existing station placement
- launch sites
- popular cross-country routes
- airspace restrictions

Therefore the dataset over-represents already covered areas.

## Impact on Station Placement

A planner that optimizes only observed aircraft coverage tends to reinforce
existing dense traffic areas instead of identifying underserved airspace.

## Mitigation v1: Spatial Density Normalization

Aircraft observations are weighted inversely to local spatial density.

- dense cell -> lower weight
- sparse cell -> higher weight

This does not remove the observational bias, but it reduces the influence of
already over-sampled areas.

## Future Work

- expected traffic models
- terrain / line-of-sight modelling
- network topology modelling
- adaptive spatial normalization
