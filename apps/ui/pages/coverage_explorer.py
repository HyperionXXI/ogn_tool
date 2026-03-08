from __future__ import annotations

import streamlit as st

try:
    import folium
except Exception:  # pragma: no cover
    folium = None

try:
    from streamlit_folium import st_folium
except Exception:  # pragma: no cover
    st_folium = None

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.metrics import metric_card
from ui import charts as ui_charts


@st.cache_data(show_spinner=False)
def compute_rf_engine(packets, station_lat, station_lon):
    engine = RFAnalysisEngine(packets, station_lat, station_lon)
    return engine.run()


def _map_tiles(ctx: dict) -> str:
    label = str(ctx.get("basemap_label") or "")
    if "Positron" in label or "clair" in label:
        return "CartoDB positron"
    if "Dark" in label or "dark" in label:
        return "CartoDB dark_matter"
    return "OpenStreetMap"


def _build_grid_polygons(grid):
    cell_size_deg = float(grid["cell_size_deg"].iloc[0]) if "cell_size_deg" in grid.columns else 0.01
    df = grid.copy()
    df["polygon"] = df.apply(
        lambda r: [
            [r["lat"], r["lon"]],
            [r["lat"], r["lon"] + cell_size_deg],
            [r["lat"] + cell_size_deg, r["lon"] + cell_size_deg],
            [r["lat"] + cell_size_deg, r["lon"]],
        ],
        axis=1,
    )
    return df, cell_size_deg


def _bin_color(value, bins, colors, default="#9ca3af"):
    if value is None:
        return default
    for idx in range(len(bins) - 1):
        if bins[idx] <= value <= bins[idx + 1]:
            return colors[idx]
    return default


def _closest_station(lat, lon, station_points, max_km=5.0):
    if not station_points:
        return None
    max_deg = max_km / 111.0
    best = None
    best_d = None
    for s in station_points:
        d_lat = abs(lat - s["lat"])
        d_lon = abs(lon - s["lon"])
        if d_lat > max_deg or d_lon > max_deg:
            continue
        d = (d_lat * d_lat + d_lon * d_lon) ** 0.5
        if best_d is None or d < best_d:
            best_d = d
            best = s
    return best


def render_coverage_explorer_page(ctx):
    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)
    st.success("Coverage Explorer loaded")

    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")

    st.subheader("DEBUG MAP TEST")
    if folium is not None and st_folium is not None:
        test_map = folium.Map(location=[47.3, 7.3], zoom_start=8, tiles=_map_tiles(ctx))
        st_folium(test_map, height=500, use_container_width=True)
    else:
        st.warning("DEBUG MAP TEST unavailable: streamlit-folium not loaded.")

    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"

    total_packets = len(packets_window) if packets_window is not None else 0
    total_rf = len(rf_packets) if rf_packets is not None else 0
    filtered_packets = total_rf if total_rf > 0 else total_packets

    st.info(
        f"packets_total = {total_packets}\n"
        f"packets_rf = {total_rf}\n"
        f"packets_filtered = {filtered_packets}"
    )

    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if total_rf == 0:
        st.warning("No RF packets detected. Showing traffic map.")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

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

    st.markdown("### Dataset Debug Panel")
    st.write(f"Packets total: {ctx['fmt_int'](len(packets_all))}")
    st.write(f"Packets RF: {ctx['fmt_int'](len(packets_rf))}")
    st.write(f"Radio events: {ctx['fmt_int'](len(radio_events))}")
    st.write(f"Coverage cells: {ctx['fmt_int'](network_metrics.get('coverage_cells', 0))}")
    st.write(f"Stations: {ctx['fmt_int'](int(len(station_metrics)) if not station_metrics.empty else 0)}")
    st.write("Network metrics:")
    st.write(
        f"  stations={ctx['fmt_int'](network_metrics.get('station_count', 0))}, "
        f"coverage_cells={ctx['fmt_int'](network_metrics.get('coverage_cells', 0))}, "
        f"redundancy_cells={ctx['fmt_int'](network_metrics.get('redundancy_cells', 0))}, "
        f"blind_cells={ctx['fmt_int'](network_metrics.get('blind_cells', 0))}, "
        f"resilience_score={ctx['fmt_float'](network_metrics.get('network_resilience_score', 0.0), 1)}%"
    )

    if "ce_active_station" not in st.session_state:
        st.session_state["ce_active_station"] = "(network)"
    if "ce_active_cell" not in st.session_state:
        st.session_state["ce_active_cell"] = None

    compare_default = st.session_state.get("ce_compare_stations")
    if compare_default is None:
        compare_default = ctx.get("os").getenv("OGN_COMPARE_STATIONS", "") if ctx.get("os") else ""

    st.markdown("### Network Configuration")
    dataset_mode = st.selectbox(
        "Dataset mode",
        ["STRICT_RF", "STATION_RF", "NETWORK"],
        index=["STRICT_RF", "STATION_RF", "NETWORK"].index(dataset_mode),
    )
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
    show_traffic = st.checkbox("Traffic", value=True, key="ce_layer_traffic")
    show_reception = st.checkbox("Reception", value=True, key="ce_layer_reception")
    show_prob = st.checkbox("Coverage probability", value=True, key="ce_layer_prob")
    show_conf = st.checkbox("Confidence", value=True, key="ce_layer_conf")
    show_redundancy = st.checkbox("Redundancy", value=False, key="ce_layer_redundancy")
    show_blind = st.checkbox("Blind zones", value=False, key="ce_layer_blind")
    show_stations = st.checkbox("Stations", value=True, key="ce_layer_stations")
    show_rings = st.checkbox("Range rings", value=True, key="ce_layer_rings")

    if folium is None or st_folium is None:
        st.warning("Map rendering disabled: streamlit-folium not available.")
        map_data = {}
        grid_df = None
        cell_size = 0.01
    else:
        m = folium.Map(
            location=[ctx.get("station_lat"), ctx.get("station_lon")],
            zoom_start=8,
            tiles=_map_tiles(ctx),
            control_scale=True,
        )

        grid_df = None
        cell_size = 0.01
        if rf_grid is not None and not rf_grid.empty:
            grid = rf_grid.dropna(subset=["lat", "lon"])
            if not grid.empty:
                grid_df, cell_size = _build_grid_polygons(grid)
                grid_df["probability_val"] = ctx["pd"].to_numeric(grid_df.get("probability"), errors="coerce")
                grid_df["confidence_val"] = ctx["pd"].to_numeric(grid_df.get("confidence"), errors="coerce")
                grid_df["max_distance_val"] = ctx["pd"].to_numeric(grid_df.get("max_distance"), errors="coerce")

                if show_prob and "probability" in grid_df.columns:
                    prob_group = folium.FeatureGroup(name="Coverage probability", show=True)
                    for _, row in grid_df.iterrows():
                        color = _bin_color(
                            row.get("probability_val"),
                            [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                            ["#ef4444", "#f97316", "#f59e0b", "#3b82f6", "#9ca3af"],
                        )
                        folium.Polygon(
                            locations=row["polygon"],
                            color="#f8fafc",
                            weight=1,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.65,
                            tooltip=(
                                f"Coverage: {ctx['fmt_float'](row.get('probability_val'), 2)}<br/>"
                                f"Confidence: {ctx['fmt_float'](row.get('confidence_val'), 2)}"
                            ),
                        ).add_to(prob_group)
                    prob_group.add_to(m)

                if show_conf and "confidence" in grid_df.columns:
                    conf_group = folium.FeatureGroup(name="Confidence", show=True)
                    for _, row in grid_df.iterrows():
                        color = _bin_color(
                            row.get("confidence_val"),
                            [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                            ["#94a3b8", "#7dd3fc", "#60a5fa", "#2563eb", "#1e3a8a"],
                        )
                        folium.Polygon(
                            locations=row["polygon"],
                            color="#f8fafc",
                            weight=1,
                            fill=True,
                            fill_color=color,
                            fill_opacity=0.4,
                            tooltip=(
                                f"Confidence: {ctx['fmt_float'](row.get('confidence_val'), 2)}<br/>"
                                f"Max dist: {ctx['fmt_float'](row.get('max_distance_val'), 1)}"
                            ),
                        ).add_to(conf_group)
                    conf_group.add_to(m)

        if show_traffic:
            traffic_group = folium.FeatureGroup(name="Traffic", show=True)
            points = packets_all.dropna(subset=["lat", "lon"]) if packets_all is not None else None
            if points is not None and not points.empty:
                for _, row in points.iterrows():
                    folium.CircleMarker(
                        location=[row["lat"], row["lon"]],
                        radius=6,
                        color="#f97316",
                        fill=True,
                        fill_opacity=0.75,
                        weight=0,
                    ).add_to(traffic_group)
            traffic_group.add_to(m)

        if show_reception:
            reception_group = folium.FeatureGroup(name="Reception", show=True)
            reception_points = packets_rf if packets_rf is not None and not packets_rf.empty else None
            if station_meta is not None and packets_window is not None and "igate" in packets_window.columns:
                reception_points = packets_window[packets_window["igate"].astype(str) == active_station]
            if reception_points is not None and not reception_points.empty:
                points = reception_points.dropna(subset=["lat", "lon"])
                for _, row in points.iterrows():
                    folium.CircleMarker(
                        location=[row["lat"], row["lon"]],
                        radius=7,
                        color="#22c55e",
                        fill=True,
                        fill_opacity=0.85,
                        weight=0,
                    ).add_to(reception_group)
            reception_group.add_to(m)

        if show_redundancy and coverage_redundancy_grid is not None and not coverage_redundancy_grid.empty:
            red_group = folium.FeatureGroup(name="Redundancy", show=True)
            for _, row in coverage_redundancy_grid.iterrows():
                count = int(row.get("station_count", 0))
                if count <= 0:
                    color = "#111827"
                elif count == 1:
                    color = "#ef4444"
                elif count == 2:
                    color = "#f97316"
                elif count == 3:
                    color = "#facc15"
                else:
                    color = "#22c55e"
                folium.CircleMarker(
                    location=[row["lat_cell"], row["lon_cell"]],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    weight=0,
                    tooltip=f"Stations: {count}",
                ).add_to(red_group)
            red_group.add_to(m)

        if show_blind and blind_cells is not None and not blind_cells.empty:
            blind_group = folium.FeatureGroup(name="Blind zones", show=True)
            for _, row in blind_cells.iterrows():
                count = int(row.get("station_count", 0))
                color = "#ef4444" if count == 1 else "#111827"
                folium.CircleMarker(
                    location=[row["lat_cell"], row["lon_cell"]],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_opacity=0.7,
                    weight=0,
                    tooltip=f"Stations: {count}",
                ).add_to(blind_group)
            blind_group.add_to(m)

        if show_stations and station_points:
            station_group = folium.FeatureGroup(name="Stations", show=True)
            for s in station_points:
                tooltip = f"{s['callsign']}<br/>Packets: {s['packet_count']}<br/>Aircraft: {s['aircraft_seen']}"
                folium.Marker(
                    location=[s["lat"], s["lon"]],
                    tooltip=tooltip,
                    icon=folium.Icon(color="blue", icon="signal", prefix="fa"),
                ).add_to(station_group)
            station_group.add_to(m)

        if station_meta:
            folium.CircleMarker(
                location=[station_meta["lat"], station_meta["lon"]],
                radius=9,
                color="#0ea5e9",
                fill=True,
                fill_opacity=0.95,
                weight=2,
            ).add_to(m)

        if show_rings and station_meta:
            rings_group = folium.FeatureGroup(name="Range rings", show=True)
            for r_km in (10, 20, 40, rings_km):
                folium.Circle(
                    location=[station_meta["lat"], station_meta["lon"]],
                    radius=r_km * 1000,
                    color="#2563eb",
                    fill=False,
                    weight=1,
                ).add_to(rings_group)
            rings_group.add_to(m)

        folium.LayerControl().add_to(m)
        map_data = st_folium(m, height=700, use_container_width=True)

    clicked = map_data.get("last_clicked") if isinstance(map_data, dict) else None
    if clicked:
        click_lat = clicked.get("lat")
        click_lon = clicked.get("lng")
        updated = False
        if click_lat is not None and click_lon is not None:
            station_hit = _closest_station(click_lat, click_lon, station_points)
            if station_hit is not None and station_hit["callsign"] != st.session_state.get("ce_active_station"):
                st.session_state["ce_active_station"] = station_hit["callsign"]
                updated = True
            elif grid_df is not None and not grid_df.empty:
                mask = (
                    (grid_df["lat"] <= click_lat)
                    & (grid_df["lat"] + cell_size > click_lat)
                    & (grid_df["lon"] <= click_lon)
                    & (grid_df["lon"] + cell_size > click_lon)
                )
                if mask.any():
                    cell = grid_df[mask].iloc[0]
                    label = f"{cell['lat']:.3f}, {cell['lon']:.3f}"
                    if label != st.session_state.get("ce_active_cell"):
                        st.session_state["ce_active_cell"] = label
                        updated = True
            if updated:
                st.rerun()

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
    zone_info = None
    if rf_grid is not None and not rf_grid.empty:
        grid = rf_grid.dropna(subset=["lat", "lon"]).copy()
        grid["label"] = grid.apply(lambda r: f"{r['lat']:.3f}, {r['lon']:.3f}", axis=1)
        default_cell = st.session_state.get("ce_active_cell")
        if default_cell not in grid["label"].values:
            default_cell = grid["label"].iloc[0]
        st.selectbox(
            "Select grid cell",
            grid["label"],
            key="ce_active_cell",
            index=int(grid["label"].tolist().index(default_cell)),
        )
        selected_cell = st.session_state.get("ce_active_cell")
        if selected_cell in grid["label"].values:
            cell = grid[grid["label"] == selected_cell].iloc[0]
            cell_size = float(grid["cell_size_deg"].iloc[0]) if "cell_size_deg" in grid.columns else 0.01
            zone_info = cell.to_dict()
            zone_info["mean_altitude"] = zone_info.get("mean_altitude")
            zone_info["max_distance"] = zone_info.get("max_distance")
    if zone_info is None:
        st.info("No dataset available")
    else:
        st.write(f"Packet density: {ctx['fmt_int'](zone_info.get('packets'))}")
        st.write(f"Dataset confidence: {ctx['fmt_float'](zone_info.get('confidence'), 2)}")
        st.write(f"Mean aircraft altitude: {ctx['fmt_float'](zone_info.get('mean_altitude'), 0)}")
        st.write(f"Max reception distance: {ctx['fmt_float'](zone_info.get('max_distance'), 1)}")

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
