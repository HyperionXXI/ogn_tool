from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card


def render_propagation_page(filters):
    ctx = filters
    dataset = ctx.get("dataset", {})
    st.markdown("<h2>Propagation</h2>", unsafe_allow_html=True)
    if ctx.get("rf_packets") is None or getattr(ctx.get("rf_packets"), "empty", False):
        st.warning("No packets for this station in APRS-IS dataset.")
        return

    station_callsign = ctx.get("station_callsign")

    packets_signal = None
    observations = dataset.get("observations")
    packets_filtered = dataset.get("packets_filtered")
    rf_packets_ctx = ctx.get("rf_packets")
    if isinstance(observations, pd.DataFrame) and not observations.empty:
        packets_signal = observations
    elif isinstance(packets_filtered, pd.DataFrame) and not packets_filtered.empty:
        packets_signal = packets_filtered
    elif isinstance(rf_packets_ctx, pd.DataFrame) and not rf_packets_ctx.empty:
        packets_signal = rf_packets_ctx

    station_metrics = dataset.get("station_metrics")

    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    if packets_signal is None or getattr(packets_signal, "empty", False):
        st.info("Not enough RF packets for this analysis.")
        return
    if len(packets_signal) < 200:
        st.info("Not enough RF packets for this analysis.")
        return

    section_signal = st.container()
    section_altitude = st.container()
    section_distribution = st.container()

    metric_row = None
    if (
        station_metrics is not None
        and hasattr(station_metrics, "empty")
        and not station_metrics.empty
        and station_callsign
    ):
        metric_row = station_metrics[station_metrics["igate"].astype(str) == str(station_callsign)]
        if not metric_row.empty:
            metric_row = metric_row.iloc[0]

    with section_signal:
        st.subheader("Signal vs distance (SNR dB)")
        c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
        with c1:
            metric_card("Packet total", ctx["fmt_int"](len(packets_signal)))
        with c2:
            val = metric_row.get("max_distance") if metric_row is not None else None
            metric_card("Max distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
        with c3:
            val = metric_row.get("p95_distance") if metric_row is not None else None
            metric_card("P95 distance (km)", f"{ctx['fmt_float'](val, 1)}" if val is not None else "—")
        with c4:
            st.empty()
        with c5:
            st.empty()

        if "distance_km" in packets_signal.columns and ("rssi_db" in packets_signal.columns or "rssi" in packets_signal.columns):
            st.markdown("**RSSI vs distance**")
            rssi_col = "rssi_db" if "rssi_db" in packets_signal.columns else "rssi"
            st.scatter_chart(packets_signal, x="distance_km", y=rssi_col)
        else:
            st.info("RSSI vs distance data missing required columns.")

    st.divider()
    with section_altitude:
        st.subheader("Altitude vs distance")
        if "altitude_m" not in packets_signal.columns:
            st.info("Altitude field not present in packets.")
        elif "distance_km" not in packets_signal.columns:
            st.info("Distance field not present in packets.")
        else:
            st.scatter_chart(packets_signal, x="distance_km", y="altitude_m")

    st.divider()
    with section_distribution:
        st.subheader("Distance distribution")
        if "distance_km" not in packets_signal.columns:
            st.info("Distance field not present in packets.")
        else:
            st.bar_chart(packets_signal["distance_km"])
