from __future__ import annotations

import pandas as pd


def detect_station_outages(timeseries: pd.DataFrame) -> pd.DataFrame:
    if timeseries is None or timeseries.empty or not {"time_bucket", "station_id", "observations"}.issubset(timeseries.columns):
        return pd.DataFrame(columns=["time_bucket", "station_id", "event"])
    outages = timeseries[timeseries["observations"] <= 0][["time_bucket", "station_id"]].copy()
    outages["event"] = "station_outage"
    return outages.reset_index(drop=True)


def detect_coverage_regressions(timeseries: pd.DataFrame) -> pd.DataFrame:
    if timeseries is None or timeseries.empty or not {"time_bucket", "coverage_points"}.issubset(timeseries.columns):
        return pd.DataFrame(columns=["time_bucket", "event", "delta"])
    out = timeseries.sort_values("time_bucket").copy()
    out["delta"] = out["coverage_points"].diff()
    reg = out[out["delta"] < 0][["time_bucket", "delta"]].copy()
    reg["event"] = "coverage_regression"
    return reg.reset_index(drop=True)


def detect_network_anomalies(timeseries: pd.DataFrame) -> pd.DataFrame:
    if timeseries is None or timeseries.empty or "observations" not in timeseries.columns:
        return pd.DataFrame(columns=["time_bucket", "event", "zscore"])
    out = timeseries.sort_values("time_bucket").copy()
    series = pd.to_numeric(out["observations"], errors="coerce")
    std = float(series.std()) if len(series) > 1 else 0.0
    if std <= 0.0:
        return pd.DataFrame(columns=["time_bucket", "event", "zscore"])
    mean = float(series.mean())
    out["zscore"] = (series - mean) / std
    an = out[out["zscore"].abs() >= 2.0][["time_bucket", "zscore"]].copy()
    an["event"] = "network_anomaly"
    return an.reset_index(drop=True)


__all__ = ["detect_station_outages", "detect_coverage_regressions", "detect_network_anomalies"]
