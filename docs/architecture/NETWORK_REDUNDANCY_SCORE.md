Network Redundancy Score
========================

Purpose
-------

Provide an intelligence-layer summary of how redundant the network is, using
existing metrics already produced by the analysis and runtime pipeline.

Layering rule
-------------

analysis.intelligence aggregates existing signals. It must not compute new
RF low-level metrics.

Inputs
------

The score consumes existing network metrics, especially:

- visibility["summary"]
- station_dominance
- station_dependency
- network_robustness

Signals
-------

- mean_stations_per_aircraft
- single_station_ratio
- mean_dominance_ratio
- high_dependency_station_ratio

Formula (v1)
------------

score =
    0.35 * min(mean_stations_per_aircraft / 4, 1)
    + 0.25 * (1 - single_station_ratio)
    + 0.20 * (1 - mean_dominance_ratio)
    + 0.20 * (1 - high_dependency_station_ratio)

Then clamp score to [0, 1].

Interpretation
--------------

- >= 0.85: very high redundancy
- >= 0.70: good redundancy
- >= 0.50: moderate redundancy
- >= 0.30: fragile network
- < 0.30: critical network

Output
------

A dict containing the score, the component values, and a short interpretation.

Future work
-----------

Future versions may include weighted dominance, station quality, distance,
RSSI, and terrain-informed robustness signals.
