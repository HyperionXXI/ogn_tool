from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import sqlite3

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field


def render_diagnostics_page(ctx):
    dataset = ctx.get("dataset", {})
    st.markdown("<h2>Diagnostics</h2>", unsafe_allow_html=True)
    packets_window = ctx.get("packets_window")
    rf_packets = ctx.get("rf_packets")
    rf_local = ctx.get("rf_local")
    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"
    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    st.markdown("**Packets summary**")
    c1, c2, c3, c4 = st.columns(4)
    metric_card(c1, "Total packets", ctx["fmt_int"](len(packets_window) if packets_window is not None else 0))
    metric_card(c2, "RF packets", ctx["fmt_int"](len(rf_packets) if rf_packets is not None else 0))
    metric_card(c3, "RF local", ctx["fmt_int"](len(rf_local) if rf_local is not None else 0))
    metric_card(c4, "Hours", ctx["fmt_int"](ctx.get("hours")))

    st.markdown("**Collector filter (APRS-IS)**")
    ogn_filter = (ctx.get("os").getenv("OGN_FILTER") if ctx.get("os") else "") or ""
    if ogn_filter:
        st.code(f"OGN_FILTER={ogn_filter}")
    else:
        st.warning("OGN_FILTER is empty. APRS-IS feed may be unfiltered (global traffic).")

    st.markdown("**SQL qAR / qAO count**")
    if packets_window is not None and "qas" in packets_window.columns:
        qas = packets_window["qas"].astype(str).str.upper()
        qar = int((qas == "QAR").sum())
        qao = int((qas == "QAO").sum())
        qac = int((qas == "QAC").sum())
        qas_srv = int((qas == "QAS").sum())
        st.write({"qAR": qar, "qAO": qao, "qAC": qac, "qAS": qas_srv})
    else:
        st.info("No qas column available for SQL-style counts.")

    st.markdown("**Station comparison**")
    st.info("Station comparison is not yet migrated to the engine dataset.")

    st.markdown("**RF reception metrics by station**")
    rf_receptions = ctx.get("rf_packets")
    if rf_receptions is None or rf_receptions.empty or "receiver" not in rf_receptions.columns:
        st.info("No rf_receptions data available for station metrics.")
    else:
        df_rx = rf_receptions.copy()
        df_rx["snr"] = pd.to_numeric(df_rx.get("snr"), errors="coerce")
        df_rx["freq_offset"] = pd.to_numeric(df_rx.get("freq_offset"), errors="coerce")
        df_rx["bit_errors"] = pd.to_numeric(df_rx.get("bit_errors"), errors="coerce")
        summary = (
            df_rx.groupby("receiver", dropna=False)
            .agg(
                packet_count=("receiver", "size"),
                avg_snr=("snr", "mean"),
                avg_freq_offset=("freq_offset", "mean"),
                bit_error_rate=("bit_errors", lambda x: (pd.to_numeric(x, errors="coerce").fillna(0) > 0).mean()),
            )
            .reset_index()
            .sort_values("packet_count", ascending=False)
        )
        st.dataframe(summary, use_container_width=True, height=240)

    st.markdown("**Station summary (SQL)**")
    db_path = ctx.get("db_path")
    if db_path:
        try:
            con = sqlite3.connect(db_path)
            sql = """
            SELECT receiver,
                   COUNT(*) AS packets,
                   AVG(snr) AS avg_snr,
                   AVG(freq_offset) AS avg_offset
            FROM rf_receptions
            GROUP BY receiver
            """
            df_sql = pd.read_sql_query(sql, con)
            st.dataframe(df_sql, use_container_width=True, height=240)
        except Exception as e:
            st.info(f"Unable to query rf_receptions: {e}")
        finally:
            try:
                con.close()
            except Exception:
                pass
    polar_coverage = ctx.get("polar_coverage") or []
    if polar_coverage:
        df_polar = pd.DataFrame(polar_coverage)
        if not df_polar.empty and "azimuth" in df_polar.columns and "max_distance" in df_polar.columns:
            fig = px.line_polar(
                df_polar,
                r="max_distance",
                theta="azimuth",
                line_close=True,
            )
            st.subheader("RF Polar Coverage")
            st.plotly_chart(fig)


