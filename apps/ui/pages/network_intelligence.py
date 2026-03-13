import streamlit as st
import pydeck as pdk
import pandas as pd

from ogn_tool.analysis.network.network_intelligence import compute_coverage_redundancy
from ogn_tool.analysis.network_graph.rf_graph_builder import build_rf_graph
from ogn_tool.analysis.network_graph.graph_metrics import compute_network_evolution_metrics
from ogn_tool.analysis.network_graph.network_timeseries import (
    compute_coverage_timeseries,
    compute_network_load_timeseries,
)
from ogn_tool.analysis.network_graph.network_events import (
    detect_coverage_regressions,
    detect_network_anomalies,
)


def render_network_intelligence(ctx):
    st.title("Network Intelligence")

    results = ctx.get("results")
    legacy_network = ctx.get("network_analysis", {}) or {}

    df = ctx.get("rf_packets")
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        df = ctx.get("packets_window")

    st.write("Rows:", len(df) if isinstance(df, pd.DataFrame) else 0)

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No packets available")
        return

    if "lat" not in df.columns or "lon" not in df.columns:
        st.warning("Packet dataset has no coordinates")
        return

    df_plot = df.copy()
    df_plot["lat"] = pd.to_numeric(df_plot["lat"], errors="coerce")
    df_plot["lon"] = pd.to_numeric(df_plot["lon"], errors="coerce")
    df_plot = df_plot.dropna(subset=["lat", "lon"])

    if df_plot.empty:
        st.warning("No valid aircraft coordinates available for RF map")
        return

    if results is not None and getattr(results, "network_graph", None) is not None:
        graph = results.network_graph
        graph_metrics = getattr(results, "network_metrics", None) or getattr(graph, "metrics", None) or {}
        evolution = getattr(results, "network_evolution", None) or compute_network_evolution_metrics(graph, None)
        anomalies = getattr(results, "network_events", None)
        if isinstance(anomalies, dict):
            anomalies = anomalies.get("anomalies") or anomalies.get("network_anomalies") or pd.DataFrame()
        if anomalies is None:
            anomalies = pd.DataFrame()
        coverage_regressions = pd.DataFrame()
        if getattr(results, "network_events", None) and isinstance(results.network_events, dict):
            coverage_regressions = results.network_events.get("coverage_regressions") or pd.DataFrame()
        if coverage_regressions is None:
            coverage_regressions = pd.DataFrame()
    else:
        graph = legacy_network.get("graph") or build_rf_graph(df_plot)
        graph_metrics = legacy_network.get("metrics") or graph.get("metrics") or {}
        evolution = compute_network_evolution_metrics(graph, None)
        load_ts = compute_network_load_timeseries(df_plot)
        coverage_ts = compute_coverage_timeseries({"observations": df_plot})
        anomalies = detect_network_anomalies(load_ts)
        coverage_regressions = detect_coverage_regressions(coverage_ts)

    connectivity = graph_metrics.get("connectivity") or {}
    redundancy_metrics = graph_metrics.get("redundancy") or {}

    st.subheader("Network overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stations", int(connectivity.get("station_count", 0)))
    c2.metric("Aircraft", int(connectivity.get("aircraft_count", 0)))
    c3.metric("Connectivity", int(connectivity.get("edge_count", 0)))
    c4.metric("Redundancy", f"{float(redundancy_metrics.get('coverage_redundancy_mean', 0.0)):.2f}")

    st.subheader("Network evolution")
    e1, e2 = st.columns(2)
    e1.metric("Coverage growth", int(evolution.get("coverage_growth", 0)))
    e2.metric("Blind zone change", int(evolution.get("blind_zone_change", 0)))
    importance_change = evolution.get("station_importance_change") or {}
    if importance_change:
        st.dataframe(
            pd.DataFrame(
                [
                    {"station_id": station_id, "importance_change": value}
                    for station_id, value in importance_change.items()
                ]
            ),
            use_container_width=True,
        )

    st.subheader("Network events")
    if not anomalies.empty:
        st.caption("Network anomalies")
        st.dataframe(anomalies, use_container_width=True)
    else:
        st.info("No network anomalies detected")
    if not coverage_regressions.empty:
        st.caption("Coverage regressions")
        st.dataframe(coverage_regressions, use_container_width=True)
    else:
        st.info("No coverage regressions detected")

    st.subheader("Coverage redundancy map")
    redundancy = compute_coverage_redundancy(df_plot)

    if redundancy is None or len(redundancy) == 0:
        st.warning("No redundancy map available (single-station dataset)")

        layer = pdk.Layer(
            "ScatterplotLayer",
            df_plot,
            get_position='[lon, lat]',
            get_radius=1500,
            get_fill_color=[0, 120, 255],
            pickable=True,
        )

        view = pdk.ViewState(
            latitude=float(df_plot["lat"].mean()),
            longitude=float(df_plot["lon"].mean()),
            zoom=7,
        )

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view),
            use_container_width=True,
        )

    else:
        layer = pdk.Layer(
            "ScatterplotLayer",
            redundancy,
            get_position='[grid_lon, grid_lat]',
            get_radius=5000,
            get_fill_color='[200, 30 * stations, 0]',
            pickable=True,
        )

        view = pdk.ViewState(
            latitude=float(df_plot["lat"].mean()),
            longitude=float(df_plot["lon"].mean()),
            zoom=6,
        )

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view),
            use_container_width=True,
        )
