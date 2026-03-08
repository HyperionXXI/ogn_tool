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


def render_terrain_page(ctx):
    st.markdown("<h2>Terrain</h2>", unsafe_allow_html=True)
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    df_grid = ctx.get("grid_df_kpi")
    station_lat = ctx.get("station_lat")
    station_lon = ctx.get("station_lon")
    engine_result = compute_rf_engine(ctx.get("rf_packets"), station_lat, station_lon)
    st.markdown("**Terrain analysis**")
    if engine_result.metrics.get("rf_packets", 0) < 200:
        st.info("Not enough RF packets for this analysis.")
        return
    result = (engine_result.metrics.get("terrain") or {"implemented": False})
    if not result.get("implemented"):
        st.info("Terrain analysis requires sufficient azimuth coverage. Current dataset too small.")
    else:
        summary = result.get("summary") or {}
        data = result.get("data")
        c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
        with c1:
            metric_card("Terrain status", summary.get("terrain_status") or "N/A")
        with c2:
            metric_card("Open sectors", ctx["fmt_int"](summary.get("open_sector_count")))
        with c3:
            metric_card("Limited sectors", ctx["fmt_int"](summary.get("limited_sector_count")))
        with c4:
            metric_card("Best opening (°)", ctx["fmt_float"](summary.get("best_opening_deg"), 0))
        with c5:
            metric_card("Main limited (°)", ctx["fmt_float"](summary.get("main_limited_deg"), 0))
        if summary.get("terrain_mask_suspected") is True:
            st.warning("Terrain mask suspected in multiple adjacent sectors.")
        elif summary.get("terrain_mask_suspected") is False:
            st.info("No significant terrain mask detected.")
        if data is not None and not data.empty:
            st.line_chart(data, x="azimuth_center_deg", y="p95_distance_km", height=220)

    st.markdown("**Visibility envelope (P10 altitude by azimuth)**")
    rf_packets = ctx.get("rf_packets")
    vis = (engine_result.metrics.get("terrain_visibility") or {"implemented": False})
    if not vis.get("implemented"):
        st.info("Visibility envelope requires altitude data and sufficient RF samples.")
    else:
        summary = vis.get("summary") or {}
        data = vis.get("data")
        v1, v2, v3, v4, v5 = st.columns(DASHBOARD_COLUMNS)
        with v1:
            metric_card("Azimuth sectors", ctx["fmt_int"](summary.get("sector_count")))
        with v2:
            metric_card("Shadow sectors", ctx["fmt_int"](summary.get("shadow_sector_count")))
        with v3:
            metric_card("Mean P10 alt (m)", ctx["fmt_float"](summary.get("mean_p10_altitude_m"), 0))
        with v4:
            metric_card("Worst sector (°)", ctx["fmt_float"](summary.get("worst_sector_deg"), 0))
        with v5:
            metric_card("Min samples/bin", ctx["fmt_int"](summary.get("min_samples")))
        if data is not None and not data.empty:
            st.line_chart(data, x="azimuth_center_deg", y="p10_altitude_m", height=220)
