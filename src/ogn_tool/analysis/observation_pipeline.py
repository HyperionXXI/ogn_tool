"""
Observation pipeline for RF analysis.

Converts raw packet dataframe into observation objects used by RFAnalysisEngine.
"""

import pandas as pd


def build_observations_from_packets(df):
    """
    Convert raw packet dataframe into RF observation dataframe.

    Expected minimal fields:
        lat
        lon
        ts_epoch
        src
    """

    if df is None or len(df) == 0:
        return pd.DataFrame()

    required = {"lat", "lon"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    obs = df.copy()

    # ensure numeric coordinates
    obs["lat"] = pd.to_numeric(obs["lat"], errors="coerce")
    obs["lon"] = pd.to_numeric(obs["lon"], errors="coerce")

    obs = obs.dropna(subset=["lat", "lon"])

    return obs
