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

    visibility = None
    if results is not None:
        network_metrics_result = getattr(results, "network_metrics", None)
        if isinstance(network_metrics_result, dict):
            visibility = network_metrics_result.get("visibility")
    if not visibility:
        visibility = legacy_network.get("visibility")

    summary = visibility.get("summary") if isinstance(visibility, dict) else None
    if isinstance(summary, dict):
        st.subheader("Network Visibility Summary")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Aircraft", int(summary.get("aircraft_count", 0) or 0))
        v2.metric("Stations", int(summary.get("station_count", 0) or 0))
        v3.metric(
            "Mean stations / aircraft",
            f"{float(summary.get('mean_stations_per_aircraft', 0.0) or 0.0):.2f}",
        )
        v4.metric(
            "Single-station ratio",
            f"{float(summary.get('single_station_ratio', 0.0) or 0.0):.2%}",
        )

    dependency = visibility.get("dependency") if isinstance(visibility, dict) else None
    if dependency is not None and not dependency.empty:
        st.subheader("Aircraft dependency")
        single_station = dependency[dependency["single_station"]]
        st.write(f"{len(single_station)} aircraft seen by only one station")
        st.dataframe(
            single_station[["aircraft_id", "station_count", "critical_station_id"]],
            use_container_width=True,
        )

    overlap = visibility.get("overlap") if isinstance(visibility, dict) else None
    if overlap is not None and not overlap.empty:
        st.subheader("Station overlap")
        st.dataframe(overlap.head(20), use_container_width=True)

    matrix = visibility.get("matrix") if isinstance(visibility, dict) else None
    if matrix is not None and not matrix.empty:
        with st.expander("Visibility matrix preview"):
            st.dataframe(matrix.head(50), use_container_width=True)

    station_influence = None
    if results is not None:
        network_metrics_result = getattr(results, "network_metrics", None)
        if isinstance(network_metrics_result, dict):
            station_influence = network_metrics_result.get("station_influence")
    if station_influence is None:
        station_influence = legacy_network.get("station_influence")

    station_anomalies = None
    network_robustness = None
    placement = None
    station_health = None
    network_summary = None
    station_dependency = None
    if results is not None:
        network_metrics_result = getattr(results, "network_metrics", None)
        if isinstance(network_metrics_result, dict):
            station_anomalies = network_metrics_result.get("station_anomalies")
            network_robustness = network_metrics_result.get("network_robustness")
            placement = network_metrics_result.get("station_placement")
            station_health = network_metrics_result.get("station_health")
            network_summary = network_metrics_result.get("network_summary")
            station_dependency = network_metrics_result.get("station_dependency")
    if station_anomalies is None:
        station_anomalies = legacy_network.get("station_anomalies")
    if network_robustness is None:
        network_robustness = legacy_network.get("network_robustness")
    if placement is None:
        placement = legacy_network.get("station_placement")
    if station_health is None:
        station_health = legacy_network.get("station_health")
    if network_summary is None:
        network_summary = legacy_network.get("network_summary")
    if station_dependency is None:
        station_dependency = legacy_network.get("station_dependency")

    if isinstance(network_summary, dict) and network_summary:
        status = str(network_summary.get("network_status") or "UNKNOWN")
        if status == "DEGRADED":
            st.error(f"Network status: {status}")
        elif status == "WARNING":
            st.warning(f"Network status: {status}")
        else:
            st.success(f"Network status: {status}")

        st.subheader("Network Summary")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Network status", status)
        s2.metric("Critical stations", int(network_summary.get("critical_station_count", 0) or 0))
        s3.metric("Warning stations", int(network_summary.get("warning_station_count", 0) or 0))
        s4.metric(
            "Mean stations / aircraft",
            f"{float(network_summary.get('mean_stations_per_aircraft', 0.0) or 0.0):.2f}",
        )
        if network_summary.get("top_critical_station"):
            st.caption(f"Top critical station: {network_summary['top_critical_station']}")
        if network_summary.get("notes"):
            st.caption(str(network_summary["notes"]))

    if station_health is not None and not station_health.empty:
        st.subheader("Station Diagnostics")
        show_critical = st.checkbox("Show only critical stations", value=False)
        health_df = station_health
        if show_critical and "health_status" in health_df.columns:
            health_df = health_df[health_df["health_status"] == "CRITICAL"]
        st.dataframe(
            health_df.sort_values("impact_score", ascending=False),
            use_container_width=True,
        )
        st.caption("Stations sorted by impact score")

    if station_dependency is not None and not station_dependency.empty:
        st.subheader("Station Dependencies")
        st.dataframe(
            station_dependency.sort_values("dependency_strength", ascending=False),
            use_container_width=True,
        )

    if station_influence is not None and not station_influence.empty:
        st.subheader("Station influence")
        influence_sorted = station_influence.sort_values("influence_score", ascending=False)
        st.dataframe(influence_sorted, use_container_width=True)

        top = influence_sorted.head(10)
        if not top.empty:
            st.bar_chart(top.set_index("station_id")["influence_score"])

        critical = influence_sorted[influence_sorted["single_station_aircraft_count"] > 0]
        if not critical.empty:
            st.subheader("Stations with unique coverage")
            st.dataframe(
                critical[
                    [
                        "station_id",
                        "single_station_aircraft_count",
                        "unique_aircraft_count",
                        "influence_score",
                    ]
                ].sort_values("single_station_aircraft_count", ascending=False),
                use_container_width=True,
            )

    if station_anomalies is not None and not station_anomalies.empty:
        st.subheader("Station anomalies")
        st.dataframe(station_anomalies, use_container_width=True)

    if network_robustness is not None and not network_robustness.empty:
        st.subheader("Network robustness")
        robustness_sorted = network_robustness.sort_values("impact_score", ascending=False)
        st.dataframe(robustness_sorted, use_container_width=True)
        top_robustness = robustness_sorted.head(10)
        if not top_robustness.empty:
            st.bar_chart(top_robustness.set_index("station_id")["impact_score"])

    st.subheader("Station placement candidates")
    if placement is not None and not placement.empty:
        st.dataframe(
            placement.sort_values("placement_score", ascending=False)[
                [
                    "lat",
                    "lon",
                    "placement_score",
                    "coverage_gain",
                    "redundancy_gain",
                    "critical_aircraft_supported",
                ]
            ].head(20),
            use_container_width=True,
        )
    else:
        st.info("No station placement candidates available.")

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
