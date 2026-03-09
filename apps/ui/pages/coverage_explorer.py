from __future__ import annotations

import streamlit as st

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.metrics import metric_card
from ui import charts as ui_charts
from ui.map_engine import (
    build_aircraft_layer,
    build_blind_zone_layer,
    build_coverage_layer,
    build_deck_map,
    build_redundancy_layer,
    build_rf_link_dataframe,
    build_rf_link_layer,
    build_station_network_dataframe,
    build_station_network_layer,
    cap_links_per_station,
    compute_station_degree,
    build_station_layer,
)


@st.cache_data(show_spinner=False)
def compute_rf_engine(packets, station_lat, station_lon):
    engine = RFAnalysisEngine(packets, station_lat, station_lon)
    return engine.run()


def render_coverage_explorer_page(ctx):
    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)

    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")

    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"

    total_packets = len(packets_window) if packets_window is not None else 0
    total_rf = len(rf_packets) if rf_packets is not None else 0
    filtered_packets = total_rf if total_rf > 0 else total_packets

    if total_rf == 0:
        st.warning("No RF packets detected. Showing traffic map.")

    if packets_window is None:
        packets_window = ctx["pd"].DataFrame()
    if rf_packets is None:
        rf_packets = ctx["pd"].DataFrame()

    engine_all = RFAnalysisEngine(packets_window, ctx.get("station_lat"), ctx.get("station_lon"))
    dataset_mode_default = st.session_state.get("ce_dataset_mode", "STRICT_RF")
    dataset_mode = dataset_mode_default if dataset_mode_default in ("STRICT_RF", "STATION_RF", "NETWORK") else "STRICT_RF"
    dataset = engine_all.build_analysis_dataset(dataset_mode=dataset_mode)
    packets_all = dataset["packets_all"]
    packets_rf = dataset["packets_rf"]
    packets_filtered = dataset["packets_filtered"]
    radio_events = dataset["radio_events"]
    rf_grid = dataset["coverage_grid"]
    coverage_redundancy_grid = dataset.get("coverage_redundancy_grid")
    blind_cells = dataset.get("blind_cells")
    station_metrics = dataset["station_metrics"]
    network_metrics = dataset["network_metrics"]


    if "ce_active_station" not in st.session_state:
        st.session_state["ce_active_station"] = "(network)"
    if "ce_active_cell" not in st.session_state:
        st.session_state["ce_active_cell"] = None

    compare_default = st.session_state.get("ce_compare_stations")
    if compare_default is None:
        compare_default = ctx.get("os").getenv("OGN_COMPARE_STATIONS", "") if ctx.get("os") else ""

    st.markdown("### Network Configuration")
    dataset_mode_labels = {
        "STRICT_RF": "Local RF coverage",
        "STATION_RF": "Station coverage",
        "NETWORK": "Network coverage",
    }
    label_options = [dataset_mode_labels[k] for k in ("STRICT_RF", "STATION_RF", "NETWORK")]
    current_label = dataset_mode_labels.get(dataset_mode, "Local RF coverage")
    selected_label = st.selectbox(
        "Dataset mode",
        label_options,
        index=label_options.index(current_label),
    )
    inverse_labels = {v: k for k, v in dataset_mode_labels.items()}
    dataset_mode = inverse_labels.get(selected_label, "STRICT_RF")
    st.session_state["ce_dataset_mode"] = dataset_mode
    dataset = engine_all.build_analysis_dataset(
        dataset_mode=dataset_mode,
        station_id=st.session_state.get("ce_active_station") if dataset_mode == "STATION_RF" else None,
    )
    packets_all = dataset["packets_all"]
    packets_rf = dataset["packets_rf"]
    packets_filtered = dataset["packets_filtered"]
    radio_events = dataset["radio_events"]
    rf_grid = dataset["coverage_grid"]
    coverage_redundancy_grid = dataset.get("coverage_redundancy_grid")
    blind_cells = dataset.get("blind_cells")
    station_metrics = dataset["station_metrics"]
    network_metrics = dataset["network_metrics"]
    stations = dataset.get("stations", [])
    compare_str = st.text_input("Stations compared (callsign=lat,lon; ...)", value=compare_default)
    st.session_state["ce_compare_stations"] = compare_str

    compare_map = ctx.get("parse_compare_stations")(compare_str) if ctx.get("parse_compare_stations") else {}
    station_cs = ctx.get("station_callsign")
    if station_cs and station_cs not in compare_map:
        compare_map[station_cs] = (ctx.get("station_lat"), ctx.get("station_lon"))

    station_points = []
    for callsign, coords in compare_map.items():
        lat, lon = coords
        if lat is None or lon is None:
            continue
        packet_count = 0
        aircraft_seen = 0
        if not station_metrics.empty:
            row = station_metrics[station_metrics["igate"] == callsign]
            if not row.empty:
                packet_count = int(row["packet_count"].iloc[0])
                aircraft_seen = int(row["aircraft_count"].iloc[0])
        station_points.append(
            {
                "callsign": callsign,
                "lat": lat,
                "lon": lon,
                "packet_count": packet_count,
                "aircraft_seen": aircraft_seen,
            }
        )

    station_choices = ["(network)"] + [s["callsign"] for s in station_points] if station_points else ["(network)"]
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.selectbox("Station analyzed", station_choices, key="ce_active_station")
        st.caption(f"Time window: {ctx.get('hours', '—')} hours")
    with col_cfg2:
        rings_raw = ctx.get("rings_km", 40)
        if isinstance(rings_raw, (list, tuple)) and rings_raw:
            rings_default = int(rings_raw[0])
        else:
            rings_default = int(rings_raw) if rings_raw is not None else 40
        rings_km = st.slider("Analysis radius (km)", 5, 200, rings_default)
        st.caption("Basemap: " + str(ctx.get("basemap_label") or "Default"))

    active_station = st.session_state.get("ce_active_station", "(network)")
    if active_station != "(network)":
        station_meta = next((s for s in station_points if s["callsign"] == active_station), None)
        station_packets = RFAnalysisEngine.filter_packets_by_station(packets_rf, active_station)
        station_engine = compute_rf_engine(
            station_packets if station_packets is not None else packets_window,
            station_meta["lat"] if station_meta is not None else ctx.get("station_lat"),
            station_meta["lon"] if station_meta is not None else ctx.get("station_lon"),
        )
    else:
        station_meta = None
        station_engine = compute_rf_engine(packets_window, ctx.get("station_lat"), ctx.get("station_lon"))

    st.markdown("### MAP")
    analysis_mode = st.selectbox(
        "Analysis mode",
        ["RF propagation", "Network topology", "Coverage"],
        key="ce_analysis_mode",
    )
    presets = {
        "RF propagation": {
            "ce_show_stations": True,
            "ce_show_aircraft": True,
            "ce_show_coverage": False,
            "ce_show_redundancy": False,
            "ce_show_blind": False,
            "ce_show_links": True,
            "ce_show_station_network": False,
        },
        "Network topology": {
            "ce_show_stations": True,
            "ce_show_aircraft": False,
            "ce_show_coverage": False,
            "ce_show_redundancy": False,
            "ce_show_blind": False,
            "ce_show_links": False,
            "ce_show_station_network": True,
        },
        "Coverage": {
            "ce_show_stations": True,
            "ce_show_aircraft": False,
            "ce_show_coverage": True,
            "ce_show_redundancy": False,
            "ce_show_blind": True,
            "ce_show_links": False,
            "ce_show_station_network": False,
        },
    }
    if st.session_state.get("ce_last_preset") != analysis_mode:
        for key, value in presets[analysis_mode].items():
            st.session_state[key] = value
        st.session_state["ce_last_preset"] = analysis_mode

    with st.expander("Layer controls", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            show_stations = st.checkbox("Stations", True, key="ce_show_stations")
            show_aircraft = st.checkbox("Aircraft", True, key="ce_show_aircraft")
        with col2:
            show_coverage = st.checkbox("Coverage", True, key="ce_show_coverage")
            show_redundancy = st.checkbox("Redundancy", False, key="ce_show_redundancy")
        with col3:
            show_blind = st.checkbox("Blind zones", False, key="ce_show_blind")
            show_links = st.checkbox("RF links", False, key="ce_show_links")
            show_station_network = st.checkbox("Station network", False, key="ce_show_station_network")

        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            min_rssi = st.slider("Min RSSI", -120, -40, -90, key="ce_min_rssi")
        with colf2:
            max_links = st.slider("Max links", 100, 20000, 2000, key="ce_max_links")
        with colf3:
            max_distance = st.slider("Max distance (km)", 10, 400, 200, key="ce_max_distance")

        if show_station_network:
            coln1, coln2, coln3 = st.columns(3)
            with coln1:
                min_overlap = st.slider("Min overlap ratio", 0.0, 1.0, 0.4, 0.05, key="ce_min_overlap")
            with coln2:
                min_shared = st.slider("Min shared aircraft", 1, 50, 5, key="ce_min_shared")
            with coln3:
                max_station_links = st.slider("Max station links", 10, 500, 100, key="ce_max_station_links")
            max_links_per_station = st.slider(
                "Max links per station",
                1,
                50,
                8,
                key="ce_max_links_per_station",
            )

    stations_df = ctx["pd"].DataFrame(station_points) if station_points else ctx["pd"].DataFrame()
    if not stations_df.empty and "callsign" in stations_df.columns:
        stations_df = stations_df.rename(columns={"callsign": "station_id"})

    net_df_all = build_station_network_dataframe({**dataset, "stations_df": stations_df})
    degree_df = compute_station_degree(net_df_all) if net_df_all is not None else ctx["pd"].DataFrame()
    if not stations_df.empty and not degree_df.empty:
        stations_df = stations_df.merge(degree_df, on="station_id", how="left")
    elif not stations_df.empty and "network_degree" not in stations_df.columns:
        stations_df["network_degree"] = 0

    dataset_for_map = {
        **dataset,
        "stations_df": stations_df,
    }

    map_col, inspector_col = st.columns([0.7, 0.3])
    with map_col:
        layers = []
        if show_stations:
            layers.append(build_station_layer(dataset_for_map))
        if show_aircraft:
            layers.append(build_aircraft_layer(dataset_for_map))
        if show_coverage:
            layers.append(build_coverage_layer(dataset_for_map))
        if show_redundancy:
            layers.append(build_redundancy_layer(dataset_for_map))
        if show_blind:
            layers.append(build_blind_zone_layer(dataset_for_map))
        if show_links:
            links_df = build_rf_link_dataframe(dataset_for_map)
            if links_df is not None and not links_df.empty:
                links_df = links_df[links_df["rssi"].fillna(-999) >= min_rssi]
                links_df = links_df[links_df["distance_km"].fillna(0) <= max_distance]
                if len(links_df) > max_links:
                    links_df = links_df.sample(max_links)
            layers.append(build_rf_link_layer(dataset_for_map, links_df))
        if show_station_network:
            net_df = build_station_network_dataframe(dataset_for_map)
            if net_df is not None and not net_df.empty:
                net_df = net_df[
                    (net_df["overlap_ratio"] >= min_overlap)
                    & (net_df["shared_aircraft"] >= min_shared)
                ]
                net_df = cap_links_per_station(net_df, max_links_per_station)
                if len(net_df) > max_station_links:
                    net_df = net_df.nlargest(max_station_links, "overlap_ratio")
            layers.append(build_station_network_layer(dataset_for_map, net_df))
        deck = build_deck_map(
            layers,
            ctx.get("station_lat"),
            ctx.get("station_lon"),
        )
        st.pydeck_chart(deck, use_container_width=True)

    with inspector_col:
        st.markdown("### Station Inspector")
        station_ids = stations_df["station_id"].tolist() if not stations_df.empty else []
        if "selected_station" not in st.session_state:
            st.session_state["selected_station"] = station_ids[0] if station_ids else None
        selected_station = st.selectbox(
            "Select station",
            station_ids if station_ids else ["(none)"],
            index=0,
            key="selected_station",
        )
        if selected_station and selected_station != "(none)" and not station_metrics.empty:
            row = station_metrics[station_metrics["igate"] == selected_station]
            if not row.empty:
                st.write(f"Station: {selected_station}")
                st.write(f"Aircraft heard: {ctx['fmt_int'](row['aircraft_count'].iloc[0])}")
                st.write(f"Max distance: {ctx['fmt_float'](row['max_distance'].iloc[0], 1)}")
            if not degree_df.empty:
                deg_row = degree_df[degree_df["station_id"] == selected_station]
                if not deg_row.empty:
                    st.write(f"Network degree: {ctx['fmt_int'](deg_row['network_degree'].iloc[0])}")
            if net_df_all is not None and not net_df_all.empty:
                connections = net_df_all[
                    (net_df_all["station_a"] == selected_station)
                    | (net_df_all["station_b"] == selected_station)
                ]
                st.write(f"Overlap connections: {ctx['fmt_int'](len(connections))}")
        else:
            st.info("Select a station to inspect.")

    st.markdown("### Station Summary")
    max_dist = None
    p95_dist = None
    aircraft_seen = 0
    packet_count = 0
    if not station_metrics.empty and active_station != "(network)":
        row = station_metrics[station_metrics["igate"] == active_station]
        if not row.empty:
            packet_count = int(row["packet_count"].iloc[0])
            aircraft_seen = int(row["aircraft_count"].iloc[0])
            max_dist = row["max_distance"].iloc[0]
            p95_dist = row["p95_distance"].iloc[0]

    k1, k2, k3, k4 = st.columns(4)
    metric_card(k1, "RF packets", ctx["fmt_int"](packet_count))
    metric_card(k2, "Aircraft", ctx["fmt_int"](aircraft_seen))
    metric_card(k3, "Max distance", ctx["fmt_float"](max_dist, 1) if max_dist is not None else "—")
    metric_card(k4, "P95 distance", ctx["fmt_float"](p95_dist, 1) if p95_dist is not None else "—")

    st.markdown("### Network Contribution")
    if active_station == "(network)":
        st.info("Select a station to compute network contribution.")
    else:
        row = station_metrics[station_metrics["igate"] == active_station] if not station_metrics.empty else None
        if row is not None and not row.empty:
            st.write(f"Unique packets: {ctx['fmt_int'](row['unique_packets'].iloc[0])}")
            st.write(f"Shared packets: {ctx['fmt_int'](row['shared_packets'].iloc[0])}")
            st.write(f"Redundant packets: {ctx['fmt_int'](row['redundant_packets'].iloc[0])}")
            st.write(f"Unique coverage cells: {ctx['fmt_int'](row['coverage_cells'].iloc[0])}")
            st.write(f"Contribution score: {ctx['fmt_float'](row['contribution_score'].iloc[0], 1)}%")
        else:
            st.info("No station metrics available for this station.")

    st.markdown("### Zone Inspector")
    zone_radius = st.slider("Zone radius (km)", 1, 50, 5)
    if rf_grid is not None and not rf_grid.empty:
        grid_labels = rf_grid.dropna(subset=["lat", "lon"]).copy()
        if not grid_labels.empty:
            grid_labels["label"] = grid_labels.apply(lambda r: f"{r['lat']:.3f}, {r['lon']:.3f}", axis=1)
            label_options = ["(select)"] + grid_labels["label"].tolist()
            selected_label = st.selectbox("Zone cell", label_options, index=0)
            if selected_label != "(select)":
                st.session_state["ce_active_cell"] = selected_label
    zone_lat = None
    zone_lon = None
    if st.session_state.get("ce_active_cell") and rf_grid is not None and not rf_grid.empty:
        grid = rf_grid.dropna(subset=["lat", "lon"]).copy()
        grid["label"] = grid.apply(lambda r: f"{r['lat']:.3f}, {r['lon']:.3f}", axis=1)
        selected_cell = st.session_state.get("ce_active_cell")
        if selected_cell in grid["label"].values:
            cell = grid[grid["label"] == selected_cell].iloc[0]
            zone_lat = float(cell["lat"])
            zone_lon = float(cell["lon"])
    if zone_lat is None or zone_lon is None:
        st.info("Click a zone on the map to inspect.")
    else:
        zone_result = engine_all.inspect_zone(zone_lat, zone_lon, radius_km=zone_radius)
        st.write(f"Events: {ctx['fmt_int'](zone_result.get('events_count', 0))}")
        st.write(f"Stations hearing: {ctx['fmt_int'](len(zone_result.get('stations', [])))}")
        st.write(f"Redundancy mean: {ctx['fmt_float'](zone_result.get('redundancy_mean'), 2)}")
        st.write(f"Max distance: {ctx['fmt_float'](zone_result.get('max_distance_km'), 1)}")

    st.markdown("### Propagation")
    if station_engine.metrics.get("rf_packets", 0) < 200:
        st.info("Not enough RF packets for this analysis.")
    else:
        signal = station_engine.metrics.get("signal_distance") or {}
        if signal.get("implemented") and signal.get("data") is not None:
            data_plot = signal.get("data")
            binned = signal.get("binned_data")
            fig = ui_charts.plot_rssi_distance(data_plot, binned=binned)
            if fig is not None:
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)
        altitude = station_engine.metrics.get("altitude_distance") or {}
        if altitude.get("implemented") and altitude.get("data") is not None:
            data_plot = altitude.get("data")
            med = altitude.get("binned_data")
            fig = ui_charts.plot_altitude_distance(data_plot, med=med)
            if fig is not None:
                fig.update_layout(height=360)
                st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Directional RF")
    az = station_engine.azimuth_df
    if az is not None and not az.empty:
        fig = ui_charts.plot_polar_p95(az)
        if fig is not None:
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Terrain Impact")
    terrain = station_engine.metrics.get("terrain") or {}
    data = terrain.get("data")
    if data is not None and not data.empty and "azimuth_center_deg" in data.columns:
        st.line_chart(data, x="azimuth_center_deg", y="p95_distance_km", height=260)
