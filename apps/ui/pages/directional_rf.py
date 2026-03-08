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


def render_directional_rf_page(ctx):
    st.markdown("<h2>Directional RF Analysis</h2>", unsafe_allow_html=True)
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")
    engine_result = compute_rf_engine(ctx.get("rf_packets"), ctx.get("station_lat"), ctx.get("station_lon"))
    az_stats = engine_result.azimuth_df
    if engine_result.metrics.get("rf_packets", 0) < 200:
        st.info("Not enough RF packets for this analysis.")
        return
    if az_stats is None or az_stats.empty:
        st.info("No azimuth statistics available.")
        return

    p95 = ctx["pd"].to_numeric(az_stats.get("p95_distance_km"), errors="coerce")
    packet_count = ctx["pd"].to_numeric(az_stats.get("packet_count"), errors="coerce").fillna(0.0)
    p95_median = float(p95.median()) if p95.notna().any() else None
    mean_val = float(p95.mean()) if p95.notna().any() else None
    std_val = float(p95.std()) if p95.notna().any() else None
    anisotropy = (std_val / mean_val) if mean_val and std_val is not None else None
    total_packets = float(packet_count.sum()) if packet_count.notna().any() else 0.0

    c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
    with c1:
        metric_card("Packet total", ctx["fmt_int"](total_packets))
    with c2:
        metric_card("P95 median (km)", ctx["fmt_float"](p95_median, 1) if p95_median is not None else "—")
    with c3:
        metric_card("Anisotropy", ctx["fmt_float"](anisotropy, 2) if anisotropy is not None else "—")
    with c4:
        st.empty()
    with c5:
        st.empty()
    dataset_count = ctx.get("rf_local_count", 0) or total_packets
    if dataset_count < 500:
        st.caption("Confidence: LOW (dataset too small)")
    elif dataset_count < 2000:
        st.caption("Confidence: MEDIUM (limited samples)")
    else:
        st.caption("Confidence: GOOD")

    st.markdown("**Polar coverage (P95 distance)**")
    polar_fig = ui_charts.plot_polar_p95(az_stats)
    if polar_fig is not None:
        st.plotly_chart(polar_fig, use_container_width=True)

    st.markdown("**P95 distance by azimuth**")
    if "az_bin" in az_stats.columns and "p95_distance_km" in az_stats.columns:
        st.line_chart(az_stats, x="az_bin", y="p95_distance_km", height=240)

    st.markdown("**Packet density by azimuth**")
    if "az_bin" in az_stats.columns and "packet_count" in az_stats.columns:
        density = az_stats[["az_bin", "packet_count"]].set_index("az_bin")
        st.bar_chart(density)

    st.markdown("**Shadow sector detection**")
    shadow_threshold = None
    if p95_median is not None:
        shadow_threshold = p95_median * 0.6
    min_packets = max(10.0, 0.02 * total_packets) if total_packets else 10.0
    shadow = az_stats.copy()
    shadow["p95_distance_km"] = p95
    shadow["packet_count"] = packet_count
    if shadow_threshold is not None:
        shadow = shadow[
            (shadow["packet_count"] >= min_packets)
            & (shadow["p95_distance_km"] <= shadow_threshold)
        ]
    else:
        shadow = shadow.iloc[0:0]
    if shadow.empty:
        st.info("No strong shadow sectors detected with current thresholds.")
    else:
        st.caption(f"Shadow threshold: ≤ {ctx['fmt_float'](shadow_threshold, 1)} km")
        st.dataframe(
            shadow[["az_bin", "packet_count", "p95_distance_km"]],
            use_container_width=True,
            height=240,
        )


def render_legacy_rf_page(filters):
    st.info("Legacy RF tab removed. Use Overview / RF Map / Propagation / Directional RF / Terrain.")
