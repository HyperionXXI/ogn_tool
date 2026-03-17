> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

Station Dominance
==================

Purpose
-------

Provide an intelligence-layer metric describing how strongly each station
dominates observed aircraft coverage within the network.

Definition
----------

For each station:

- total_aircraft_count: number of distinct aircraft observed by the station
- unique_aircraft_count: number of aircraft observed only by that station
- shared_aircraft_count: number of aircraft observed by that station and at least one other station
- dominance_ratio: unique_aircraft_count / total_aircraft_count
- dominance_rank: rank of the station by dominance_ratio, then unique_aircraft_count

Interpretation
--------------

- dominance_ratio near 1.0 indicates a station provides mostly unique coverage
- dominance_ratio near 0.0 indicates the station is largely redundant

Inputs
------

- observations as a pandas DataFrame
- optional network_metrics for future compatibility

Output
------

A pandas DataFrame with one row per station containing the fields above.

Layering rule
-------------

analysis.intelligence interprets network structure from canonical observation
surfaces. It does not perform low-level RF modelling.

Future use
----------

This metric is intended to support future network-level metrics such as:

- network redundancy score
- station criticality summaries
- engineering report interpretation
