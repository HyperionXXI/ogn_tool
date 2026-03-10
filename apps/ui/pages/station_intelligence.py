from __future__ import annotations

import pandas as pd
import streamlit as st

from ogn_tool.engine.rf_engine import RFAnalysisEngine


try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None


def render_coverage_radar(azimuth_df: pd.DataFrame) -> None:
    st.subheader("Directional RF Coverage")

    if azimuth_df is None or not isinstance(azimuth_df, pd.DataFrame) or azimuth_df.empty:
        st.info("No azimuth data available")
        return

    angles = None
    values = None

    if "azimuth_center_deg" in azimuth_df.columns and "max_distance_km" in azimuth_df.columns:
        angles = azimuth_df["azimuth_center_deg"].tolist()
        values = azimuth_df["max_distance_km"].tolist()
    elif "azimuth_bin" in azimuth_df.columns and "packet_count" in azimuth_df.columns:
        angles = azimuth_df["azimuth_bin"].tolist()
        values = azimuth_df["packet_count"].tolist()

    if not angles or not values:
        st.info("No azimuth data available")
        return

    if go is None:
        st.line_chart(pd.DataFrame({"angle": angles, "value": values}).set_index("angle"))
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=angles,
            fill="toself",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        showlegend=False,
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_propagation_models(rf_models: dict) -> None:
    st.subheader("Propagation Models")

    if not rf_models:
        st.info("No RF models available")
        return

    for name, model in rf_models.items():
        st.markdown(f"### {name}")
        if isinstance(model, dict):
            summary = model.get("summary") or {}
            if summary:
                st.json(summary, expanded=False)
            data = model.get("data")
            if isinstance(data, pd.DataFrame) and not data.empty:
                st.line_chart(data)
            binned = model.get("binned_data")
            if isinstance(binned, pd.DataFrame) and not binned.empty:
                st.line_chart(binned)
        else:
            st.write(model)


def render_diagnostics(diagnostics: dict) -> None:
(diagnostics: dict) -> None:
    st.subheader("RF Diagnostics")

    if not diagnostics:
        st.info("No diagnostics available")
        return

    for name, value in vars(diagnostics).items():
        st.write(f"**{name}** : {value}")


def render_station_intelligence_page(ctx: dict) -> None:
    st.title("Station Intelligence")

    dataset = ctx.get("dataset", {})
    rf_packets = ctx.get("rf_packets")
    if rf_packets is None and isinstance(dataset, dict):
        rf_packets = dataset.get("rf_receptions")

    if rf_packets is None or not isinstance(rf_packets, pd.DataFrame) or rf_packets.empty:
        st.info("No RF packets available")
        return

    station_lat = ctx.get("station_lat")
    station_lon = ctx.get("station_lon")

    engine = RFAnalysisEngine(rf_packets, station_lat, station_lon)
    results = engine.run()

    metrics = results.metrics or {}
    rf_models = metrics.get("rf_models", {})
    diagnostics = ctx.get("rf_diagnostics", {})

    median_distance = None
    if isinstance(results.distance_df, pd.DataFrame) and "distance_km" in results.distance_df.columns:
        median_distance = results.distance_df["distance_km"].median()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Max distance", metrics.get("max_range_km", "-"))
    with col2:
        st.metric("Median distance", median_distance if median_distance is not None else "-")
    with col3:
        st.metric("Observations", metrics.get("rf_packets", "-"))

    st.divider()

    render_coverage_radar(results.azimuth_df)
    render_propagation_models(rf_models)
    render_diagnostics(diagnostics)
