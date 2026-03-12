from __future__ import annotations

import streamlit as st

from ogn_tool.ui.charts import render_rf_cartography
from ogn_tool.ui.view_models.station_view import StationAnalysisView


def render_rf_map_page(ctx):
    view = StationAnalysisView.from_context(ctx)
    st.markdown("<h2>RF Coverage</h2>", unsafe_allow_html=True)
    data_source = ctx.get("data_source", "APRS-IS gated")
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    rf_packets = view.metrics.get("packets_rf")
    if rf_packets is None or (hasattr(rf_packets, "empty") and rf_packets.empty):
        st.warning("No packets for this station in APRS-IS dataset.")
        return

    coverage_grid = view.coverage
    if coverage_grid is None or (hasattr(coverage_grid, "empty") and coverage_grid.empty):
        st.info("Coverage grid not available in the dataset.")
        return

    st.caption(f"Data source: {data_source}")

    st.markdown(
        "**Legend (probability bands)**: "
        "<span style='color:#dc2626'>0-0.2 very low</span> · "
        "<span style='color:#f97316'>0.2-0.4 low</span> · "
        "<span style='color:#eab308'>0.4-0.6 medium</span> · "
        "<span style='color:#84cc16'>0.6-0.8 high</span> · "
        "<span style='color:#22c55e'>0.8-1.0 very high</span>",
        unsafe_allow_html=True,
    )

    layers = st.multiselect(
        "Map layers",
        ["Coverage cloud", "RF probability", "RF contours", "Confidence", "Max distance footprint"],
        default=["Coverage cloud", "RF probability", "Confidence"],
        help="Toggle map layers",
    )

    min_samples = st.slider(
        "Min samples per cell",
        min_value=1,
        max_value=50,
        value=5,
        step=1,
        help="Minimum samples for a cell to appear",
    )

    rf_grid = coverage_grid
    if "sample_count" in rf_grid.columns:
        rf_grid = rf_grid[rf_grid["sample_count"] >= min_samples]
    elif "packets" in rf_grid.columns:
        rf_grid = rf_grid[rf_grid["packets"] >= min_samples]

    if rf_grid.empty:
        st.info("Not enough samples for the selected minimum. Lower the threshold.")
        return

    render_rf_cartography(rf_grid, view.station_lat, view.station_lon, ctx.get("basemap_label"), layers)
