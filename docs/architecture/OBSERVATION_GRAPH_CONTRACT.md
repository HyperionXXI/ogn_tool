# Observation Graph Contract

This document defines the minimal canonical multi-station observation
model required for future network-centric RF analysis.

Its purpose is to provide a stable conceptual contract for metrics that
cannot be modeled cleanly from station-centric analysis alone.

This document does not introduce a new pipeline or immediate refactor.
It defines the target model for progressive integration.

---

## Purpose

The current RF analytical core remains largely station-centric for RF
coverage and diagnostics.

However, network intelligence metrics such as:

- visibility
- station influence
- network robustness
- station placement

increasingly depend on a multi-station view of observations.

The Observation Graph is the minimal canonical structure intended to
support that future evolution.

---

## Canonical Source

The canonical source for the Observation Graph is:

- `dataset.observations`

The Observation Graph must be built from analytical observations, not
from UI context, dashboard state, or other runtime-only surfaces.

---

## Core Entities

### `ObservationNode`

Represents a target observation in space and time.

Required fields:

- `observation_id: str`
- `protocol: str`

Recommended fields:

- `target_id: str | None`
- `lat: float | None`
- `lon: float | None`
- `altitude_m: float | None`
- `timestamp: float | int | None`

Fields required for spatial network metrics:

- `lat`
- `lon`

Field required for temporal network metrics:

- `timestamp`

Semantic meaning:
- one logical observed event or target position
- potentially heard by one or more stations
- protocol-aware to support future multi-protocol networks

`observation_id` identifies one logical analytical observation, not
necessarily one raw RF packet. Its construction may depend on
protocol-specific normalization or grouping rules.

Examples of protocol values:

- `OGN`
- `FLARM`
- `FANET`
- `APRS`
- `ADS-B`

---

### `StationReception`

Represents the reception of an observation by a station.

Required fields:

- `observation_id: str`
- `station_id: str`
- `received_at_timestamp: float | int | None`

Optional analytical fields:

- `rssi: float | None`
- `snr: float | None`
- `distance_km: float | None`
- `bearing_deg: float | None`

Semantic meaning:
- one station hearing one observation
- multiple `StationReception` rows may point to the same
  `ObservationNode`
- this is the key structure enabling overlap, redundancy, influence,
  and station removal analysis

---

### `ObservationGraph`

Minimal container composed of:

- `observations: list[ObservationNode]`
- `receptions: list[StationReception]`

Optional future fields:

- `metrics: dict`

Semantic meaning:
- a network-centric view of observed targets and the stations that heard
  them
- a canonical bridge between packet-level observations and network
  intelligence metrics

The Observation Graph is initially defined as an internal analytical
contract. It is not automatically part of the public runtime API.

---

## Architectural Role

The Observation Graph is intended to support metrics that require true
multi-station context, such as:

- station overlap
- aircraft dependency
- redundancy surfaces
- station influence
- station removal impact
- station placement scoring

It is not intended to replace the current RF station-centric pipeline in
one step.

---

## Integration Strategy

### Phase 1

- define the contract
- add a minimal builder in the analytical layer
- use it only in the network analysis path

### Phase 2

- progressively migrate network metrics to this canonical structure
- keep RF diagnostics unchanged
- once a canonical Observation Graph builder exists, new network metrics
  should prefer this structure rather than rebuilding ad-hoc
  multi-station relationships directly from raw observations

### Phase 3

- decide whether the Observation Graph becomes a central runtime object
  or remains an internal analytical abstraction

---

## Future Governance Trigger

The Observation Graph does not need to become a central runtime object
immediately.

However, the project must treat the following pattern as a trigger for
canonicalization:

- multiple intelligence modules independently rebuild
  `station_to_aircraft`
- multiple intelligence modules independently rebuild
  `aircraft_to_station`
- the same observation-network relations appear in competing forms such
  as dicts, DataFrames, or ad-hoc visibility tables

When this happens, a shared Observation Graph model and builder should
be introduced as the canonical internal structure rather than allowing
continued ad-hoc reconstruction.

Likely trigger scenarios include:

- temporal analysis
- mobility analytics
- multi-band analysis
- weather-aware observation context

Likely implementation target:

- `src/ogn_tool/models/observation_graph.py`

This is a future governance rule, not an immediate refactor mandate.

---

## Dependency Rules

The Observation Graph model and builder must:

- live in the analytical/domain side of the system
- depend on typed observations
- remain independent from UI, services, and storage concerns

It must not be built from:

- `ctx[...]`
- dashboard state
- UI view models
- Streamlit components

---

## Non-Goals

This contract does not imply:

- a new heavy RF propagation model
- terrain modelling
- replacement of the current RF pipeline
- immediate introduction of a new network pipeline
- UI-driven graph construction

---

## Strategic Value

The Observation Graph is the missing canonical layer between:

- station-centric RF analysis
- network-centric RF intelligence

It allows the project to evolve from station diagnostics toward true
multi-station RF network analysis while preserving the current typed
kernel.
