from __future__ import annotations

import streamlit as st
import pandas as pd

from apps.ui.layout import DASHBOARD_COLUMNS
from apps.ui.metrics import metric_card
from apps.ui import charts as ui_charts
from apps.ui.charts import render_rf_cartography
from ogn_tool.analysis.rf_probability_field import build_rf_probability_field


def render_aircraft_page(ctx):
    dataset = ctx.get("dataset", {})
    st.subheader("Aircraft traffic")
    rf_mode = ctx.get("has_rf", False)
    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")
    aircraft_packets = ctx.get("aircraft_packets")
    if aircraft_packets is None:
        aircraft_packets = packets_window

    st.markdown("**FANET local performance (heard by station)**")
    fanet_local = ctx.get("fanet_local")
    test_fanet = ctx.get("test_fanet_igate", "")
    if test_fanet:
        st.caption(f"FANET IGate override: {test_fanet}")
    if fanet_local is None or fanet_local.empty:
        st.info("No FANET packets heard by this station.")
    else:
        c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
        with c1:
            metric_card("FANET packets (local)", ctx["fmt_int"](len(fanet_local)))
        with c2:
            metric_card("FANET devices", ctx["fmt_int"](fanet_local["src"].nunique() if "src" in fanet_local.columns else 0))
        with c3:
            max_dist = fanet_local["distance_km"].max() if "distance_km" in fanet_local.columns else None
            metric_card("Max distance (km)", ctx["fmt_float"](max_dist, 1) if max_dist is not None else "—")
        with c4:
            p95 = fanet_local["distance_km"].quantile(0.95) if "distance_km" in fanet_local.columns and not fanet_local.empty else None
            metric_card("P95 distance (km)", ctx["fmt_float"](p95, 1) if p95 is not None else "—")
        with c5:
            st.empty()
        unique_positions = 0
        if "lat" in fanet_local.columns and "lon" in fanet_local.columns:
            unique_positions = int(fanet_local[["lat", "lon"]].dropna().drop_duplicates().shape[0])
        if "src" in fanet_local.columns:
            fanet_devices = int(fanet_local["src"].nunique())
            if fanet_devices == 1 and max_dist == 0:
                st.info(
                    "FANET local devices detected: 1\n"
                    f"Position variance: {ctx['fmt_float'](0, 0)} km\n"
                    "Likely fixed device (e.g. weather station)"
                )
        if unique_positions == 1 and fanet_local is not None and not fanet_local.empty:
            st.caption("Unique FANET positions: 1")
        if "src" in fanet_local.columns:
            st.subheader("FANET devices (top 20)")
            st.bar_chart(fanet_local["src"].value_counts().head(20))
        if "ts_epoch" in fanet_local.columns:
            ts = pd.to_datetime(fanet_local["ts_epoch"], unit="s", utc=True, errors="coerce")
            per_hour = ts.dt.floor("h").value_counts().sort_index()
            if not per_hour.empty:
                st.subheader("FANET local packets per hour")
                st.line_chart(per_hour)
        st.subheader("FANET local coverage (grid)")
        fanet_grid = build_rf_probability_field(fanet_local)
        if "sample_count" in fanet_grid.columns:
            low_samples = int((fanet_grid["sample_count"] < 5).sum())
            c6, c7, c8, c9, c10 = st.columns(DASHBOARD_COLUMNS)
            with c6:
                metric_card("Cells (low samples)", ctx["fmt_int"](low_samples))
            with c7:
                metric_card("Cells (total)", ctx["fmt_int"](len(fanet_grid)))
            with c8:
                st.empty()
            with c9:
                st.empty()
            with c10:
                st.empty()
            if low_samples > 0:
                st.info("FANET reliability low in some cells (sample_count < 5).")
        render_rf_cartography(fanet_grid, ctx.get("station_lat"), ctx.get("station_lon"), ctx.get("basemap_label"), ["RF probability", "Confidence"])

    st.markdown("**OGN vs FANET comparison (local, same grid)**")
    rf_local = ctx.get("rf_local")
    if rf_local is None or rf_local.empty or fanet_local is None or fanet_local.empty:
        st.info("Comparison requires both OGN RF local and FANET local datasets.")
    else:
        ogn_grid = build_rf_probability_field(rf_local)
        fanet_grid = build_rf_probability_field(fanet_local)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**OGN RF (local)**")
            render_rf_cartography(ogn_grid, ctx.get("station_lat"), ctx.get("station_lon"), ctx.get("basemap_label"), ["RF probability", "Confidence"])
        with col2:
            st.markdown("**FANET (local)**")
            render_rf_cartography(fanet_grid, ctx.get("station_lat"), ctx.get("station_lon"), ctx.get("basemap_label"), ["RF probability", "Confidence"])

    st.markdown("**FANET network traffic (dataset)**")
    fanet_global = ctx.get("fanet_packets_global")
    if fanet_global is None or fanet_global.empty:
        st.info("No FANET packets in dataset.")
    else:
        c6, c7, c8, c9, c10 = st.columns(DASHBOARD_COLUMNS)
        with c6:
            metric_card("FANET packets (global)", ctx["fmt_int"](len(fanet_global)))
        with c7:
            metric_card("FANET devices", ctx["fmt_int"](fanet_global["src"].nunique() if "src" in fanet_global.columns else 0))
        with c8:
            st.empty()
        with c9:
            st.empty()
        with c10:
            st.empty()
        if "src" in fanet_global.columns:
            st.subheader("FANET devices (global, top 20)")
            st.bar_chart(fanet_global["src"].value_counts().head(20))
        if (fanet_local is None or fanet_local.empty) and len(fanet_global) > 0:
            st.warning("FANET traffic present in APRS-IS, but none received by this station.")

    if rf_mode:
        if "distance_km" in rf_packets.columns and "altitude_m" in rf_packets.columns:
            st.scatter_chart(rf_packets.rename(columns={"distance_km": "x", "altitude_m": "y"})[["x", "y"]])
        aircraft_counts = rf_packets["src"].value_counts().head(50)
        st.metric("Aircraft count", ctx["fmt_int"](rf_packets["src"].nunique()))
        st.dataframe(aircraft_counts.reset_index(name="packets"), use_container_width=True, height=300)
    else:
        st.warning("Aircraft RF analysis unavailable.")
        if aircraft_packets is None or aircraft_packets.empty:
            st.info("No packets available.")
            return
        aircraft_counts = aircraft_packets["src"].value_counts().head(50)
        st.metric("Aircraft count", ctx["fmt_int"](aircraft_packets["src"].nunique()))
        st.dataframe(aircraft_counts.reset_index(name="packets"), use_container_width=True, height=300)
        if "lat" in aircraft_packets.columns and "lon" in aircraft_packets.columns:
            st.subheader("Aircraft positions")
            st.scatter_chart(aircraft_packets.rename(columns={"lat": "x", "lon": "y"})[["x", "y"]])


