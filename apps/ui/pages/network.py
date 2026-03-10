from __future__ import annotations

import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field


def render_network_page(ctx):
    dataset = ctx.get("dataset", {})
    st.subheader("Network")
    rf_count = ctx.get("rf_count", 0)
    internet_count = ctx.get("internet_count", 0)
    server_count = ctx.get("server_count", 0)
    st.markdown("**Packet source distribution**")
    st.bar_chart(
        ctx["pd"].Series(
            {
                "RF IGates (qAR / qAO)": rf_count,
                "Internet clients (qAC)": internet_count,
                "APRS servers (qAS)": server_count,
            }
        )
    )
    packets = ctx.get("network_packets")
    if packets is not None and not packets.empty and "igate" in packets.columns:
        igates = packets.groupby("igate").size().sort_values(ascending=False).head(15)
        st.subheader("Top IGates in dataset")
        st.bar_chart(igates)
    overlap = ctx.get("station_overlap")
    if overlap is not None and not overlap.empty:
        st.subheader("Station overlap")
        st.dataframe(overlap, use_container_width=True, height=300)
    redundancy = ctx.get("redundancy")
    if redundancy is not None and not redundancy.empty:
        st.subheader("Aircraft redundancy")
        st.bar_chart(redundancy)

