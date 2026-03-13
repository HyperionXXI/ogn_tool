"""
RF feature module: terrain visibility envelope (heuristic, no DEM).
Derives minimum visible altitude by azimuth bins from RF packets.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd

from ogn_tool.analysis.rf_metrics.rf_statistics import compute_bearing



def analyze(
    df_observations: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
    bin_deg: int = 10,
    min_samples: int = 30,
    altitude_offset_m: float = 400.0,
    **_: Any,
) -> Dict[str, Any]:
    if df_observations is None or not isinstance(df_observations, pd.DataFrame) or df_observations.empty:
        return {"implemented": False, "summary": {"reason": "no_packets"}, "data": None}
    if station_lat is None or station_lon is None:
        return {"implemented": False, "summary": {"reason": "no_station_coords"}, "data": None}
    required = {"lat", "lon", "altitude_m"}
    if not required.issubset(set(df_observations.columns)):
        return {"implemented": False, "summary": {"reason": "missing_columns"}, "data": None}

    lat = pd.to_numeric(df_observations["lat"], errors="coerce").to_numpy()
    lon = pd.to_numeric(df_observations["lon"], errors="coerce").to_numpy()
    alt = pd.to_numeric(df_observations["altitude_m"], errors="coerce").to_numpy()
    dist = pd.to_numeric(df_observations.get("distance_km"), errors="coerce").to_numpy()

    mask = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(alt)
    if not mask.any():
        return {"implemented": False, "summary": {"reason": "no_valid_coords"}, "data": None}

    lat = lat[mask]
    lon = lon[mask]
    alt = alt[mask]
    dist = dist[mask] if dist.size == mask.size else np.full_like(alt, np.nan, dtype=float)

    az = compute_bearing(float(station_lat), float(station_lon), lat, lon)
    az_bin = (az // bin_deg) * bin_deg
    az_center = az_bin + (bin_deg / 2.0)

    df = pd.DataFrame(
        {
            "azimuth_bin": az_bin,
            "azimuth_center_deg": az_center,
            "altitude_m": alt,
            "distance_km": dist,
        }
    )

    agg = (
        df.groupby("azimuth_bin", as_index=False)
        .agg(
            azimuth_center_deg=("azimuth_center_deg", "mean"),
            sample_count=("altitude_m", "count"),
            p10_altitude_m=("altitude_m", lambda x: np.nanpercentile(x.to_numpy(), 10)),
            p50_altitude_m=("altitude_m", lambda x: np.nanpercentile(x.to_numpy(), 50)),
            max_distance_km=("distance_km", "max"),
        )
        .sort_values("azimuth_bin")
    )

    # Ensure full 360° coverage bins for consistent visuals
    full_bins = pd.DataFrame(
        {"azimuth_bin": np.arange(0, 360, bin_deg, dtype=float)}
    )
    full_bins["azimuth_center_deg"] = full_bins["azimuth_bin"] + (bin_deg / 2.0)
    agg = full_bins.merge(agg, on=["azimuth_bin", "azimuth_center_deg"], how="left")
    agg["sample_count"] = agg["sample_count"].fillna(0).astype(int)

    valid = agg["sample_count"] >= int(min_samples)
    if valid.sum() < 3:
        return {"implemented": False, "summary": {"reason": "insufficient_samples"}, "data": agg}

    valid_p10 = pd.to_numeric(agg.loc[valid, "p10_altitude_m"], errors="coerce")
    global_p10 = float(valid_p10.median()) if valid_p10.notna().any() else float("nan")
    threshold_alt = global_p10 + float(altitude_offset_m)
    agg["shadow_suspected"] = False
    agg.loc[valid & (agg["p10_altitude_m"] >= threshold_alt), "shadow_suspected"] = True
    agg["confidence"] = agg["sample_count"] / float(agg["sample_count"].max() or 1)

    worst_idx = valid_p10.idxmax() if valid_p10.notna().any() else None
    worst_sector_deg = float(agg.loc[worst_idx, "azimuth_center_deg"]) if worst_idx is not None else None

    summary = {
        "bin_deg": int(bin_deg),
        "min_samples": int(min_samples),
        "sector_count": int(valid.sum()),
        "shadow_sector_count": int(agg["shadow_suspected"].sum()),
        "mean_p10_altitude_m": float(valid_p10.mean()) if valid_p10.notna().any() else None,
        "worst_sector_deg": worst_sector_deg,
    }

    return {"implemented": True, "summary": summary, "data": agg}
