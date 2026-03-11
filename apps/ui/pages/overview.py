from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card


def render_overview_page(ctx):
    import streamlit as st
    st.write("DEBUG: page renderer executed")
    dataset = ctx.get("dataset", {})
    st.markdown("<h2>Overview</h2>", unsafe_allow_html=True)
    rf_packets = ctx.get("rf_packets")

    rf_packets_count = 0
    observations = dataset.get("observations")
    if isinstance(observations, pd.DataFrame) and not observations.empty:
        rf_packets_count = int(len(observations))
    elif isinstance(rf_packets, pd.DataFrame) and not rf_packets.empty:
        rf_packets_count = int(len(rf_packets))

    readiness = "GOOD" if rf_packets_count >= 2000 else "FAIR" if rf_packets_count >= 500 else "LOW"

    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_packets_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_packets_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    st.info(
        """
Dataset source: APRS-IS

Station packets are filtered using the APRS igate field.

Note:
APRS-IS shows the station that injected the packet into the network,
not necessarily the RF receiver.
"""
    )

    aircraft_seen = rf_packets["src"].nunique() if rf_packets is not None and "src" in rf_packets.columns else None
    max_range = None
    health = None
    if isinstance(dataset.get("rf_diagnosis"), dict):
        health = dataset.get("rf_diagnosis", {}).get("health")
    try:
        health_val = float(health) if health is not None else None
    except (TypeError, ValueError):
        health_val = None
    health_status = ("GOOD" if health_val is not None and health_val >= 80 else "FAIR" if health_val is not None and health_val >= 50 else "POOR")

    st.markdown("<div style='font-size:18px;font-weight:600;'>Key Metrics</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    metric_card(col1, "Packets heard", ctx["fmt_int"](rf_packets_count))
    metric_card(col2, "Aircraft seen", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
    metric_card(col3, "Max distance", ctx["fmt_float"](max_range, 1) if max_range is not None else "—")
    metric_card(col4, "RF Health", f"{ctx['fmt_float'](health, 0)} / 100" if health is not None else "—")

    st.markdown("**Station health diagnostic**")
    st.write(health_status)
