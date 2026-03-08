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


def render_overview_page(ctx):
    st.markdown("<h2>Overview</h2>", unsafe_allow_html=True)
    rf_packets = ctx.get("rf_packets")
    rf_local_count = int(ctx.get("rf_local_count", 0))
    engine_result = compute_rf_engine(rf_packets, ctx.get("station_lat"), ctx.get("station_lon"))
    rf_packets_count = int(engine_result.metrics.get("rf_packets", 0))
    readiness = "GOOD" if rf_packets_count >= 2000 else "FAIR" if rf_packets_count >= 500 else "LOW"

    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_packets_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_packets_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    aircraft_seen = rf_packets["src"].nunique() if rf_packets is not None and "src" in rf_packets.columns else None
    max_range = engine_result.metrics.get("max_range_km")
    health = engine_result.metrics.get("health")
    health_status = "GOOD" if health is not None and health >= 80 else "FAIR" if health is not None and health >= 50 else "POOR"

    st.markdown("<div style='font-size:18px;font-weight:600;'>Key Metrics</div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    metric_card(col1, "Packets heard", ctx["fmt_int"](rf_packets_count))
    metric_card(col2, "Aircraft seen", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
    metric_card(col3, "Max distance", ctx["fmt_float"](max_range, 1) if max_range is not None else "—")
    metric_card(col4, "RF Health", f"{ctx['fmt_float'](health, 0)} / 100" if health is not None else "—")

    st.markdown("**Station health diagnostic**")
    st.write(health_status)
