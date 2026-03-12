from __future__ import annotations

import pandas as pd
import streamlit as st

from apps.ui.layout import DASHBOARD_COLUMNS
from apps.ui.view_models.station_view import StationAnalysisView
from apps.ui.metrics import metric_card


def render_directional_rf_page(ctx):
    view = StationAnalysisView.from_context(ctx)
    st.markdown("<h2>Directional RF Analysis</h2>", unsafe_allow_html=True)
    if not view.has_rf:
        st.warning("No packets for this station in APRS-IS dataset.")
        return

    hist_data = view.azimuth_histogram
    directional_balance = view.directional_balance
    station_metrics = view.metrics.get("station_metrics")
    station_callsign = ctx.get("station_callsign")

    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

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

    c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
    with c1:
        total_packets = metric_row.get("packet_count") if metric_row is not None else None
        metric_card("Packet total", ctx["fmt_int"](total_packets) if total_packets is not None else "—")
    with c2:
        p95 = metric_row.get("p95_distance") if metric_row is not None else None
        metric_card("P95 median (km)", ctx["fmt_float"](p95, 1) if p95 is not None else "—")
    with c3:
        anisotropy = directional_balance.get("anisotropy") if isinstance(directional_balance, dict) else None
        metric_card("Anisotropy", ctx["fmt_float"](anisotropy, 2) if anisotropy is not None else "—")
    with c4:
        st.empty()
    with c5:
        st.empty()

    if hist_data:
        df = pd.DataFrame({
            "sector": hist_data.get("edges", [])[:-1],
            "packets": hist_data.get("hist", []),
        })
        st.subheader("Azimuth reception distribution")
        st.bar_chart(df.set_index("sector"), use_container_width=True)
    else:
        st.info("No azimuth histogram available in the dataset.")

    if isinstance(directional_balance, dict) and directional_balance:
        st.subheader("Directional balance")
        st.dataframe(pd.DataFrame([directional_balance]), use_container_width=True)


def render_legacy_rf_page(filters):
    st.info("Legacy RF tab removed. Use Overview / RF Map / Propagation / Directional RF / Terrain.")

