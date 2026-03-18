from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {"lat", "lon", "station_count", "gap_level"}

PRIORITY_MAP = {
    "CRITICAL": 100,
    "HIGH": 70,
    "MEDIUM": 40,
    "OK": 0,
}

ACTION_MAP = {
    "CRITICAL": "deploy new station",
    "HIGH": "increase redundancy",
    "MEDIUM": "monitor coverage",
    "OK": "no action",
}


def prioritize_coverage_gaps(
    gaps: pd.DataFrame,
    *,
    max_candidates: int = 20,
) -> pd.DataFrame:
    """Rank detected coverage gaps into operator-facing priorities."""
    missing = REQUIRED_COLUMNS - set(gaps.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = gaps.copy()
    if "notes" not in df.columns:
        df["notes"] = ""

    if df.empty:
        return pd.DataFrame(
            columns=[
                "lat",
                "lon",
                "station_count",
                "gap_level",
                "priority_score",
                "recommended_action",
                "notes",
            ]
        )

    df["priority_score"] = df["gap_level"].map(PRIORITY_MAP).fillna(0).astype(int)
    df["recommended_action"] = df["gap_level"].map(ACTION_MAP).fillna("review manually")
    df = df[df["priority_score"] > 0]

    if df.empty:
        return pd.DataFrame(
            columns=[
                "lat",
                "lon",
                "station_count",
                "gap_level",
                "priority_score",
                "recommended_action",
                "notes",
            ]
        )

    df = df.sort_values(
        ["priority_score", "station_count", "lat", "lon"],
        ascending=[False, True, True, True],
    )
    return df[[
        "lat",
        "lon",
        "station_count",
        "gap_level",
        "priority_score",
        "recommended_action",
        "notes",
    ]].head(max_candidates).reset_index(drop=True)
