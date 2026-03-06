# RF Scope Guardrails

## Central rule

Any functional evolution must be explicitly attached to one of the 10 features
listed in the RF Features Index.

## Allowed changes within a feature

Examples of allowed changes:

- adding or correcting an internal metric
- improving a score or computation
- better robustness or edge‑case handling
- improved visualization of an existing feature
- adding useful summary/data fields in analyze(...)
- improving normalization or thresholds

## Not allowed without roadmap update

Examples that are not allowed without an explicit roadmap update:

- a new analysis module outside the index
- a new diagnostic family
- a new standalone UI view not tied to an existing feature
- a new analytic architecture layer
- any implicit “feature 11”

## Mapping rule

Every functional commit must explicitly mention the feature it belongs to,
for example:

- Feature 01 Polar coverage
- Feature 04 Shadow zones
- Feature 06 Antenna diagnostics

## Practical decision rule

Before implementing anything, verify:

- Which feature does this belong to?
- Is the link to the spec explicit?
- Is this an internal improvement or a new feature?
