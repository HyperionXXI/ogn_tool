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
    st.subheader("Overview")
    if not ctx.get("has_rf", False):
        st.warning(
            "No RF-gated packets detected in this dataset. "
            "Displaying APRS-IS network traffic only."
        )
    rf_receiver_only_count = ctx.get("rf_receiver_only_count", 0)
    if rf_receiver_only_count > 0 and ctx.get("rf_local_count", 0) == 0:
        st.warning(
            "This station receives RF but does not gate packets to APRS-IS.\n"
            "RF coverage analysis requires gated packets (qAR/qAO)."
        )
    rf_packets = ctx.get("rf_packets")
    aircraft_seen = rf_packets["src"].nunique() if rf_packets is not None and "src" in rf_packets.columns else None
    igates_seen = ctx.get("packets_window")["igate"].nunique() if ctx.get("packets_window") is not None and "igate" in ctx.get("packets_window").columns else None
    redundancy = ctx.get("redundancy")
    mean_redundancy = None
    if redundancy is not None and not redundancy.empty:
        total_aircraft = redundancy.mul(redundancy.index).sum()
        mean_redundancy = float(total_aircraft / redundancy.sum()) if redundancy.sum() else None

    rf_local_count = int(ctx.get("rf_local_count", 0))
    engine_result = compute_rf_engine(rf_packets, ctx.get("station_lat"), ctx.get("station_lon"))
    az_stats = engine_result.azimuth_df
    p95_dist = None
    anisotropy_indicator = None
    if az_stats is not None and not az_stats.empty and "p95_distance_km" in az_stats.columns:
        p95 = ctx["pd"].to_numeric(az_stats.get("p95_distance_km"), errors="coerce")
        if p95.notna().any():
            p95_dist = float(p95.median())
            mean_val = float(p95.mean()) if p95.notna().any() else None
            std_val = float(p95.std()) if p95.notna().any() else None
            anisotropy_indicator = (std_val / mean_val) if mean_val and std_val is not None else None

    components = []
    if rf_local_count >= 0:
        components.append((min(rf_local_count / 2000.0, 1.0), 40.0))
    if p95_dist is not None:
        components.append((min(p95_dist / 80.0, 1.0), 30.0))
    if anisotropy_indicator is not None:
        components.append((max(0.0, 1.0 - min(anisotropy_indicator / 0.6, 1.0)), 30.0))

    score = None
    status = None
    if components:
        score = sum(v * w for v, w in components) / sum(w for _, w in components) * 100.0
        score = round(score, 1)
        status = "GOOD" if score >= 80 else "FAIR" if score >= 50 else "POOR"

    c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
    metric_card(c1, "RF packets", ctx.get("rf_count"))
    metric_card(c2, "Aircraft seen", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
    metric_card(c3, "IGates seen", ctx["fmt_int"](igates_seen) if igates_seen is not None else "—")
    metric_card(c4, "RF Health", f"{score} / 100" if score is not None else "—")
    metric_card(c5, "Mean redundancy", ctx["fmt_float"](mean_redundancy, 2) if mean_redundancy is not None else "—")
    if status:
        st.caption(f"RF Health Status: {status}")
