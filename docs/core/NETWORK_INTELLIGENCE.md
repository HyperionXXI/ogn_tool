STATUS: explanatory
REFERENCE: docs/architecture/ADR-001-project-vision.md

# Network Intelligence

This document describes the current network-intelligence problem space.

For canonical contracts and governance, use:
- `docs/architecture/RF_METRIC_CONTRACT.md`
- `docs/architecture/OBSERVATION_GRAPH_CONTRACT.md`
- `docs/architecture/NETWORK_ENGINEERING_REPORT.md`

## Scope

The network intelligence layer covers:
- visibility matrices
- overlap and redundancy
- station influence
- robustness and SPOF analysis
- placement and gap prioritization
- operator diagnostics

## Practical capabilities

The current engine can support:
- detection of RF coverage gaps
- redundancy analysis
- blind-zone candidates
- simulation of station removal
- empirical station addition simulation
- engineering reporting

## Important limitation

Aircraft tracks alone do not represent RF coverage.
Coverage must be inferred from receptions and multi-station visibility.
