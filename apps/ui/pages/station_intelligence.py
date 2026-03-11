from __future__ import annotations

import pandas as pd
import streamlit as st
import pydeck as pdk

from ogn_tool.engine.rf_engine import RFAnalysisEngine
from ogn_tool.services.rf_analysis_pipeline import run_rf_analysis


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

    st.subheader("RF Diagnostics")

    if diagnostics is None:
        st.info("No diagnostics available")
        return

    if isinstance(diagnostics, dict):
        for name, value in diagnostics.items():
            st.write(f"{name}: {value}")
    else:
        st.write(diagnostics)



@st.cache_data
def cached_rf_analysis(df):
    from ogn_tool.services.rf_analysis_pipeline import run_rf_analysis
    return run_rf_analysis(df)

def render_station_intelligence_page(ctx: dict) -> None:
    st.title("Station Intelligence")

    dataset = ctx.get("dataset", {})
    rf_packets = ctx.get("rf_packets")
    if rf_packets is None and isinstance(dataset, dict):
        rf_packets = dataset.get("rf_receptions")

    if rf_packets is None or not isinstance(rf_packets, pd.DataFrame) or rf_packets.empty:
        st.info("No RF packets available")
        return

    rf_results = cached_rf_analysis(rf_packets)

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
    st.subheader("RF Metrics Summary")

    visibility = rf_results.get("visibility")

    if visibility:
        col1, col2, col3 = st.columns(3)
        col1.metric("Radio Horizon (km)", f"{visibility['radio_horizon_km']:.1f}")
        col2.metric("Observed Max Range (km)", f"{visibility['observed_max_km']:.1f}")
        col3.metric("Coverage Efficiency", f"{visibility['coverage_efficiency']:.2f}")

    st.subheader("RF Debug")

    st.write("Packets:", len(rf_packets))

    if "station_candidates" in rf_results:
        st.write("Candidates:", len(rf_results["station_candidates"]))
    else:
        st.write("No station_candidates in pipeline output")

    st.subheader("RF Map")

    if rf_packets is None or rf_packets.empty:
        st.warning("No aircraft positions available for RF map")
    else:
        aircraft_layer = pdk.Layer(
            "ScatterplotLayer",
            data=rf_packets,
            get_position='[lon, lat]',
            get_radius=1000,
            get_fill_color=[0, 120, 255],
            pickable=True,
        )

        layers = [aircraft_layer]

        candidates = rf_results.get("station_candidates")

        if candidates is not None and len(candidates) > 0:

            candidate_layer = pdk.Layer(
                "ScatterplotLayer",
                data=candidates,
                get_position='[lon, lat]',
                get_radius=5000,
                get_fill_color=[255, 0, 0],
                pickable=True,
            )

            layers.append(candidate_layer)

        lat = float(st.session_state.get("station_lat", rf_packets["lat"].mean()))
        lon = float(st.session_state.get("station_lon", rf_packets["lon"].mean()))

        view = pdk.ViewState(
            latitude=lat,
            longitude=lon,
            zoom=8,
            pitch=0,
        )

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view,
            map_style="mapbox://styles/mapbox/light-v9"
        )

        st.pydeck_chart(deck)
    st.subheader("RF Visibility Model")

    visibility = rf_results.get("visibility")

    if visibility:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Radio Horizon (km)",
            f"{visibility['radio_horizon_km']:.1f}"
        )

        col2.metric(
            "Observed Max Range (km)",
            f"{visibility['observed_max_km']:.1f}"
        )

        col3.metric(
            "Coverage Efficiency",
            f"{visibility['coverage_efficiency']:.2f}"
        )

    st.subheader("RF Blind Zones")

    blind = rf_results.get("blind_zones")

    if blind is not None and len(blind) > 0:
        st.dataframe(
            blind.sort_values("blind_score", ascending=False).head(20)
        )

    st.subheader("Station Placement Optimizer")

    candidates = rf_results.get("station_candidates")

    if candidates is not None and len(candidates) > 0:

        st.dataframe(
            candidates.sort_values("traffic_score", ascending=False).head(10)
        )
    render_diagnostics(diagnostics)
