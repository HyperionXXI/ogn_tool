# RF Validation — 2026-03-21 Multi-Station (Synchronized Window)

## Context
Dataset:
- scope: OGN-only
- stations: `FK50887`, `LSPD`, `LSZG`, `SOLOTHURN`
- gate: strict (`packet_count>=500`, `unique_aircraft>=10`, `temporal_coverage_ratio>=0.5`)
- synchronized window:
  - start: `2026-03-21T06:19:27Z`
  - end: `2026-03-21T12:19:27Z`

Run IDs retained (duplicates cleaned):
- `fk50887_2026_03_21_121927_6h_offset7h`
- `lspd_2026_03_21_121927_6h_offset7h`
- `lszg_2026_03_21_121927_6h_offset7h`
- `solothurn_2026_03_21_121927_6h_offset7h`

## Raw Table

| run_id | center | share | uniformity | largest_gap | stable? |
|---|---:|---:|---:|---:|---|
| fk50887_2026_03_21_121927_6h_offset7h | 295° | 0.83 | 0.97 | 240 | YES |
| lspd_2026_03_21_121927_6h_offset7h | 215° | 0.29 | 0.99 | 180 | NO |
| lszg_2026_03_21_121927_6h_offset7h | 85° | 0.24 | 0.99 | 120 | NO |
| solothurn_2026_03_21_121927_6h_offset7h | 245° | 0.47 | 0.99 | 180 | NO |

## Conclusion
Conclusion: variable (inter-station).

## Short Interpretation
The RF structure is not invariant across stations on the same synchronized window, which is expected for a spatially coherent model.
