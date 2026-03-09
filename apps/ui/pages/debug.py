from __future__ import annotations

import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field
import sqlite3


def render_debug_page(filters):
    ctx = filters
    
    section_raw = st.container()
    section_stats = st.container()

    with section_raw:
        st.subheader("Raw packets")
        if not ctx['raw_packets_mode']:
            st.info(
                "Raw packets disabled for performance.\n"
                "Enable in Advanced settings → Developer → Raw packets mode"
            )
        else:
            packets_ctx = ctx['get_packets_context']()
            if packets_ctx.df_packets is None or packets_ctx.df_packets.empty:
                st.info("No raw packets available.")
            else:
                st.dataframe(packets_ctx.df_packets.head(100), use_container_width=True, height=300)

    with section_stats:
        st.subheader("Dataset statistics")
        result = ctx['analysis_station_quality'].analyze(ctx['grid_df_kpi'])
        if not result.get("implemented"):
            st.info("Feature not implemented yet")

    def show_station_stats(con, station):
        q = """
        SELECT COUNT(*)
        FROM packets
        WHERE igate = :station
        """
        return con.execute(q, {"station": station}).fetchone()[0]

    station = ctx.get("station_callsign")
    if station:
        try:
            con = sqlite3.connect(ctx["db_path"])
            count = show_station_stats(con, station)
            con.close()
            st.metric("Packets received via station", count)
        except Exception:
            st.info("Station stats unavailable.")
