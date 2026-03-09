from __future__ import annotations

import streamlit as st

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.map_engine import (
    build_aircraft_layer,
    build_coverage_layer,
    build_deck_map,
    build_station_layer,
)


def render_coverage_explorer_page(ctx):
    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)

    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")

    rf_local_count = int(ctx.get("rf_local_count", 0))

    total_packets = len(packets_window) if packets_window is not None else 0
    total_rf = len(rf_packets) if rf_packets is not None else 0
    filtered_packets = total_rf if total_rf > 0 else total_packets

    if total_rf == 0:
        st.warning("No RF packets detected in selected time window. Showing traffic only.")
        st.warning("No packets for this station in APRS-IS dataset.")

    if packets_window is None:
        packets_window = ctx["pd"].DataFrame()
    if rf_packets is None:
        rf_packets = ctx["pd"].DataFrame()

    engine_all = RFAnalysisEngine(packets_window, ctx.get("station_lat"), ctx.get("station_lon"))
    dataset = engine_all.build_analysis_dataset()
    packets_all = dataset["packets_all"]
    packets_rf = dataset["packets_rf"]
    rf_grid = dataset["coverage_grid"]
    station_metrics = dataset["station_metrics"]

    if "selected_object" not in st.session_state:
        st.session_state["selected_object"] = None

    # Compact header
    hdr1, hdr2, hdr3 = st.columns([0.4, 0.3, 0.3])
    with hdr1:
        st.caption("Station")
        st.write(st.session_state.get("selected_station") or ctx.get("station_callsign") or "—")
    with hdr2:
        st.caption("Time window")
        st.write(f"{ctx.get('hours', '—')} h")
    with hdr3:
        st.caption("Dataset status")
        st.write(f"RF packets: {ctx['fmt_int'](rf_local_count)}")

    # Main layout: controls | map | inspector
    col_left, col_map, col_right = st.columns([0.22, 0.56, 0.22])

    with col_left:
        st.markdown("### Dataset")
        st.caption("Station")
        st.write(st.session_state.get("selected_station") or ctx.get("station_callsign") or "—")
        st.caption("Latitude / Longitude")
        st.write(f"{ctx.get('station_lat')} / {ctx.get('station_lon')}")
        st.caption("Time window")
        st.write(f"{ctx.get('hours', '—')} h")
        st.caption("Data source")
        st.write(ctx.get("data_source") or "—")
        st.caption("Aircraft types")
        types_str = "/".join(ctx.get("dst_types") or [])
        st.write(types_str if types_str else "—")

        st.markdown("### Map")
        st.caption(f"Basemap: {ctx.get('basemap_label') or 'Default'}")
        st.session_state.setdefault("ce_show_stations", True)
        st.session_state.setdefault("ce_show_aircraft", True)
        st.session_state.setdefault("ce_show_coverage", total_rf > 0)
        if total_rf == 0:
            st.session_state["ce_show_coverage"] = False
        show_stations = st.checkbox("Stations", key="ce_show_stations")
        show_aircraft = st.checkbox("Aircraft", key="ce_show_aircraft")
        show_coverage = st.checkbox(
            "Coverage grid",
            key="ce_show_coverage",
            disabled=total_rf == 0,
        )

    stations_df = ctx["pd"].DataFrame(
        [
            {
                "station_id": st.session_state.get("selected_station") or ctx.get("station_callsign") or "—",
                "lat": ctx.get("station_lat"),
                "lon": ctx.get("station_lon"),
                "network_degree": 0,
            }
        ]
    )

    dataset_for_map = {
        **dataset,
        "stations_df": stations_df,
    }

    with col_map:
        layers = []
        if show_stations:
            layers.append(build_station_layer(dataset_for_map))
        if show_aircraft:
            layers.append(build_aircraft_layer(dataset_for_map))
        if show_coverage and total_rf > 0:
            layers.append(build_coverage_layer(dataset_for_map))
        deck = build_deck_map(
            layers,
            ctx.get("station_lat"),
            ctx.get("station_lon"),
        )
        st.pydeck_chart(deck, use_container_width=True, height=750)

    with col_right:
        st.markdown("### Object Inspector")
        selected = st.session_state.get("selected_object")
        if not selected:
            st.info("Click an object on the map to inspect it.")
        else:
            st.write(selected)
