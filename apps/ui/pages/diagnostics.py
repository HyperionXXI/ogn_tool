from __future__ import annotations

import streamlit as st

from ui.layout import DASHBOARD_COLUMNS
from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.charts import render_rf_cartography
from ogn_tool.rf_probability_field import build_rf_probability_field


def render_diagnostics_page(ctx):
    st.subheader("Diagnostics")
    packets_window = ctx.get("packets_window")
    rf_packets = ctx.get("rf_packets")
    rf_local = ctx.get("rf_local")

    c1, c2, c3, c4, c5 = st.columns(DASHBOARD_COLUMNS)
    with c1:
        metric_card("Total packets", ctx["fmt_int"](len(packets_window) if packets_window is not None else 0))
    with c2:
        metric_card("RF packets", ctx["fmt_int"](len(rf_packets) if rf_packets is not None else 0))
    with c3:
        metric_card("RF local", ctx["fmt_int"](len(rf_local) if rf_local is not None else 0))
    with c4:
        st.empty()
    with c5:
        st.empty()

    with st.expander("Raw packets"):
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

    with st.expander("Debug diagnostics"):
        st.markdown("**Collector filter (APRS-IS)**")
        ogn_filter = (ctx.get("os").getenv("OGN_FILTER") if ctx.get("os") else "") or ""
        if ogn_filter:
            st.code(f"OGN_FILTER={ogn_filter}")
        else:
            st.warning("OGN_FILTER is empty. APRS-IS feed may be unfiltered (global traffic).")

        if packets_window is not None and "qas" in packets_window.columns:
            st.markdown("**SQL qAR / qAO count**")
            qas = packets_window["qas"].astype(str).str.upper()
            qar = int((qas == "QAR").sum())
            qao = int((qas == "QAO").sum())
            qac = int((qas == "QAC").sum())
            qas_srv = int((qas == "QAS").sum())
            st.write({"qAR": qar, "qAO": qao, "qAC": qac, "qAS": qas_srv})
            if "ts_epoch" in packets_window.columns and (qar + qao) > 0:
                ts = ctx["pd"].to_datetime(packets_window["ts_epoch"], unit="s", utc=True, errors="coerce")
                qas_mask = qas.isin(["QAR", "QAO"]) & ts.notna()
                if qas_mask.any():
                    per_hour = (
                        packets_window.loc[qas_mask]
                        .assign(_hour=ts[qas_mask].dt.floor("h"))
                        .groupby(["_hour", "qas"])
                        .size()
                        .unstack(fill_value=0)
                    )
                    st.subheader("RF qAR/qAO per hour")
                    st.line_chart(per_hour)
        else:
            st.info("No qas column available for SQL-style counts.")

        if rf_packets is None or rf_packets.empty:
            st.info("No RF-gated packets (qAR/qAO) in the current dataset.")
        else:
            rf_aircraft = rf_packets["src"].nunique() if "src" in rf_packets.columns else 0
            rf_samples = int(len(rf_packets))
            c6, c7, c8, c9, c10 = st.columns(DASHBOARD_COLUMNS)
            with c6:
                metric_card("RF packets", ctx["fmt_int"](rf_samples))
            with c7:
                metric_card("RF aircraft", ctx["fmt_int"](rf_aircraft))
            with c8:
                status = "RF dataset usable" if (rf_samples > 500 and rf_aircraft > 10) else "RF dataset insufficient"
                metric_card("RF dataset health", status)
            with c9:
                st.empty()
            with c10:
                st.empty()
            if "igate" in rf_packets.columns:
                st.subheader("RF packets by IGate (top 20)")
                st.bar_chart(rf_packets["igate"].value_counts().head(20))

    with st.expander("Station comparison"):
        db_path = ctx['db_path']
        filters_apply = ctx['filters_apply']
        station_callsign = ctx['station_callsign']
        station_lat = ctx['station_lat']
        station_lon = ctx['station_lon']
        dst_types = ctx['dst_types']
        limit_rows = ctx['limit_rows']
        compare_map = ctx['parse_compare_stations'](ctx['os'].getenv("OGN_COMPARE_STATIONS", ""))
        compare_map.setdefault(station_callsign, (station_lat, station_lon))
        packets_compare = ctx['_load_packets_window_raw'](
            db_path=db_path,
            since_iso=filters_apply["since_iso"],
            since_epoch=filters_apply["since_epoch"],
            dst_types=dst_types,
            station_callsign=station_callsign,
            only_heard_by=False,
            igate_filter="",
            source_mode="Heard-by station",
            qas_filter="",
            limit_rows=limit_rows,
        )
        result = ctx['analysis_station_compare'].analyze(
            packets_compare,
            station_coords=compare_map,
            station_callsigns=list(compare_map.keys()),
        )
        if not result.get("implemented"):
            summary = result.get("summary") or {}
            reason = summary.get("reason")
            if reason == "missing_station_config":
                st.info(
                    "Station comparison requires configuration.\n\n"
                    "Set environment variable:\n\n"
                    "OGN_COMPARE_STATIONS=CALLSIGN:lat,lon;CALLSIGN2:lat,lon"
                )
            elif reason == "fewer_than_two_stations":
                st.info("Station comparison requires at least 2 configured stations.")
            elif reason == "no_packets_for_configured_stations":
                st.info(
                    "Configured stations were found, but fewer than 2 have usable data in the selected time window."
                )
            elif reason == "invalid_station_coordinates":
                st.info("Some configured stations have missing or invalid coordinates.")
            else:
                st.info("Station comparison not implemented.")
            st.caption("Example: OGN_COMPARE_STATIONS=FK50887:47.3359,7.2728;STATION2:47.20,7.40")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c11, c12, c13, c14, c15 = st.columns(DASHBOARD_COLUMNS)
            with c11:
                metric_card("Station count", ctx['fmt_int'](summary.get("station_count")))
            with c12:
                metric_card("Best station", summary.get("best_station") or "—")
            with c13:
                val = summary.get("best_rank_score")
                metric_card("Best rank score", f"{ctx['fmt_float'](val, 2)}" if val is not None else "—")
            with c14:
                st.empty()
            with c15:
                st.empty()
            if data is not None and not data.empty:
                if "station_callsign" in data.columns and "rank_score" in data.columns:
                    st.bar_chart(data[["station_callsign", "rank_score"]].set_index("station_callsign"))
                cols = [
                    "station_callsign",
                    "rank_score",
                    "p95_distance_km",
                    "max_distance_km",
                    "packet_total",
                    "quality_score",
                    "health_status",
                ]
                st.dataframe(data[[c for c in cols if c in data.columns]], use_container_width=True, height=300)
