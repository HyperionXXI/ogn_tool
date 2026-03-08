from __future__ import annotations

import streamlit as st

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field


@st.cache_data(show_spinner=False)
def compute_rf_engine(packets, station_lat, station_lon):
    engine = RFAnalysisEngine(packets, station_lat, station_lon)
    return engine.run()


def render_propagation_page(filters):
    ctx = filters
    st.markdown("<h2>Propagation</h2>", unsafe_allow_html=True)
    
    db_path = ctx['db_path']
    filters_apply = ctx['filters_apply']
    station_callsign = ctx['station_callsign']
    station_lat = ctx['station_lat']
    station_lon = ctx['station_lon']
    dst_types = ctx['dst_types']
    limit_rows = ctx['limit_rows']

    section_signal = st.container()
    section_altitude = st.container()
    section_distribution = st.container()

    df_grid = ctx['load_coverage_grid'](db_path, filters_apply["since_epoch"])
    packets_signal = ctx['_load_packets_window_raw'](
        db_path=db_path,
        since_iso=filters_apply["since_iso"],
        since_epoch=filters_apply["since_epoch"],
        dst_types=dst_types,
        station_callsign=station_callsign,
        only_heard_by=False,
        igate_filter="",
        source_mode="Heard-by station",
        qas_filter="",
        limit_rows=limit_rows,
    )
    engine_result = compute_rf_engine(packets_signal, station_lat, station_lon)
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")
    horizon_result = (engine_result.metrics.get("radio_horizon") or {"implemented": False})
    horizon_summary = horizon_result.get("summary") or {}
    horizon_p95 = horizon_summary.get("horizon_p95_km")
    observed_p95 = horizon_summary.get("observed_p95_distance_km")
    if engine_result.metrics.get("rf_packets", 0) < 200:
        st.info("Not enough RF packets for this analysis.")
        return

    with section_signal:
        st.subheader("Signal vs distance (SNR dB)")
        result = (engine_result.metrics.get("signal_distance") or {"implemented": False})
        if not result.get("implemented"):
            df = ctx.get("rf_packets")
            if df is None or df.empty:
                st.info("No RF packets available.")
            else:
                import pandas as pd

                bins = (
                    df.groupby(pd.cut(df["distance_km"], bins=40))
                    .size()
                    .reset_index(name="packets")
                )

                st.bar_chart(bins["packets"])
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Packet total", ctx['fmt_int'](summary.get("packet_total")))
                with c2:
                    val = summary.get("max_distance_km")
                    metric_card("Max distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("mean_rssi")
                    metric_card("Mean signal (SNR dB)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    metric_card("P95 distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
                data_plot = data
                if len(data_plot) > 20000:
                    data_plot = data_plot.sample(n=20000, random_state=42)
                x_max = None
                if "distance_km" in data_plot.columns and not data_plot["distance_km"].empty:
                    x_max = float(data_plot["distance_km"].quantile(0.99))
                if "distance_km" in data_plot.columns and "rssi_db" in data_plot.columns:
                    st.markdown("**RSSI vs distance**")
                    binned = result.get("binned_data")
                    distance_markers = [
                        {"value": summary.get("p95_distance_km"), "label": "P95 range", "color": "#0ea5e9"},
                        {"value": horizon_p95, "label": "Radio horizon P95", "color": "#f97316"},
                        {"value": observed_p95, "label": "Observed P95", "color": "#22c55e"},
                    ]
                    fig = ui_charts.plot_rssi_distance(
                        data_plot,
                        binned=binned,
                        x_max=x_max,
                        distance_markers=distance_markers,
                    )
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.scatter_chart(data_plot, x="distance_km", y="rssi_db")
                else:
                    st.info("RSSI vs distance data missing required columns.")
                st.dataframe(data.head(20), use_container_width=True, height=300)

    st.divider()
    with section_altitude:
        st.subheader("Altitude vs distance")
        result = (engine_result.metrics.get("altitude_distance") or {"implemented": False})
        if not result.get("implemented"):
            df = ctx.get("rf_packets")
            if df is None or df.empty:
                st.info("No RF packets available.")
            elif "altitude_m" not in df.columns:
                st.info("Altitude field not present in packets.")
            else:
                st.scatter_chart(
                    df.rename(
                        columns={
                            "distance_km": "x",
                            "altitude_m": "y",
                        }
                    )[["x", "y"]]
                )
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Packet total", ctx['fmt_int'](summary.get("packet_total")))
                with c2:
                    val = summary.get("max_distance_km")
                    metric_card("Max distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("mean_altitude_m")
                    metric_card("Mean altitude (m)", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    metric_card("P95 distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
                data_plot = data
                if len(data_plot) > 20000:
                    data_plot = data_plot.sample(n=20000, random_state=42)
                x_max = None
                if "distance_km" in data_plot.columns and not data_plot["distance_km"].empty:
                    x_max = float(data_plot["distance_km"].quantile(0.99))
                if "distance_km" in data_plot.columns and "altitude_m" in data_plot.columns:
                    # Feature 03 uses 20 km bins for altitude trend readability
                    bins = (data_plot["distance_km"] // 20) * 20
                    med = (
                        data_plot.assign(distance_bin_km=bins)
                        .groupby("distance_bin_km", as_index=False)
                        .agg(altitude_median=("altitude_m", "median"))
                        .sort_values("distance_bin_km")
                    )
                    distance_markers = [
                        {"value": summary.get("p95_distance_km"), "label": "P95 range", "color": "#0ea5e9"},
                        {"value": horizon_p95, "label": "Radio horizon P95", "color": "#f97316"},
                        {"value": observed_p95, "label": "Observed P95", "color": "#22c55e"},
                    ]
                    fig = ui_charts.plot_altitude_distance(
                        data_plot,
                        med=med,
                        x_max=x_max,
                        distance_markers=distance_markers,
                    )
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.scatter_chart(data_plot, x="distance_km", y="altitude_m")
                binned = result.get("binned_data")
                if binned is not None and not binned.empty:
                    order = ["0-500 m", "500-1000 m", "1000-2000 m", ">2000 m"]
                    if "altitude_bin" in binned.columns:
                        binned = binned.copy()
                        binned["altitude_bin"] = ctx['pd'].Categorical(binned["altitude_bin"], categories=order, ordered=True)
                        binned = binned.sort_values("altitude_bin")
                    st.dataframe(binned, use_container_width=True, height=300)

    st.divider()
    with section_distribution:
        st.subheader("Distance distribution")
        result = (engine_result.metrics.get("station_range") or {"implemented": False})
        if not result.get("implemented"):
            st.info("Distance distribution analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            if summary:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Packet total", ctx['fmt_int'](summary.get("packet_total")))
                with c2:
                    metric_card("Grid cells", ctx['fmt_int'](summary.get("grid_cells")))
                with c3:
                    val = summary.get("max_distance_km")
                    metric_card("Max distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    metric_card("P95 distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No distance statistics available.")
