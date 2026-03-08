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


def render_rf_map_page(ctx):
    st.subheader("RF Coverage")
    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")
    data_source = ctx.get("data_source", "APRS-IS gated")
    if ctx.get("rf_local_count", 0) < 500:
        st.warning("RF dataset too small for reliable coverage analysis.")
    if rf_packets is None or rf_packets.empty:
        st.warning("No RF-gated packets detected (qAR / qAO). Showing APRS-IS network coverage instead.")
        dataset = packets_window
    else:
        dataset = rf_packets
    st.caption(f"Data source: {data_source}")
    if dataset is None or (hasattr(dataset, "empty") and dataset.empty):
        st.info("No packets available for coverage map.")
        return

    st.caption(
        "RF probability is a normalized packet-density proxy (not absolute reception probability). "
        "Use confidence and minimum samples to assess reliability."
    )
    st.markdown(
        "**Legend (probability bands)**: "
        "<span style='color:#dc2626'>0–0.2 very low</span> · "
        "<span style='color:#f97316'>0.2–0.4 low</span> · "
        "<span style='color:#eab308'>0.4–0.6 medium</span> · "
        "<span style='color:#84cc16'>0.6–0.8 high</span> · "
        "<span style='color:#22c55e'>0.8–1.0 very high</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "**Legend (max distance footprint)**: "
        "<span style='color:#e2e8f0'>0–10 km</span> · "
        "<span style='color:#bfdbfe'>10–20 km</span> · "
        "<span style='color:#93c5fd'>20–40 km</span> · "
        "<span style='color:#60a5fa'>40–80 km</span> · "
        "<span style='color:#3b82f6'>80–120 km</span> · "
        "<span style='color:#2563eb'>120–160 km</span> · "
        "<span style='color:#1e40af'>160–250 km</span> · "
        "<span style='color:#111827'>>250 km</span>",
        unsafe_allow_html=True,
    )
    layers = st.multiselect(
        "Map layers",
        ["Coverage cloud", "RF probability", "RF contours", "Confidence", "Max distance footprint"],
        default=["Coverage cloud", "RF probability", "Confidence"],
    )
    altitude_filter = st.checkbox("Apply altitude filter", value=False)
    alt_min, alt_max = st.slider(
        "Altitude range (m)",
        min_value=0,
        max_value=8000,
        value=(0, 2000),
        step=100,
    )
    if altitude_filter and "altitude_m" in dataset.columns:
        alt_series = ctx["pd"].to_numeric(dataset["altitude_m"], errors="coerce")
        dataset = dataset[(alt_series >= float(alt_min)) & (alt_series <= float(alt_max))]
        if dataset.empty:
            st.info("No packets remain after altitude filtering.")
            return
    elif altitude_filter and "altitude_m" not in dataset.columns:
        st.info("Altitude field not present in packets. Filter skipped.")
    max_range_km = st.slider("Max range (km)", min_value=10, max_value=300, value=200, step=10)
    if "distance_km" in dataset.columns:
        dist_series = ctx["pd"].to_numeric(dataset["distance_km"], errors="coerce")
        dataset = dataset[dist_series <= float(max_range_km)]
        if dataset.empty:
            st.info("No packets remain after range filtering.")
            return
    min_samples = st.slider("Min samples per cell", min_value=1, max_value=50, value=5, step=1)
    side_by_side = st.checkbox("Side-by-side Probability / Confidence", value=True)
    engine_result = compute_rf_engine(dataset, ctx.get("station_lat"), ctx.get("station_lon"))
    rf_grid = engine_result.coverage_grid
    if "sample_count" in rf_grid.columns:
        rf_grid = rf_grid[rf_grid["sample_count"] >= min_samples]
    if rf_grid.empty:
        st.info("Not enough samples for the selected minimum. Lower the threshold.")
        return
    if side_by_side:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**RF probability**")
            render_rf_cartography(rf_grid, ctx, ["RF probability", "RF contours"])
        with col2:
            st.markdown("**Confidence (sample density)**")
            render_rf_cartography(rf_grid, ctx, ["Confidence"])
        if "Coverage cloud" in layers:
            st.markdown("**Coverage cloud**")
            render_rf_cartography(rf_grid, ctx, ["Coverage cloud"])
        if "Max distance footprint" in layers:
            st.markdown("**Max distance footprint**")
            render_rf_cartography(rf_grid, ctx, ["Max distance footprint"])
    else:
        render_rf_cartography(rf_grid, ctx, layers)
