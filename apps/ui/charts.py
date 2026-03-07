from typing import Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

import folium
from folium.features import DivIcon
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None

MAX_MAP_POINTS = 50000
MAX_GRID_CELLS = 20000
LEGEND = {
    "packets": "packet density",
    "aircraft": "unique aircraft",
    "max_distance": "maximum reception distance",
    "shadow": "terrain shadow proxy",
}
SHADOW_COLORS = {
    True: "#222222",   # shadow
    False: "#00aa55",  # received
}


@st.cache_data(show_spinner=False)
def prepare_map_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    return dataset


def _color_from_value(val: float, vmin: float, vmax: float) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "#999999"
    if vmax <= vmin:
        t = 0.5
    else:
        t = (val - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
    if t < 0.25:
        return "#2563eb"
    if t < 0.5:
        return "#06b6d4"
    if t < 0.75:
        return "#22c55e"
    if t < 0.9:
        return "#eab308"
    return "#ef4444"


def render_map(title: str, dataset, ctx: dict) -> None:
    with st.container():
        st.subheader(title)
        with st.spinner("Loading map..."):
            bm = ctx["BASEMAPS"][ctx["basemap_label"]]
            m = folium.Map(
                location=[ctx["station_lat"], ctx["station_lon"]],
                zoom_start=8,
                tiles=None,
                control_scale=True,
                prefer_canvas=True,
            )
            folium.TileLayer(tiles=bm.tiles, attr=bm.attr, name=bm.name, control=False).add_to(m)
            folium.CircleMarker(
                location=[ctx["station_lat"], ctx["station_lon"]],
                radius=7,
                weight=2,
                color="#000000",
                fill=True,
                fill_opacity=1.0,
                popup=f"{ctx['station_callsign']} (ref)",
            ).add_to(m)
            max_range_km = ctx.get("max_distance_grid")
            max_range_label = ctx["fmt_float"](max_range_km, 1)
            folium.Marker(
                location=[ctx["station_lat"], ctx["station_lon"]],
                icon=DivIcon(
                    icon_size=(200, 36),
                    icon_anchor=(0, -10),
                    html=(
                        '<div style="font-size:12px;color:#111;background:rgba(255,255,255,0.8);'
                        'padding:2px 6px;border-radius:4px;border:1px solid #ddd;">'
                        f"Max range: {max_range_label} km</div>"
                    ),
                ),
            ).add_to(m)
            if ctx["show_rings"] and ctx["rings_km"]:
                for rkm in sorted(set(ctx["rings_km"])):
                    folium.Circle(
                        location=[ctx["station_lat"], ctx["station_lon"]],
                        radius=float(rkm) * 1000.0,
                        color="#3b82f6",
                        weight=1,
                        fill=False,
                        opacity=0.6,
                    ).add_to(m)
            folium_key = f"folium_{title.replace(' ', '_').lower()}"
            if not ctx["use_cov_grid"]:
                st.warning("Coverage grid is required for maps. Enable it in filters.")
                st_folium(m, height=750, use_container_width=True, key=folium_key)
                return
            if dataset is None or len(dataset) == 0:
                st.info("No packets found for this station in the selected time window.")
                return
            if "lat" not in dataset.columns or "lon" not in dataset.columns:
                st.warning("Coverage grid missing or invalid (lat/lon columns not found).")
                st_folium(m, height=750, use_container_width=True, key=folium_key)
                return
            df_points = prepare_map_dataset(dataset)
            map_bounds: Optional[Tuple[float, float, float, float]] = ctx.get("map_bounds")
            if map_bounds is not None:
                min_lat, min_lon, max_lat, max_lon = map_bounds
                df_points = df_points[
                    (df_points["lat"] >= min_lat)
                    & (df_points["lat"] <= max_lat)
                    & (df_points["lon"] >= min_lon)
                    & (df_points["lon"] <= max_lon)
                ]
            df_points = df_points[df_points["lat"].notna() & df_points["lon"].notna()]
            if df_points.empty:
                st.warning("No packets in the selected time window.")
                st_folium(m, height=750, use_container_width=True, key=folium_key)
                return
            if "heatmap" in title.lower() or "coverage map" in title.lower():
                if len(df_points) > MAX_GRID_CELLS:
                    df_points = df_points.sample(n=MAX_GRID_CELLS, random_state=42)
            original_len = len(df_points)
            if original_len > MAX_MAP_POINTS:
                df_points = df_points.sample(n=MAX_MAP_POINTS, random_state=42)
                st.warning(
                    f"Map limited to {MAX_MAP_POINTS:,} points "
                    f"(dataset contains {original_len:,})."
                )
            if not df_points.empty:
                coords = df_points[["lat", "lon"]].values.tolist()
                FastMarkerCluster(coords).add_to(m)
            st_folium(m, height=750, use_container_width=True, key=folium_key)


def render_grid_map(grid: pd.DataFrame, value: str, title: str, ctx: dict) -> None:
    if grid is None or len(grid) == 0:
        st.info("No packets found for this station in the selected time window.")
        return
    if value not in grid.columns:
        st.info(f"Missing column: {value}")
        return

    data = grid.copy()
    if len(data) > MAX_MAP_POINTS:
        data = data.sample(n=MAX_MAP_POINTS, random_state=42)

    bm = ctx["BASEMAPS"][ctx["basemap_label"]]
    m = folium.Map(
        location=[ctx["station_lat"], ctx["station_lon"]],
        zoom_start=8,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer(tiles=bm.tiles, attr=bm.attr, name=bm.name, control=False).add_to(m)
    folium.CircleMarker(
        location=[ctx["station_lat"], ctx["station_lon"]],
        radius=7,
        weight=2,
        color="#000000",
        fill=True,
        fill_opacity=1.0,
        popup=f"{ctx['station_callsign']} (ref)",
    ).add_to(m)

    vals = pd.to_numeric(data[value], errors="coerce")
    vmin = float(np.nanpercentile(vals.to_numpy(), 10)) if vals.notna().any() else 0.0
    vmax = float(np.nanpercentile(vals.to_numpy(), 90)) if vals.notna().any() else 1.0

    for _, row in data.iterrows():
        lat = row.get("grid_lat", row.get("lat"))
        lon = row.get("grid_lon", row.get("lon"))
        if pd.isna(lat) or pd.isna(lon):
            continue
        val = row.get(value)
        if value == "shadow":
            color = SHADOW_COLORS.get(bool(val), "#999999")
        else:
            val = float(val) if val == val else None
            color = _color_from_value(val, vmin, vmax) if val is not None else "#999999"
        tooltip = (
            f"Packets: {row.get('packets', '—')}\n"
            f"Aircraft: {row.get('aircraft', '—')}\n"
            f"Max distance: {ctx['fmt_float'](row.get('max_distance'), 1)} km\n"
            f"Shadow: {bool(row.get('shadow'))}"
        )
        folium.CircleMarker(
            location=[float(lat), float(lon)],
            radius=4.0,
            weight=1,
            color=color,
            fill=True,
            fill_opacity=0.75,
            tooltip=tooltip,
        ).add_to(m)

    st.caption(f"{title} — {LEGEND.get(value, value)}")
    st_folium(m, height=750, use_container_width=True, key=f"grid_{value}")


def plot_rssi_distance(data_plot, binned=None, x_max: Optional[float] = None):
    if go is None:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data_plot["distance_km"],
            y=data_plot["rssi_db"],
            mode="markers",
            name="Packets",
            marker=dict(size=2, opacity=0.18),
        )
    )
    if binned is not None and not binned.empty:
        fig.add_trace(
            go.Scatter(
                x=binned["distance_bin_km"],
                y=binned["rssi_median"],
                mode="lines",
                name="Median RSSI",
                line=dict(width=3, color="#f97316"),
            )
        )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.02),
        xaxis_title="Distance (km)",
        yaxis_title="RSSI (dB)",
        xaxis=dict(range=[0, x_max] if x_max else None),
    )
    return fig


def plot_altitude_distance(data_plot, med, x_max: Optional[float] = None):
    if go is None:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data_plot["distance_km"],
            y=data_plot["altitude_m"],
            mode="markers",
            name="Packets",
            marker=dict(size=2, opacity=0.15),
        )
    )
    if med is not None and not med.empty:
        fig.add_trace(
            go.Scatter(
                x=med["distance_bin_km"],
                y=med["altitude_median"],
                mode="lines",
                name="Median altitude",
                line=dict(width=3, color="#0ea5e9"),
            )
        )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.02),
        xaxis_title="Distance (km)",
        yaxis_title="Altitude (m)",
        # limit altitude axis for readability; extreme outliers remain in table/statistics
        xaxis=dict(range=[0, x_max] if x_max else None),
        yaxis=dict(range=[0, 5000]),
    )
    return fig


def plot_radio_horizon(data, med=None):
    if go is None:
        return None
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["horizon_km"],
            y=data["distance_km"],
            mode="markers",
            name="Packets",
            marker=dict(size=2, opacity=0.15),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, 400],
            y=[0, 400],
            mode="lines",
            name="Theoretical horizon",
            line=dict(width=2, color="#f97316"),
        )
    )
    if med is not None and not med.empty:
        fig.add_trace(
            go.Scatter(
                x=med["horizon_bin_km"],
                y=med["distance_median"],
                mode="lines",
                name="Median observed",
                line=dict(width=3, color="#0ea5e9"),
            )
        )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.02),
        xaxis_title="Horizon (km)",
        yaxis_title="Distance (km)",
        xaxis=dict(range=[0, 400]),
        yaxis=dict(range=[0, 400]),
    )
    return fig
