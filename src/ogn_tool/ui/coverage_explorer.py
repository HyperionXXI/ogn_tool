from __future__ import annotations

import streamlit as st

from apps.ui.map_engine import (
    build_aircraft_layer,
    build_coverage_layer,
    build_deck_map,
    build_station_layer,
)
from ogn_tool.ui.view_models.station_view import StationAnalysisView


def render_coverage_explorer_page(ctx):
    view = StationAnalysisView.from_context(ctx)

    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)

    if not view.has_rf:
        st.warning("No RF packets detected in selected time window. Showing traffic only.")
        st.warning("No packets for this station in APRS-IS dataset.")

    if "selected_object" not in st.session_state:
        st.session_state["selected_object"] = None

    hdr1, hdr2, hdr3 = st.columns([0.4, 0.3, 0.3])
    with hdr1:
        st.caption("Station")
        st.write(st.session_state.get("selected_station") or view.station_id or "—")
    with hdr2:
        st.caption("Time window")
        st.write(f"{view.hours if view.hours is not None else '—'} h")
    with hdr3:
        st.caption("Dataset status")
        st.write(f"RF packets: {ctx['fmt_int'](view.rf_local_count)}")

    col_left, col_map, col_right = st.columns([0.22, 0.56, 0.22])

    with col_left:
        st.markdown("### Dataset")
        st.caption("Station")
        st.write(st.session_state.get("selected_station") or view.station_id or "—")
        st.caption("Latitude / Longitude")
        st.write(f"{view.station_lat} / {view.station_lon}")
        st.caption("Time window")
        st.write(f"{view.hours if view.hours is not None else '—'} h")
        st.caption("Data source")
        st.write(view.data_source or "—")
        st.caption("Aircraft types")
        types_str = "/".join(view.dst_types)
        st.write(types_str if types_str else "—")

        st.markdown("### Map")
        st.caption(f"Basemap: {ctx.get('basemap_label') or 'Default'}")
        st.session_state.setdefault("ce_show_stations", True)
        st.session_state.setdefault("ce_show_aircraft", True)
        st.session_state.setdefault("ce_show_coverage", view.has_rf)
        if not view.has_rf:
            st.session_state["ce_show_coverage"] = False
        show_stations = st.checkbox("Stations", key="ce_show_stations")
        show_aircraft = st.checkbox("Aircraft", key="ce_show_aircraft")
        show_coverage = st.checkbox(
            "Coverage grid",
            key="ce_show_coverage",
            disabled=not view.has_rf,
        )

    stations_df = ctx["pd"].DataFrame(
        [
            {
                "station_id": st.session_state.get("selected_station") or view.station_id or "—",
                "lat": view.station_lat,
                "lon": view.station_lon,
                "network_degree": 0,
            }
        ]
    )

    dataset_for_map = {
        "packets_all": view.metrics.get("packets_all"),
        "packets_rf": view.metrics.get("packets_rf"),
        "coverage_grid": view.coverage,
        "station_metrics": view.metrics.get("station_metrics"),
        "stations_df": stations_df,
    }

    with col_map:
        layers = []
        if show_stations:
            layers.append(build_station_layer(dataset_for_map))
        if show_aircraft:
            layers.append(build_aircraft_layer(dataset_for_map))
        if show_coverage and view.has_rf:
            layers.append(build_coverage_layer(dataset_for_map))
        deck = build_deck_map(
            layers,
            view.station_lat,
            view.station_lon,
        )
        st.pydeck_chart(deck, use_container_width=True, height=750)

    with col_right:
        st.markdown("### Object Inspector")
        selected = st.session_state.get("selected_object")
        if not selected:
            st.info("Click an object on the map to inspect it.")
        else:
            st.write(selected)
