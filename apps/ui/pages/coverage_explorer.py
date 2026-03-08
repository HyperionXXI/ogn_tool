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


def _compute_station_points(ctx, packets_window, compare_str: str):
    station_points = []
    compare_map = ctx.get("parse_compare_stations")(compare_str) if ctx.get("parse_compare_stations") else {}
    station_cs = ctx.get("station_callsign")
    if station_cs and station_cs not in compare_map:
        compare_map[station_cs] = (ctx.get("station_lat"), ctx.get("station_lon"))

    if packets_window is not None and "igate" in packets_window.columns:
        igate_counts = packets_window.groupby("igate").size()
        igate_aircraft = (
            packets_window.groupby("igate")["src"].nunique() if "src" in packets_window.columns else None
        )
    else:
        igate_counts = ctx["pd"].Series(dtype=int)
        igate_aircraft = None

    for callsign, coords in compare_map.items():
        lat, lon = coords
        if lat is None or lon is None:
            continue
        station_points.append(
            {
                "callsign": callsign,
                "lat": lat,
                "lon": lon,
                "packet_count": int(igate_counts.get(callsign, 0)),
                "aircraft_seen": int(igate_aircraft.get(callsign, 0)) if igate_aircraft is not None else 0,
            }
        )

    return station_points


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


def _compute_network_contribution(packets_window, station_callsign, station_engine):
    if packets_window is None or packets_window.empty or "igate" not in packets_window.columns:
        return {
            "unique_packets": 0,
            "shared_packets": 0,
            "redundant_packets": 0,
            "unique_cells": 0,
            "contribution_score": 0.0,
        }
    station_packets = packets_window[packets_window["igate"].astype(str) == station_callsign]
    if station_packets.empty or "src" not in station_packets.columns:
        return {
            "unique_packets": 0,
            "shared_packets": 0,
            "redundant_packets": 0,
            "unique_cells": 0,
            "contribution_score": 0.0,
        }

    src_igates = packets_window.groupby("src")["igate"].nunique() if "src" in packets_window.columns else None
    if src_igates is None:
        unique_packets = 0
        shared_packets = 0
    else:
        unique_src = src_igates[src_igates == 1].index
        shared_src = src_igates[src_igates > 1].index
        unique_packets = int(station_packets[station_packets["src"].isin(unique_src)].shape[0])
        shared_packets = int(station_packets[station_packets["src"].isin(shared_src)].shape[0])

    redundant_packets = shared_packets
    total_packets = int(station_packets.shape[0])
    contribution_score = (unique_packets / total_packets * 100.0) if total_packets else 0.0

    unique_cells = 0
    if station_engine is not None and station_engine.coverage_grid is not None:
        grid = station_engine.coverage_grid
        if not grid.empty and "packets" in grid.columns:
            unique_cells = int((grid["packets"] > 0).sum())

    return {
        "unique_packets": unique_packets,
        "shared_packets": shared_packets,
        "redundant_packets": redundant_packets,
        "unique_cells": unique_cells,
        "contribution_score": contribution_score,
    }


def render_coverage_explorer_page(ctx):
    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)
    st.success("Coverage Explorer loaded")

    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")

    if folium is None or st_folium is None:
        st.error("Missing dependency: streamlit-folium. Install: pip install streamlit-folium")
        return

    st.subheader("DEBUG MAP TEST")
    test_map = folium.Map(location=[47.3, 7.3], zoom_start=8, tiles=_map_tiles(ctx))
    st_folium(test_map, height=500, use_container_width=True)

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
    analysis_data = engine_all.build_analysis_dataset()
    packets_all = analysis_data["packets_all"]
    packets_rf = analysis_data["packets_rf"]
    packets_filtered = analysis_data["packets_filtered"]
    rf_grid = analysis_data["coverage_grid"]

    if "ce_active_station" not in st.session_state:
        st.session_state["ce_active_station"] = "(network)"
    if "ce_active_cell" not in st.session_state:
        st.session_state["ce_active_cell"] = None

    st.markdown("### MAP")
    show_traffic = st.checkbox("Traffic", value=True, key="ce_layer_traffic")
    show_reception = st.checkbox("Reception", value=True, key="ce_layer_reception")
    show_prob = st.checkbox("Coverage probability", value=True, key="ce_layer_prob")
    show_conf = st.checkbox("Confidence", value=True, key="ce_layer_conf")
    show_stations = st.checkbox("Stations", value=True, key="ce_layer_stations")
    show_rings = st.checkbox("Range rings", value=True, key="ce_layer_rings")

    compare_default = st.session_state.get("ce_compare_stations")
    if compare_default is None:
        compare_default = ctx.get("os").getenv("OGN_COMPARE_STATIONS", "") if ctx.get("os") else ""

    station_points = _compute_station_points(ctx, packets_window, compare_default)
    station_choices = ["(network)"] + [s["callsign"] for s in station_points] if station_points else ["(network)"]
    active_station = st.session_state.get("ce_active_station", "(network)")

    if active_station != "(network)":
        station_meta = next((s for s in station_points if s["callsign"] == active_station), None)
        station_packets = (
            packets_window[packets_window["igate"].astype(str) == active_station]
            if packets_window is not None and "igate" in packets_window.columns
            else ctx["pd"].DataFrame()
        )
        if station_meta and (station_packets is not None and not station_packets.empty):
            station_engine = compute_rf_engine(station_packets, station_meta["lat"], station_meta["lon"])
        else:
            station_engine = compute_rf_engine(packets_window, ctx.get("station_lat"), ctx.get("station_lon"))
    else:
        station_meta = None
        station_engine = compute_rf_engine(packets_window, ctx.get("station_lat"), ctx.get("station_lon"))

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
        for r_km in (10, 20, 40):
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

    st.markdown("### Network Configuration")
    compare_str = st.text_input("Stations compared (callsign=lat,lon; ...)", value=compare_default)
    st.session_state["ce_compare_stations"] = compare_str

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        st.selectbox("Station analyzed", station_choices, key="ce_active_station")
        st.caption(f"Time window: {ctx.get('hours', '—')} hours")
    with col_cfg2:
        rings_km = st.slider("Analysis radius (km)", 5, 200, int(ctx.get("rings_km", 40)))
        st.caption("Basemap: " + str(ctx.get("basemap_label") or "Default"))

    st.markdown("### Station Summary")
    range_summary = (station_engine.metrics.get("station_range") or {}).get("summary") or {}
    max_dist = range_summary.get("max_distance_km")
    p95_dist = range_summary.get("p95_distance_km")
    aircraft_seen = None
    if active_station != "(network)" and station_meta is not None:
        aircraft_seen = station_meta.get("aircraft_seen")
    elif rf_packets is not None and "src" in rf_packets.columns:
        aircraft_seen = rf_packets["src"].nunique()

    k1, k2, k3, k4 = st.columns(4)
    metric_card(k1, "RF packets", ctx["fmt_int"](station_engine.metrics.get("rf_packets", 0)))
    metric_card(k2, "Aircraft", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
    metric_card(k3, "Max distance", ctx["fmt_float"](max_dist, 1) if max_dist is not None else "—")
    metric_card(k4, "P95 distance", ctx["fmt_float"](p95_dist, 1) if p95_dist is not None else "—")

    st.markdown("### Network Contribution")
    if active_station == "(network)":
        st.info("Select a station to compute network contribution.")
    else:
        contribution = _compute_network_contribution(packets_window, active_station, station_engine)
        st.write(f"Unique packets: {ctx['fmt_int'](contribution['unique_packets'])}")
        st.write(f"Shared packets: {ctx['fmt_int'](contribution['shared_packets'])}")
        st.write(f"Redundant packets: {ctx['fmt_int'](contribution['redundant_packets'])}")
        st.write(f"Unique coverage cells: {ctx['fmt_int'](contribution['unique_cells'])}")
        st.write(f"Contribution score: {ctx['fmt_float'](contribution['contribution_score'], 1)}%")

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
            if packets_filtered is not None and "lat" in packets_filtered.columns and "lon" in packets_filtered.columns:
                lat_min, lat_max = cell["lat"], cell["lat"] + cell_size
                lon_min, lon_max = cell["lon"], cell["lon"] + cell_size
                subset = packets_filtered[
                    (packets_filtered["lat"] >= lat_min)
                    & (packets_filtered["lat"] < lat_max)
                    & (packets_filtered["lon"] >= lon_min)
                    & (packets_filtered["lon"] < lon_max)
                ]
                zone_info["mean_altitude"] = subset["altitude_m"].mean() if "altitude_m" in subset.columns else None
                zone_info["max_distance"] = subset["distance_km"].max() if "distance_km" in subset.columns else None
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
