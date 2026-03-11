STATUS: derived
REFERENCE: docs/ROADMAP_MASTER.md

This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Data Validation Implementation

## How validation works

The validation layer operates on RF observation dataframes and applies
rule-based checks to identify invalid rows. Each validation rule returns a
boolean mask, and the masks are combined into a final validity mask.

## Error reporting

The validator returns:

- a filtered dataframe containing only valid observations
- a report dictionary with counts for each rule

Report fields include:

- rows_total
- rows_valid
- invalid_coordinates
- invalid_distance
- invalid_snr
- invalid_timestamp
- duplicates

## Filtering invalid observations

Rows that fail any validation rule are excluded from the returned dataframe.
Duplicates are detected and removed by default to avoid skewed metrics.

The validation module is implemented in:

src/ogn_tool/analysis/data_validation.py
