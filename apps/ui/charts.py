from typing import Optional

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None

try:
    import pydeck as pdk
except Exception:  # pragma: no cover
    pdk = None

MAX_MAP_POINTS = 10000


def _map_style(ctx: dict):
    if pdk is None:
        return None
    label = str(ctx.get("basemap_label") or "")
    if "Positron" in label or "clair" in label:
        return pdk.map_styles.CARTO_LIGHT
    if "Dark" in label or "dark" in label:
        return pdk.map_styles.CARTO_DARK
    return pdk.map_styles.ROAD




def render_rf_cartography(grid: pd.DataFrame, ctx: dict, layers: list[str]) -> None:
    if pdk is None:
        st.error("Missing dependency: pydeck. Install: pip install pydeck")
        return
    if grid is None or len(grid) == 0:
        st.info("No packets available.")
        return
    grid = grid.dropna(subset=["lat", "lon"])
    if grid.empty:
        st.info("No packets available.")
        return

    view = pdk.ViewState(
        latitude=ctx["station_lat"],
        longitude=ctx["station_lon"],
        zoom=8,
        pitch=35,
    )

    deck_layers = []

    # Build square polygons from fixed grid cells (scientific, comparable)
    cell_size_deg = float(grid["cell_size_deg"].iloc[0]) if "cell_size_deg" in grid.columns else 0.01
    poly_df = grid.copy()
    poly_df["polygon"] = poly_df.apply(
        lambda r: [
            [r["lon"], r["lat"]],
            [r["lon"] + cell_size_deg, r["lat"]],
            [r["lon"] + cell_size_deg, r["lat"] + cell_size_deg],
            [r["lon"], r["lat"] + cell_size_deg],
        ],
        axis=1,
    )
    # Precompute stable color bins
    prob_bins = pd.cut(
        pd.to_numeric(poly_df.get("probability"), errors="coerce").fillna(0.0),
        bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        include_lowest=True,
        right=True,
    )
    prob_colors = [
        [220, 38, 38, 110],
        [249, 115, 22, 120],
        [234, 179, 8, 130],
        [132, 204, 22, 140],
        [34, 197, 94, 150],
    ]
    poly_df["probability_color"] = [
        prob_colors[i] if i is not None else [153, 153, 153, 80]
        for i in prob_bins.cat.codes
    ]
    conf_bins = pd.cut(
        pd.to_numeric(poly_df.get("confidence"), errors="coerce").fillna(0.0),
        bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
        include_lowest=True,
        right=True,
    )
    conf_colors = [
        [148, 163, 184, 90],
        [125, 211, 252, 100],
        [59, 130, 246, 110],
        [37, 99, 235, 120],
        [30, 64, 175, 130],
    ]
    poly_df["confidence_color"] = [
        conf_colors[i] if i is not None else [153, 153, 153, 80]
        for i in conf_bins.cat.codes
    ]
    max_dist = pd.to_numeric(poly_df.get("max_distance"), errors="coerce").fillna(0.0)
    dist_bins = pd.cut(
        max_dist,
        bins=[0.0, 10.0, 20.0, 40.0, 80.0, 120.0, 160.0, 250.0, float("inf")],
        include_lowest=True,
        right=True,
    )
    dist_colors = [
        [226, 232, 240, 90],
        [191, 219, 254, 110],
        [147, 197, 253, 120],
        [96, 165, 250, 130],
        [59, 130, 246, 140],
        [37, 99, 235, 150],
        [30, 64, 175, 160],
        [17, 24, 39, 170],
    ]
    poly_df["max_distance_color"] = [
        dist_colors[i] if i is not None else [153, 153, 153, 80]
        for i in dist_bins.cat.codes
    ]

    if "RF probability" in layers:
        deck_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=poly_df,
                get_polygon="polygon",
                get_fill_color="probability_color",
                get_line_color=[255, 255, 255, 30],
                line_width_min_pixels=1,
                stroked=True,
                filled=True,
                opacity=0.7,
            )
        )
    if "Confidence" in layers and "confidence" in grid.columns:
        deck_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=poly_df,
                get_polygon="polygon",
                get_fill_color="confidence_color",
                get_line_color=[255, 255, 255, 30],
                line_width_min_pixels=1,
                stroked=True,
                filled=True,
                opacity=0.7,
            )
        )
    if "Max distance footprint" in layers and "max_distance" in grid.columns:
        deck_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=poly_df,
                get_polygon="polygon",
                get_fill_color="max_distance_color",
                get_line_color=[255, 255, 255, 30],
                line_width_min_pixels=1,
                stroked=True,
                filled=True,
                opacity=0.7,
            )
        )

    if "RF contours" in layers:
        # approximate contours via fixed probability bins and stable colors
        probs = pd.to_numeric(grid["probability"], errors="coerce").fillna(0.0)
        bin_edges = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bins = pd.cut(probs, bins=bin_edges, include_lowest=True, right=True)
        colors = [
            [220, 38, 38, 120],
            [249, 115, 22, 120],
            [234, 179, 8, 120],
            [132, 204, 22, 120],
            [34, 197, 94, 120],
        ]
        contour_df = poly_df.copy()
        contour_df["contour_color"] = [
            colors[i] if i is not None else [153, 153, 153, 80]
            for i in bins.cat.codes
        ]
        deck_layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=contour_df,
                get_polygon="polygon",
                get_fill_color="contour_color",
                get_line_color=[255, 255, 255, 20],
                line_width_min_pixels=1,
                stroked=True,
                filled=True,
                opacity=0.6,
            )
        )

    if "Coverage cloud" in layers:
        deck_layers.append(
            pdk.Layer(
                "HeatmapLayer",
                data=grid,
                get_position=["lon", "lat"],
                radius_pixels=60,
            )
        )

    # Station marker + range rings (km)
    station = {"lat": ctx.get("station_lat"), "lon": ctx.get("station_lon")}
    if station["lat"] is not None and station["lon"] is not None:
        deck_layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=[station],
                get_position=["lon", "lat"],
                get_radius=300,
                get_fill_color=[37, 99, 235, 200],
            )
        )
        for r_km in (10, 20, 40):
            deck_layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=[station],
                    get_position=["lon", "lat"],
                    get_radius=r_km * 1000,
                    get_fill_color=[0, 0, 0, 0],
                    get_line_color=[37, 99, 235, 120],
                    line_width_min_pixels=1,
                    stroked=True,
                    filled=False,
                )
            )

    deck = pdk.Deck(layers=deck_layers, initial_view_state=view, map_style=_map_style(ctx))
    st.pydeck_chart(deck, use_container_width=True)


def plot_rssi_distance(data_plot, binned=None, x_max: Optional[float] = None, distance_markers=None):
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
    if distance_markers:
        for marker in distance_markers:
            value = marker.get("value")
            if value is None:
                continue
            try:
                fig.add_vline(
                    x=value,
                    line=dict(color=marker.get("color", "#64748b"), width=2, dash="dash"),
                    annotation_text=marker.get("label", ""),
                    annotation_position="top left",
                )
            except Exception:
                pass
    return fig


def plot_altitude_distance(data_plot, med, x_max: Optional[float] = None, distance_markers=None):
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
    if (
        med is not None
        and not med.empty
        and "distance_bin_km" in med.columns
        and "altitude_median" in med.columns
    ):
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
    if distance_markers:
        for marker in distance_markers:
            value = marker.get("value")
            if value is None:
                continue
            try:
                fig.add_vline(
                    x=value,
                    line=dict(color=marker.get("color", "#64748b"), width=2, dash="dash"),
                    annotation_text=marker.get("label", ""),
                    annotation_position="top left",
                )
            except Exception:
                pass
    return fig


def plot_polar_p95(az_stats: pd.DataFrame):
    if go is None or az_stats is None or az_stats.empty:
        return None
    df = az_stats.copy()
    if "az_bin" in df.columns:
        df = df.sort_values("az_bin")
        theta = df["az_bin"].astype(float)
    else:
        return None
    r = pd.to_numeric(df.get("p95_distance_km"), errors="coerce").fillna(0.0)
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            mode="lines+markers",
            marker=dict(size=4, color="#0ea5e9"),
            line=dict(width=2, color="#0ea5e9"),
            name="P95 distance",
        )
    )
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
        polar=dict(
            angularaxis=dict(direction="clockwise", rotation=90),
            radialaxis=dict(title="Distance (km)", angle=90),
        ),
    )
    return fig


