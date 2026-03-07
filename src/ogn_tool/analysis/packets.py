from __future__ import annotations

import pandas as pd


def deduplicate_packets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove APRS duplicates caused by multiple IGates hearing the same packet.
    """
    if df is None or df.empty:
        return df

    df = df.sort_values("ts_epoch")
    df = df.drop_duplicates(subset=["src", "ts_epoch", "lat", "lon"], keep="first")
    return df
