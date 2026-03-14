# Kernel Risk Note

This note summarizes the current architectural risk posture of the
analytical kernel.

It is a governance document, not a feature roadmap.

---

## Current Kernel Risk Posture

The kernel is not currently fragile from a scientific or algorithmic
point of view.

Its primary risk is structural complexity drift:

- overly broad runtime surfaces
- duplicated internal representations
- partial exposure of analytical capabilities
- contamination from transitional layers

---

## Primary Risks

### 1. Incomplete Typed Runtime Surface

`results.network_metrics` is the official typed runtime surface for
network intelligence outputs.

Risk:

- reporting remains incomplete
- parallel access paths appear outside the official contract
- consumers begin to build their own local "truth"
- legacy access patterns gradually return

Impact:

- very high

### 2. Repeated Observation-Network Reconstruction

Multiple modules may reconstruct the same observation-network relations,
for example:

- `station_to_aircraft`
- `aircraft_to_station`

Risk:

- logical divergence between modules
- avoidable memory and CPU overhead
- fragmented internal network model

Impact:

- high in the medium term

### 3. Flat Growth of `results.network_metrics`

A flat runtime surface is acceptable while the number of metric families
remains limited.

Risk:

- reduced discoverability
- reporting fragility
- typing and documentation overhead
- unstable consumer expectations

Impact:

- high in the medium term

### 4. Transitional Layer Contamination

Transitional modules such as `engine/` and the legacy dashboard must not
become hosts for new analytical logic.

Risk:

- duplicated orchestration logic
- erosion of layer boundaries
- increased coupling between UI/runtime and kernel

Impact:

- high if discipline weakens

---

## Risk Triggers

The following conditions indicate that the kernel is entering a higher
risk state:

- new analytical outputs exist in code but are not exposed through
  `results.network_metrics`
- multiple consumers read different internal surfaces for the same
  capability
- multiple modules rebuild the same observation-network relations
- new metric families continue to accumulate in a flat runtime namespace
- new analytical logic is added to transitional modules

---

## Mitigation Rules

### Runtime Rule

`results.*` remains the official runtime API.

Analytical consumers must prefer typed `results` surfaces over legacy or
ad-hoc access paths.

### Delivery Rule

No analytical capability is considered delivered until it is either:

- exposed through `results.network_metrics`, or
- explicitly classified as internal or transitional

### Layer Rule

The following boundaries must remain strict:

- `analysis` computes measurable facts
- `intelligence` derives judgments, priorities, and scenarios
- `reporting` assembles operator-facing outputs
- `UI` displays and filters only

### Observation Graph Rule

A canonical Observation Graph should be introduced only when repeated
ad-hoc reconstruction becomes a real maintenance problem.

It should not be introduced prematurely.

### Namespace Rule

If `results.network_metrics` continues to grow, it must evolve toward
stable grouped namespaces rather than unbounded flat expansion.

---

## Operational Priority

The immediate priority is not adding more analytical modules.

The immediate priority is:

1. complete the typed `results.network_metrics` surface
2. connect reporting to this surface consistently
3. keep transitional layers free of new analytical logic
4. defer structural refactors until their trigger conditions are real
