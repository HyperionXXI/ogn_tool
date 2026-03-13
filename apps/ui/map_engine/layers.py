from __future__ import annotations

import pandas as pd
import pydeck as pdk


def _empty_layer():
    return pdk.Layer("ScatterplotLayer", data=[])


def _source_get(source: object, key: str, default=None):
    if isinstance(source, dict):
        return source.get(key, default)

    alias_map = {
        "coverage_grid": "coverage",
        "blind_cells": "blind_zones",
    }

    if hasattr(source, key):
        value = getattr(source, key)
        return default if value is None else value

    alias = alias_map.get(key)
    if alias and hasattr(source, alias):
        value = getattr(source, alias)
        return default if value is None else value

    metrics = getattr(source, "metrics", None)
    if isinstance(metrics, dict) and key in metrics:
        value = metrics.get(key, default)
        return default if value is None else value

    return default


def compute_station_degree(links_df: pd.DataFrame) -> pd.DataFrame:
    if links_df is None or links_df.empty:
        return pd.DataFrame(columns=["station_id", "network_degree"])
    a_counts = links_df["station_a"].value_counts()
    b_counts = links_df["station_b"].value_counts()
    degree = a_counts.add(b_counts, fill_value=0).astype(int)
    return degree.rename_axis("station_id").reset_index(name="network_degree")


def build_station_layer(dataset: dict):
    stations_df = _source_get(dataset, "stations_df")
    if stations_df is None or stations_df.empty:
        return _empty_layer()
    if "network_degree" not in stations_df.columns:
        stations_df = stations_df.copy()
        stations_df["network_degree"] = 0
    return pdk.Layer(
        "ScatterplotLayer",
        data=stations_df,
        get_position="[lon, lat]",
        get_radius=30,
        radius_min_pixels=3,
        radius_max_pixels=6,
        get_fill_color=[239, 68, 68],
        pickable=True,
    )


def build_aircraft_layer(dataset: dict):
    packets_df = _source_get(dataset, "packets_all")
    if packets_df is None or packets_df.empty:
        return _empty_layer()
    packets_df = packets_df.iloc[::5].copy()
    return pdk.Layer(
        "ScatterplotLayer",
        data=packets_df,
        get_position="[lon, lat]",
        get_radius=30,
        radius_min_pixels=2,
        radius_max_pixels=4,
        get_fill_color=[0, 150, 255],
        opacity=0.5,
        pickable=False,
    )


def build_coverage_layer(dataset: dict):
    packets_df = _source_get(dataset, "packets_rf")
    if packets_df is None or packets_df.empty:
        return _empty_layer()
    return pdk.Layer(
        "HexagonLayer",
        data=packets_df,
        get_position="[lon, lat]",
        radius=2000,
        elevation_scale=50,
        extruded=True,
        pickable=False,
    )


def build_redundancy_layer(dataset: dict):
    redundancy_df = _source_get(dataset, "coverage_redundancy_grid")
    if redundancy_df is None or redundancy_df.empty:
        return _empty_layer()

    def _color(row):
        count = row.get("station_count", 0)
        if count <= 0:
            return [17, 24, 39]
        if count == 1:
            return [249, 115, 22]
        if count == 2:
            return [250, 204, 21]
        return [34, 197, 94]

    return pdk.Layer(
        "ScatterplotLayer",
        data=redundancy_df,
        get_position="[lon_cell, lat_cell]",
        get_radius=3000,
        get_fill_color=_color,
        opacity=0.6,
        pickable=True,
    )


def build_blind_zone_layer(dataset: dict):
    blind_df = _source_get(dataset, "blind_cells")
    if blind_df is None or blind_df.empty:
        return _empty_layer()
    return pdk.Layer(
        "ScatterplotLayer",
        data=blind_df,
        get_position="[lon_cell, lat_cell]",
        get_radius=3000,
        get_fill_color=[239, 68, 68],
        opacity=0.6,
        pickable=True,
    )


def build_rf_link_dataframe(dataset: dict):
    radio_events = _source_get(dataset, "radio_events")
    station_reception = _source_get(dataset, "station_reception")
    stations_df = _source_get(dataset, "stations_df")
    if (
        radio_events is None
        or station_reception is None
        or radio_events.empty
        or station_reception.empty
        or stations_df is None
        or stations_df.empty
    ):
        return None

    if "event_key" not in radio_events.columns or "event_key" not in station_reception.columns:
        return None

    links = station_reception.merge(
        radio_events[["event_key", "lat", "lon", "aircraft"]]
        if "aircraft" in radio_events.columns
        else radio_events[["event_key", "lat", "lon"]].assign(aircraft=""),
        on="event_key",
        how="left",
    )

    if "station_id" not in links.columns:
        return None

    stations_df = stations_df.rename(columns={"callsign": "station_id"})
    links = links.merge(
        stations_df[["station_id", "lat", "lon"]].rename(
            columns={"lat": "station_lat", "lon": "station_lon"}
        ),
        on="station_id",
        how="left",
    )

    links = links.rename(
        columns={"lat": "aircraft_lat", "lon": "aircraft_lon", "aircraft": "aircraft_id"}
    )

    rssi_col = None
    if "rssi_db" in links.columns:
        rssi_col = "rssi_db"
    elif "rssi" in links.columns:
        rssi_col = "rssi"

    if rssi_col is None:
        links["rssi"] = None
    else:
        links["rssi"] = links[rssi_col]

    if "distance_km" not in links.columns:
        links["distance_km"] = None

    def _rssi_color(row):
        val = row.get("rssi")
        try:
            rssi = float(val)
        except Exception:
            rssi = None
        if rssi is None:
            return [239, 68, 68]
        if rssi > -70:
            return [34, 197, 94]
        if rssi > -90:
            return [250, 204, 21]
        return [239, 68, 68]

    links["rssi_color"] = links.apply(_rssi_color, axis=1)
    return links


def build_rf_link_layer(dataset: dict, links_df=None):
    if links_df is None:
        links_df = build_rf_link_dataframe(dataset)
    if links_df is None or links_df.empty:
        return _empty_layer()
    return pdk.Layer(
        "ArcLayer",
        data=links_df,
        get_source_position="[aircraft_lon, aircraft_lat]",
        get_target_position="[station_lon, station_lat]",
        get_source_color="rssi_color",
        get_target_color="rssi_color",
        get_width=2,
        pickable=True,
    )


def build_station_network_dataframe(dataset: dict):
    overlap = _source_get(dataset, "station_overlap_matrix")
    stations_df = _source_get(dataset, "stations_df")
    if overlap is None or stations_df is None or overlap.empty or stations_df.empty:
        return None

    stations_df = stations_df.rename(columns={"callsign": "station_id"})
    if "station_id" not in stations_df.columns:
        return None

    coords = stations_df.set_index("station_id")[["lat", "lon"]]

    diag = {}
    for station in overlap.index:
        try:
            diag[station] = float(overlap.loc[station, station])
        except Exception:
            diag[station] = 0.0

    rows = []
    for i, station_a in enumerate(overlap.index):
        for station_b in overlap.columns[i + 1 :]:
            shared = overlap.loc[station_a, station_b]
            try:
                shared_val = float(shared)
            except Exception:
                shared_val = 0.0
            if shared_val <= 0:
                continue
            if station_a not in coords.index or station_b not in coords.index:
                continue
            denom = min(diag.get(station_a, 0.0), diag.get(station_b, 0.0))
            overlap_ratio = (shared_val / denom) if denom else 0.0
            rows.append(
                {
                    "station_a": station_a,
                    "station_b": station_b,
                    "shared_aircraft": int(shared_val),
                    "overlap_ratio": overlap_ratio,
                    "station_a_lat": coords.loc[station_a, "lat"],
                    "station_a_lon": coords.loc[station_a, "lon"],
                    "station_b_lat": coords.loc[station_b, "lat"],
                    "station_b_lon": coords.loc[station_b, "lon"],
                }
            )

    if not rows:
        return None

    links_df = pd.DataFrame(rows)
    return links_df


def build_station_network_layer(dataset: dict, links_df=None):
    if links_df is None:
        links_df = build_station_network_dataframe(dataset)
    if links_df is None or links_df.empty:
        return _empty_layer()

    return pdk.Layer(
        "ArcLayer",
        data=links_df,
        get_source_position="[station_a_lon, station_a_lat]",
        get_target_position="[station_b_lon, station_b_lat]",
        get_source_color=[
            "overlap_ratio > 0.7 ? 0 : 255",
            "overlap_ratio > 0.7 ? 200 : (overlap_ratio > 0.4 ? 200 : 0)",
            "overlap_ratio > 0.7 ? 0 : (overlap_ratio > 0.4 ? 0 : 200)",
            "50 + overlap_ratio * 150",
        ],
        get_target_color=[
            "overlap_ratio > 0.7 ? 0 : 255",
            "overlap_ratio > 0.7 ? 200 : (overlap_ratio > 0.4 ? 200 : 0)",
            "overlap_ratio > 0.7 ? 0 : (overlap_ratio > 0.4 ? 0 : 200)",
            "50 + overlap_ratio * 150",
        ],
        get_width="overlap_ratio * 20",
        width_scale=1,
        opacity=1,
        pickable=True,
    )


def cap_links_per_station(df, max_links_per_station: int):
    if df is None or df.empty:
        return df
    if max_links_per_station <= 0:
        return df.iloc[0:0].copy()
    df_sorted = df.sort_values("overlap_ratio", ascending=False)
    counts = {}
    filtered_rows = []
    for _, row in df_sorted.iterrows():
        a = row.get("station_a")
        b = row.get("station_b")
        if a is None or b is None:
            continue
        counts.setdefault(a, 0)
        counts.setdefault(b, 0)
        if counts[a] >= max_links_per_station:
            continue
        if counts[b] >= max_links_per_station:
            continue
        filtered_rows.append(row)
        counts[a] += 1
        counts[b] += 1
    return pd.DataFrame(filtered_rows)
