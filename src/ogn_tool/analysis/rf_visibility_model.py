from __future__ import annotations

import numpy as np
import pandas as pd


def compute_radio_horizon(station_height_m, aircraft_height_m):
    h1 = max(0.0, float(station_height_m))
    h2 = max(0.0, float(aircraft_height_m))
    return {"radio_horizon_km": float(3.57 * ((h1 ** 0.5) + (h2 ** 0.5)))}


def compute_expected_vs_observed_range(df, station_height_m=10, aircraft_height_m=1200):
    if df is None or len(df) == 0:
        return {
            "radio_horizon_km": float(compute_radio_horizon(station_height_m, aircraft_height_m)["radio_horizon_km"]),
            "observed_max_km": None,
            "observed_p95_km": None,
            "coverage_efficiency": None,
        }

    df_local = pd.DataFrame(df).copy()

    # Vector-first: consume observation vectors directly.
    if "distance_km" in df_local.columns:
        dist = pd.to_numeric(df_local.get("distance_km"), errors="coerce")
    elif "distance" in df_local.columns:
        dist = pd.to_numeric(df_local.get("distance"), errors="coerce")
    else:
        dist = pd.Series([np.nan] * len(df_local))

    if "radio_horizon_km" in df_local.columns:
        horizon_series = pd.to_numeric(df_local.get("radio_horizon_km"), errors="coerce")
        horizon = float(horizon_series.dropna().median()) if not horizon_series.dropna().empty else None
    else:
        horizon = None

    if horizon is None:
        horizon = compute_radio_horizon(station_height_m, aircraft_height_m)["radio_horizon_km"]

    dist = dist[np.isfinite(dist)]
    observed_max = float(dist.max()) if len(dist) else None
    observed_p95 = float(np.nanpercentile(dist, 95)) if len(dist) else None

    if observed_p95 is None or not np.isfinite(horizon) or horizon <= 0:
        efficiency = None
    else:
        efficiency = float(observed_p95 / float(horizon))

    return {
        "radio_horizon_km": float(horizon),
        "observed_max_km": observed_max,
        "observed_p95_km": observed_p95,
        "coverage_efficiency": efficiency,
    }
