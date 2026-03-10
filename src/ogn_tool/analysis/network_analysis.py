from __future__ import annotations

import pandas as pd


def station_aircraft_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return dataframe with columns:
    src (aircraft), igate (station), packets
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["src", "igate", "packets"])
    return (
        df.groupby(["src", "igate"])
        .size()
        .reset_index(name="packets")
    )


def station_overlap(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix is None or matrix.empty:
        return pd.DataFrame()
    pivot = matrix.pivot(index="src", columns="igate", values="packets").fillna(0)
    overlap = pivot.T.dot(pivot)
    return overlap


def station_metrics(df: pd.DataFrame, station: str) -> dict:
    if df is None or df.empty or station is None:
        return {"aircraft": 0, "packets": 0, "max_distance": None, "mean_distance": None}
    sub = df[df["igate"] == station]
    return {
        "aircraft": int(sub["src"].nunique()) if "src" in sub.columns else 0,
        "packets": int(len(sub)),
        "max_distance": float(sub["distance_km"].max()) if "distance_km" in sub.columns and not sub.empty else None,
        "mean_distance": float(sub["distance_km"].mean()) if "distance_km" in sub.columns and not sub.empty else None,
    }


def aircraft_redundancy(matrix: pd.DataFrame) -> pd.Series:
    if matrix is None or matrix.empty:
        return pd.Series(dtype=int)
    counts = matrix.groupby("src")["igate"].nunique()
    return counts.value_counts().sort_index()


def detect_network_blind_zones(coverage_redundancy_grid: pd.DataFrame) -> dict:
    """Detect network blind/critical zones based on redundancy grid.

    Args:
        coverage_redundancy_grid: DataFrame with columns ['lat_cell', 'lon_cell',
            'station_count', 'reception_count'].

    Returns:
        Dict containing blind and critical zones and a coverage summary.
    """

    if coverage_redundancy_grid is None or coverage_redundancy_grid.empty:
        return {
            "blind_zones": [],
            "critical_zones": [],
            "coverage_summary": {
                "blind_cells": 0,
                "single_station_cells": 0,
                "redundant_cells": 0,
            },
        }

    df = coverage_redundancy_grid.copy()
    if "station_count" not in df.columns or "reception_count" not in df.columns:
        return {
            "blind_zones": [],
            "critical_zones": [],
            "coverage_summary": {
                "blind_cells": 0,
                "single_station_cells": 0,
                "redundant_cells": 0,
            },
        }

    max_reception = float(df["reception_count"].max()) or 1.0

    def _severity(val: float) -> float:
        return float(val) / max_reception if max_reception > 0 else 0.0

    blind_df = df[df["station_count"] == 0]
    critical_df = df[df["station_count"] == 1]

    blind_zones = [
        {
            "lat_cell": float(row["lat_cell"]),
            "lon_cell": float(row["lon_cell"]),
            "reception_count": int(row["reception_count"]),
            "severity": _severity(row["reception_count"]),
        }
        for _, row in blind_df.iterrows()
    ]

    critical_zones = [
        {
            "lat_cell": float(row["lat_cell"]),
            "lon_cell": float(row["lon_cell"]),
            "reception_count": int(row["reception_count"]),
            "severity": _severity(row["reception_count"]),
        }
        for _, row in critical_df.iterrows()
    ]

    return {
        "blind_zones": blind_zones,
        "critical_zones": critical_zones,
        "coverage_summary": {
            "blind_cells": int(len(blind_df)),
            "single_station_cells": int(len(critical_df)),
            "redundant_cells": int((df["station_count"] > 1).sum()),
        },
    }


def suggest_station_locations(
    blind_zones: list[dict],
    coverage_grid: pd.DataFrame,
    terrain_data: pd.DataFrame,
) -> dict:
    """Suggest station placement to cover blind zones.

    This is a heuristic helper for identifying potential station placements in
    areas with low reception.

    Args:
        blind_zones: List of blind zone dicts as returned by `detect_network_blind_zones`.
        coverage_grid: DataFrame with coverage cells (should include `lat`, `lon`, `packets`).
        terrain_data: DataFrame with terrain elevation info (should include `lat`, `lon`, `altitude_m`).

    Returns:
        Dict with recommended locations and associated coverage gain/priority.
    """

    if not blind_zones:
        return {"recommended_locations": []}

    # Cluster blind zones by rounding cells to 0.1° grid.
    clusters: dict[tuple[float, float], list[dict]] = {}
    for z in blind_zones:
        lat = float(z.get("lat_cell", 0.0))
        lon = float(z.get("lon_cell", 0.0))
        key = (round(lat, 1), round(lon, 1))
        clusters.setdefault(key, []).append(z)

    recommendations = []
    for (lat_k, lon_k), zones in clusters.items():
        # centroid of blind zone cells in the cluster
        lats = [float(z["lat_cell"]) for z in zones]
        lons = [float(z["lon_cell"]) for z in zones]
        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)

        # estimate coverage gain from nearby coverage grid cells
        gain_cells = coverage_grid.copy() if coverage_grid is not None else pd.DataFrame()
        if not gain_cells.empty and "lat" in gain_cells.columns and "lon" in gain_cells.columns:
            # use small radius (~0.05°) to capture nearby value
            dist = ((gain_cells["lat"] - centroid_lat) ** 2 + (gain_cells["lon"] - centroid_lon) ** 2) ** 0.5
            gain_cells = gain_cells[dist <= 0.05]
            coverage_gain = float(gain_cells["packets"].sum()) if "packets" in gain_cells.columns else 0.0
        else:
            coverage_gain = 0.0

        # use terrain altitude to de-prioritize high-altitude locations
        altitude = None
        if terrain_data is not None and not terrain_data.empty and "lat" in terrain_data.columns and "lon" in terrain_data.columns:
            terr = terrain_data.copy()
            dist = ((terr["lat"] - centroid_lat) ** 2 + (terr["lon"] - centroid_lon) ** 2) ** 0.5
            terr = terr[dist <= 0.05]
            if not terr.empty and "altitude_m" in terr.columns:
                altitude = float(terr["altitude_m"].mean())

        # priority: higher coverage gain and lower altitude gets higher priority
        priority = coverage_gain
        if altitude is not None:
            priority = coverage_gain / (1 + altitude / 1000.0)

        recommendations.append(
            {
                "lat": centroid_lat,
                "lon": centroid_lon,
                "coverage_gain": coverage_gain,
                "priority": priority,
            }
        )

    # Sort by priority descending
    recommendations.sort(key=lambda x: x.get("priority", 0.0), reverse=True)

    return {"recommended_locations": recommendations}
