import datetime as dt
from typing import Dict, Any

import streamlit as st


AIRCRAFT_TYPES = ["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"]

def render_sidebar_filters(default_filters: Dict[str, Any], now_utc_fn, has_rf: bool = True) -> Dict[str, Any]:
    if "filters_apply" not in st.session_state:
        st.session_state["filters_apply"] = default_filters.copy()
    if "filters_edit" not in st.session_state:
        st.session_state["filters_edit"] = st.session_state["filters_apply"].copy()
    if "last_apply_ts" not in st.session_state:
        st.session_state["last_apply_ts"] = now_utc_fn()

    with st.sidebar:
        with st.form("filters_form"):
            st.markdown("## Station")
            station_callsign = st.text_input("Callsign", st.session_state["filters_edit"]["station_callsign"])
            db_path = st.text_input("DB path", st.session_state["filters_edit"]["db_path"])
            station_lat = st.number_input("Latitude", value=float(st.session_state["filters_edit"]["station_lat"]), format="%.6f")
            station_lon = st.number_input("Longitude", value=float(st.session_state["filters_edit"]["station_lon"]), format="%.6f")

            st.markdown("## Time window")
            hours = st.slider("Time window (hours)", 1, 72, int(st.session_state["filters_edit"]["hours"]))

            st.markdown("## Data source")
            data_source = st.selectbox(
                "Data source mode",
                ["APRS-IS gated", "Receiver-only RF", "FANET local", "OGN live tracking"],
                index=["APRS-IS gated", "Receiver-only RF", "FANET local", "OGN live tracking"].index(
                    st.session_state["filters_edit"].get("data_source", "APRS-IS gated")
                ),
            )

            st.markdown("## Aircraft types")
            st.multiselect(
                "Aircraft types",
                AIRCRAFT_TYPES,
                disabled=True,
            )

            st.caption("Filters are applied only when clicking 'Apply filters'.")
            apply_button = st.form_submit_button("Apply filters")

        if apply_button:
            # Preserve advanced filters from existing state
            source_mode = st.session_state["filters_edit"]["source_mode"]
            only_heard_by = bool(st.session_state["filters_edit"]["only_heard_by"])
            only_local_radio = bool(st.session_state["filters_edit"]["only_local_radio"])
            igate_filter = st.session_state["filters_edit"]["igate_filter"]
            use_cov_grid = bool(st.session_state["filters_edit"].get("use_cov_grid", True))
            st.session_state["filters_edit"] = {
                **st.session_state["filters_edit"],
                "db_path": db_path,
                "station_callsign": station_callsign,
                "station_lat": float(station_lat),
                "station_lon": float(station_lon),
                "hours": int(hours),
                "data_source": data_source,
                "source_mode": source_mode,
                "dst_types": list(AIRCRAFT_TYPES),
                "only_local_radio": bool(only_local_radio),
                "only_heard_by": bool(only_heard_by),
                "igate_filter": igate_filter,
                "use_cov_grid": bool(use_cov_grid),
            }

            applied = st.session_state["filters_edit"].copy()
            if applied["only_local_radio"]:
                applied["source_mode"] = "Radio station view"
                if not applied.get("igate_filter"):
                    applied["igate_filter"] = applied["station_callsign"]
                applied["qas_filter"] = "qA*"
            else:
                applied["qas_filter"] = ""
            since_dt = now_utc_fn() - dt.timedelta(hours=int(applied["hours"]))
            applied["since_iso"] = since_dt.isoformat().replace("+00:00", "+00:00")
            applied["since_epoch"] = int(since_dt.timestamp())
            st.session_state["filters_apply"] = applied
            st.session_state["last_apply_ts"] = now_utc_fn()

    filters_apply = st.session_state["filters_apply"]
    if filters_apply["do_autorefresh"]:
        filters_apply = filters_apply.copy()
        since_dt = now_utc_fn() - dt.timedelta(hours=int(filters_apply["hours"]))
        filters_apply["since_iso"] = since_dt.isoformat().replace("+00:00", "+00:00")
        filters_apply["since_epoch"] = int(since_dt.timestamp())
    return filters_apply
