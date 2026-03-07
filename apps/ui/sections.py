from __future__ import annotations

import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts


def render_coverage_tab(filters):
    ctx = filters
    # Late import to avoid circulars; reuse existing logic exactly.
    
    db_path = ctx['db_path']
    filters_apply = ctx['filters_apply']
    station_callsign = ctx['station_callsign']
    limit_rows = ctx['limit_rows']
    hours = ctx['hours']

    section_map = st.container()
    section_rssi = st.container()
    section_distance = st.container()

    df_grid = ctx['load_coverage_grid'](db_path, filters_apply["since_epoch"])

    with section_map:
        st.subheader("Coverage map")
        raw_packets = ctx['_load_packets_window_raw'](
            db_path=db_path,
            since_iso=filters_apply["since_iso"],
            since_epoch=filters_apply["since_epoch"],
            dst_types=[],
            station_callsign=station_callsign,
            only_heard_by=False,
            igate_filter="",
            source_mode="Heard-by station",
            qas_filter="",
            limit_rows=limit_rows,
        )
        shadow_ctx = {
            "packets": raw_packets,
            "station_callsign": station_callsign,
            "cell_size_km": 3.0,
            "window_hours": hours,
        }
        result = ctx['analysis_shadow_map'].analyze(shadow_ctx)
        if not result.get("implemented"):
            reason = (result.get("summary") or {}).get("reason")
            if reason == "no_local_packets_in_window":
                summary = result.get("summary") or {}
                msg = (
                    "No local packets found for this station in the selected time window. "
                    "Try increasing the time window or disable local radio only."
                )
                last_ts = summary.get("last_local_rx_ts")
                if last_ts:
                    msg = f"{msg} Last local reception: {last_ts}."
                st.info(msg)
            else:
                st.info("Coverage map not available.\nRequires coverage_grid dataset.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            st.markdown("**Radio shadow map**")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Cells", ctx['fmt_int'](summary.get("cells_total")))
                with c2:
                    metric_card("Shadow cells", ctx['fmt_int'](summary.get("shadow_cells")))
                with c3:
                    val = summary.get("coverage_mean")
                    metric_card("Coverage mean", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
                with c4:
                    st.empty()
                with c5:
                    st.empty()
                d1, d2, d3, d4, d5 = st.columns(DASHBOARD_COLUMNS)
                with d1:
                    metric_card("Local points", ctx['fmt_int'](summary.get("local_points")))
                with d2:
                    metric_card("Local igate", ctx['fmt_int'](summary.get("local_points_igate")))
                with d3:
                    metric_card("Local raw", ctx['fmt_int'](summary.get("local_points_raw")))
                with d4:
                    st.empty()
                with d5:
                    st.empty()
                st.dataframe(data.head(30), use_container_width=True, height=300)

    st.divider()
    with section_rssi:
        st.subheader("RSSI heatmap")
        result = ctx['analysis_signal_distance'].analyze(df_grid)
        if not result.get("implemented"):
            st.info(
                "RSSI heatmap not available.\n"
                "No local packets detected in the current window. "
                "Try increasing the time window or disable local radio only."
            )

    st.divider()
    with section_distance:
        st.subheader("Distance heatmap")
        result = ctx['analysis_station_range'].analyze(df_grid)
        if not result.get("implemented"):
            st.info(
                "Distance heatmap not available.\n"
                "No local packets detected in the current window. "
                "Try increasing the time window or disable local radio only."
            )
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


def render_signal_tab(filters):
    ctx = filters
    
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

    with section_signal:
        st.subheader("Signal vs distance (SNR dB)")
        result = ctx['analysis_signal_distance'].analyze(
            packets_signal,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Signal vs distance analysis not implemented.")
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
                    fig = ui_charts.plot_rssi_distance(data_plot, binned=binned, x_max=x_max)
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
        result = ctx['analysis_altitude_distance'].analyze(
            packets_signal,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Altitude vs distance analysis not implemented.")
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
                    fig = ui_charts.plot_altitude_distance(data_plot, med=med, x_max=x_max)
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
        result = ctx['analysis_station_range'].analyze(df_grid)
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


def render_rf_tab(filters):
    ctx = filters
    
    db_path = ctx['db_path']
    filters_apply = ctx['filters_apply']
    station_callsign = ctx['station_callsign']
    station_lat = ctx['station_lat']
    station_lon = ctx['station_lon']
    dst_types = ctx['dst_types']
    limit_rows = ctx['limit_rows']

    section_azimuth = st.container()
    section_terrain = st.container()
    section_antenna = st.container()
    section_horizon = st.container()
    section_range = st.container()
    section_probability = st.container()
    section_summary = st.container()
    section_compare = st.container()

    df_grid = ctx['load_coverage_grid'](db_path, filters_apply["since_epoch"])
    quality_result = ctx['analysis_station_quality'].analyze(df_grid)
    range_result = ctx['analysis_station_range'].analyze(df_grid)
    packets_horizon = ctx['_load_packets_window_raw'](
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
    horizon_result = ctx['analysis_radio_horizon'].analyze(
        packets_horizon,
        station_lat=station_lat,
        station_lon=station_lon,
    )

    with section_azimuth:
        st.subheader("Azimuth radiation")
        result = ctx['analysis_polar'].analyze(df_grid, station_lat=station_lat, station_lon=station_lon)
        if not result.get("implemented"):
            st.info("Not enough packets to compute azimuth radiation. Increase the time window or reduce filters.")
        else:
            data = result.get("data")
            summary = result.get("summary") or {}
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Azimuth bins", ctx['fmt_int'](summary.get("bins")))
                with c2:
                    metric_card("Packet total", ctx['fmt_int'](summary.get("packet_total")))
                with c3:
                    val = summary.get("max_distance_km")
                    metric_card("Max distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("anisotropy_ratio")
                    metric_card("Anisotropy", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
                with c5:
                    st.empty()
                best_sector = summary.get("best_sector_deg")
                worst_sector = summary.get("worst_sector_deg")
                shadow_flag = summary.get("shadow_suspect")
                anisotropy_level = summary.get("anisotropy_level")
                st.caption(
                    f"Best sector: {ctx['fmt_float'](best_sector, 0)}° • "
                    f"Worst sector: {ctx['fmt_float'](worst_sector, 0)}° • "
                    f"Shadow suspect: {'yes' if shadow_flag else 'no'} • "
                    f"Anisotropy: {anisotropy_level or 'n/a'}"
                )
                if "azimuth_center_deg" in data.columns and "max_distance_km" in data.columns:
                    chart = data[["azimuth_center_deg", "max_distance_km"]].copy()
                    chart = chart.sort_values("azimuth_center_deg")
                    st.line_chart(
                        chart,
                        x="azimuth_center_deg",
                        y="max_distance_km",
                        height=240,
                    )
                st.dataframe(
                    data[
                        [
                            "azimuth_center_deg",
                            "packet_count",
                            "p95_distance_km",
                            "mean_rssi_db",
                        ]
                    ].head(20),
                    use_container_width=True,
                    height=300,
                )

    st.divider()

    with section_terrain:
        st.subheader("Terrain analysis")
        result = ctx['analysis_terrain'].analyze(
            df_grid,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Terrain analysis requires sufficient azimuth coverage. Current dataset too small.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
            with c1:
                metric_card("Terrain status", summary.get("terrain_status") or "N/A")
            with c2:
                metric_card("Open sectors", ctx['fmt_int'](summary.get("open_sector_count")))
            with c3:
                metric_card("Limited sectors", ctx['fmt_int'](summary.get("limited_sector_count")))
            with c4:
                val = summary.get("best_opening_deg")
                metric_card("Best opening (°)", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
            with c5:
                val = summary.get("main_limited_deg")
                metric_card("Main limited (°)", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
            d1, d2, d3, d4, d5 = st.columns(DASHBOARD_COLUMNS)
            with d1:
                metric_card("Terrain mask", "yes" if summary.get("terrain_mask_suspected") else "no")
            with d2:
                st.empty()
            with d3:
                st.empty()
            with d4:
                st.empty()
            with d5:
                st.empty()
            if data is not None and not data.empty:
                cols = [
                    "azimuth_center_deg",
                    "packet_count",
                    "p95_distance_km",
                    "mean_rssi_db",
                    "terrain_class",
                ]
                chart_cols = ["azimuth_center_deg", "p95_distance_km"]
                if all(c in data.columns for c in chart_cols):
                    st.markdown("**P95 distance by azimuth sector**")
                    chart = data[chart_cols].sort_values("azimuth_center_deg")
                    st.line_chart(chart, x="azimuth_center_deg", y="p95_distance_km", height=220)
                st.dataframe(data[[c for c in cols if c in data.columns]].head(20), use_container_width=True, height=300)

    st.divider()

    with section_antenna:
        st.subheader("Antenna diagnostics")
        result = ctx['analysis_antenna_health'].analyze(
            df_grid,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Antenna diagnostics requires more packets to estimate antenna pattern.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
            with c1:
                metric_card("Health status", summary.get("health_status") or "N/A")
            with c2:
                val = summary.get("anisotropy_ratio")
                metric_card("Anisotropy ratio", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
            with c3:
                shadow_flag = summary.get("suspected_shadow")
                metric_card("Suspected shadow", "yes" if shadow_flag else "no")
            with c4:
                val = summary.get("best_sector_deg")
                metric_card("Best sector (°)", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
            with c5:
                val = summary.get("worst_sector_deg")
                metric_card("Worst sector (°)", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
            if summary.get("suspected_shadow") is False:
                st.info("No significant directional shadow detected")
            if data is not None and not data.empty:
                cols = [
                    "azimuth_center_deg",
                    "packet_count",
                    "p95_distance_km",
                    "mean_rssi_db",
                ]
                st.dataframe(data[[c for c in cols if c in data.columns]].head(20), use_container_width=True, height=300)

    st.divider()

    with section_horizon:
        st.subheader("Radio horizon")
        result = horizon_result
        if not result.get("implemented"):
            st.info("Radio horizon analysis not implemented.")
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
                    val = summary.get("horizon_mean_km")
                    metric_card("Horizon mean (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("horizon_p95_km")
                    metric_card("Horizon P95 (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("observed_p95_distance_km")
                    metric_card("Observed P95 (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c5:
                    val = summary.get("efficiency_ratio")
                    metric_card("Efficiency ratio", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
                station_alt_used = summary.get("station_alt_m")
                if station_alt_used is not None:
                    st.caption(f"Station altitude used: {ctx['fmt_float'](station_alt_used, 0)} m")
                    if float(station_alt_used) == 400.0:
                        st.info(
                            "Station altitude not available. "
                            "Radio horizon computed with fallback altitude = 400 m."
                        )
                if "horizon_km" in data.columns and "distance_km" in data.columns:
                    med = result.get("binned_data")
                    if med is not None and "sample_count" in med.columns:
                        med = med[med["sample_count"] >= 30]
                    fig = ui_charts.plot_radio_horizon(data, med=med)
                    if fig is not None:
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption("Blue = median observed distance • Orange = theoretical horizon")
                    else:
                        st.scatter_chart(data, x="horizon_km", y="distance_km")
                else:
                    st.info("Radio horizon data missing required columns.")

    st.divider()

    with section_range:
        st.subheader("Station range estimation")
        result = range_result
        if not result.get("implemented"):
            st.info("Station range estimation not implemented.")
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
                st.info("No range statistics available.")

    st.divider()

    with section_probability:
        st.subheader("Coverage probability")
        result = quality_result
        if not result.get("implemented"):
            st.info("Coverage probability analysis not implemented.")
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
                    val = summary.get("rssi_best")
                    metric_card("Best RSSI (dB)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("rssi_mean")
                    metric_card("Mean RSSI (dB)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("quality_score")
                    metric_card("Quality score", f"{ctx['fmt_float'](val, 0)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No quality statistics available.")

    st.divider()

    with section_summary:
        st.subheader("Station synthesis")
        quality_score = (quality_result.get("summary") or {}).get("quality_score")
        if quality_score is None:
            health_status = "N/A"
        elif quality_score >= 80:
            health_status = "GOOD"
        elif quality_score >= 50:
            health_status = "FAIR"
        else:
            health_status = "POOR"

        p95_range = (range_result.get("summary") or {}).get("p95_distance_km")
        if p95_range is None:
            range_status = "N/A"
        elif p95_range < 100:
            range_status = "LOW"
        elif p95_range < 200:
            range_status = "NORMAL"
        else:
            range_status = "HIGH"

        efficiency_ratio = (horizon_result.get("summary") or {}).get("efficiency_ratio")
        if efficiency_ratio is None:
            horizon_status = "N/A"
        elif efficiency_ratio < 0.7:
            horizon_status = "LOW"
        elif efficiency_ratio < 1.1:
            horizon_status = "NORMAL"
        else:
            horizon_status = "HIGH"

        c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
        with c1:
            metric_card("Station health", health_status)
        with c2:
            metric_card("Range status", range_status)
        with c3:
            metric_card("Horizon status", horizon_status)
        with c4:
            st.empty()
        with c5:
            st.empty()

    st.divider()

    with section_compare:
        st.subheader("Station comparison")
        compare_map = ctx['parse_compare_stations'](ctx['os'].getenv("OGN_COMPARE_STATIONS", ""))
        compare_map.setdefault(station_callsign, (station_lat, station_lon))
        packets_compare = ctx['_load_packets_window_raw'](
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
        result = ctx['analysis_station_compare'].analyze(
            packets_compare,
            station_coords=compare_map,
            station_callsigns=list(compare_map.keys()),
        )
        if not result.get("implemented"):
            summary = result.get("summary") or {}
            reason = summary.get("reason")
            if reason == "missing_station_config":
                st.info(
                    "Station comparison requires configuration.\n\n"
                    "Set environment variable:\n\n"
                    "OGN_COMPARE_STATIONS=CALLSIGN:lat,lon;CALLSIGN2:lat,lon\n\n"
                    "Example:\n"
                    "OGN_COMPARE_STATIONS=FK50887:47.33,7.27;FJ12345:46.20,6.14"
                )
            elif reason == "fewer_than_two_stations":
                st.info("Station comparison requires at least 2 configured stations.")
            elif reason == "no_packets_for_configured_stations":
                st.info(
                    "Configured stations were found, but fewer than 2 have usable data in the selected time window."
                )
            elif reason == "invalid_station_coordinates":
                st.info("Some configured stations have missing or invalid coordinates.")
            else:
                st.info("Station comparison not implemented.")
            st.caption("Example: OGN_COMPARE_STATIONS=FK50887:47.3359,7.2728;STATION2:47.20,7.40")
            configured = summary.get("configured_station_count")
            comparable = summary.get("comparable_station_count")
            if configured is not None or comparable is not None:
                c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
                with c1:
                    metric_card("Configured stations", ctx['fmt_int'](configured))
                with c2:
                    metric_card("Comparable stations", ctx['fmt_int'](comparable))
                with c3:
                    st.empty()
                with c4:
                    st.empty()
                with c5:
                    st.empty()
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
            with c1:
                metric_card("Station count", ctx['fmt_int'](summary.get("station_count")))
            with c2:
                metric_card("Best station", summary.get("best_station") or "—")
            with c3:
                val = summary.get("best_rank_score")
                metric_card("Best rank score", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
            with c4:
                st.empty()
            with c5:
                st.empty()
            if data is not None and not data.empty:
                if "station_callsign" in data.columns and "rank_score" in data.columns:
                    chart = data[["station_callsign", "rank_score"]].set_index("station_callsign")
                    st.bar_chart(chart)
                cols = [
                    "station_callsign",
                    "rank_score",
                    "p95_distance_km",
                    "max_distance_km",
                    "packet_total",
                    "quality_score",
                    "health_status",
                ]
                st.dataframe(data[[c for c in cols if c in data.columns]], use_container_width=True, height=300)


def render_debug_tab(filters):
    ctx = filters
    
    section_raw = st.container()
    section_stats = st.container()

    with section_raw:
        st.subheader("Raw packets")
        if not ctx['raw_packets_mode']:
            st.info(
                "Raw packets disabled for performance.\n"
                "Enable in Advanced settings → Developer → Raw packets mode"
            )
        else:
            ctx = ctx['get_packets_context']()
            if ctx.df_packets is None or ctx.df_packets.empty:
                st.info("No raw packets available.")
            else:
                st.dataframe(ctx.df_packets.head(100), use_container_width=True, height=300)

    with section_stats:
        st.subheader("Dataset statistics")
        result = ctx['analysis_station_quality'].analyze(ctx['grid_df_kpi'])
        if not result.get("implemented"):
            st.info("Feature not implemented yet")
