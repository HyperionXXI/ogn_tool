This document is subordinate to docs/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# RF Model API Audit

Scope: `src/ogn_tool/analysis/`

## Module API table

| module | main_function | inputs | outputs | notes |
|---|---|---|---|---|
| signal_distance | `analyze(df_observations, station_lat, station_lon, **_)` | observations DataFrame with `lat`, `lon`, `snr`/`snr_db` | dict: `implemented`, `summary`, `data`, `binned_data` | empirical RSSI/SNR vs distance; requires station coords |
| radio_horizon | `analyze(df_observations, station_lat, station_lon, station_alt_m=None, **_)` | observations DataFrame with `raw`, `lat`, `lon` | dict: `implemented`, `summary`, `data`, `binned_data` | computes theoretical horizon vs observed distance; parses altitude from raw |
| terrain | `analyze(df_grid, station_lat, station_lon, **_)` | grid DataFrame with `lat`, `lon`, `packet_count`, `max_distance_km`, `best_rssi_db` | dict: `implemented`, `summary`, `data` | uses grid cells, not observations |
| terrain_visibility | `analyze(df_observations, station_lat, station_lon, bin_deg=10, min_samples=30, altitude_offset_m=400, **_)` | observations DataFrame with `lat`, `lon`, `altitude_m`, optional `distance_km` | dict: `implemented`, `summary`, `data` | azimuth‑binned altitude visibility envelope |
| polar | `analyze(df_grid, station_lat, station_lon, **_)` | grid DataFrame with `lat`, `lon`, `packet_count`, `max_distance_km`, `best_rssi_db` | dict: `implemented`, `summary`, `data` | polar coverage analysis on grid |
| polar_coverage | `compute_polar_coverage(packets_rf, bins=36)` | DataFrame‑like with `bearing_deg`, `distance_km` | list[dict] | returns per‑sector stats; no `implemented` flag |
| altitude_distance | `analyze(df_observations, station_lat, station_lon, **_)` | observations DataFrame with `raw`, `lat`, `lon` | dict: `implemented`, `summary`, `data`, `binned_data` | parses altitude from raw; computes distance/alt bins |
| azimuth_footprint | `compute_azimuth_footprint(df_observations, station_lat, station_lon, bin_deg=10, min_samples=50)` | observations DataFrame with `lat`, `lon`, `distance_km` | dict: `implemented`, `summary`, `data` | computes sector footprint by distance |

## Inconsistencies observed

1. **Function naming**
   - Most modules use `analyze(...)`, but `polar_coverage` uses `compute_polar_coverage(...)` and `azimuth_footprint` uses `compute_azimuth_footprint(...)`.

2. **Input types**
   - Some modules expect **observation dataframes** (`df_observations`), others expect **grid dataframes** (`df_grid`).

3. **Return formats**
   - Most modules return a dict with `implemented`, `summary`, `data` (and sometimes `binned_data`).
   - `polar_coverage` returns a **list of dicts** with no `implemented` flag.

4. **Column expectations**
   - `signal_distance` uses `snr`/`snr_db`.
   - `radio_horizon` and `altitude_distance` parse altitude from `raw` rather than `altitude_m`.
   - `azimuth_footprint` requires `distance_km` already computed in input.

5. **Station coordinate handling**
   - Some modules allow missing station coords (and return `implemented: False`), but the error reasons are not consistent.

If you want, I can normalize naming and return shapes as a follow‑up (without changing logic).
