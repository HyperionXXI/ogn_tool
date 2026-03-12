from __future__ import annotations

import streamlit as st

from apps.ui.layout import DASHBOARD_COLUMNS
from apps.ui.view_models.station_view import StationAnalysisView
from apps.ui.metrics import metric_card


def render_terrain_page(ctx):
    view = StationAnalysisView.from_context(ctx)
    st.markdown("<h2>Terrain</h2>", unsafe_allow_html=True)
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    shadow_map = view.shadow_map

    st.markdown("**Terrain analysis**")
    if shadow_map is None or (hasattr(shadow_map, "empty") and shadow_map.empty):
        st.info("No terrain visibility data available in the dataset.")
        return

    c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
    with c1:
        metric_card("Shadow sectors", ctx["fmt_int"](len(shadow_map)))
    with c2:
        st.empty()
    with c3:
        st.empty()
    with c4:
        st.empty()
    with c5:
        st.empty()

    if "azimuth_center_deg" in shadow_map.columns and "p95_distance_km" in shadow_map.columns:
        st.line_chart(shadow_map, x="azimuth_center_deg", y="p95_distance_km", height=220)
    else:
        st.dataframe(shadow_map, use_container_width=True, height=300)

