Network Engineering Report
=========================

> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

See also:
	- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
	- [INDEX.md](INDEX.md)

Purpose
-------

Provide a structured interpretation layer for RF analysis results.

The report consumes metrics produced by the analysis layer
and generates engineering diagnostics useful for understanding
network behavior.

Layering rule
-------------

analysis   -> compute metrics
reporting  -> interpret metrics
runtime    -> orchestrate analysis

The reporting layer must NOT perform RF computations.

Input
-----

results.network_metrics

Expected metrics currently include:

- station_health
- station_angular_entropy
- shadow_risk_scores
- network_summary
- station_dependency
- network_robustness

Output
------

A typed NetworkEngineeringReport containing:

- station diagnostics
- network summary
- future space for network-level diagnostics

Future extensions may include:

- station dominance
- network redundancy
- propagation corridors
