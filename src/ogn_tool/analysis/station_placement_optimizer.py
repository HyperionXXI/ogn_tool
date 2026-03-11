import pandas as pd


def find_candidate_station_locations(df, grid_km=5):
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=["lat", "lon", "traffic_score"])

    grid_size_deg = grid_km / 111.0
    df_local = df.copy()
    df_local["grid_lat"] = (df_local["lat"] / grid_size_deg).round() * grid_size_deg
    df_local["grid_lon"] = (df_local["lon"] / grid_size_deg).round() * grid_size_deg

    grouped = (
        df_local.groupby(["grid_lat", "grid_lon"]).size().reset_index(name="traffic_score")
    )

    top = grouped.sort_values("traffic_score", ascending=False).head(20)
    return top.rename(columns={"grid_lat": "lat", "grid_lon": "lon"})
