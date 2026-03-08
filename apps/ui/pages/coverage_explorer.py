from __future__ import annotations

import streamlit as st

try:
    import pydeck as pdk
except Exception:  # pragma: no cover
    pdk = None

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.metrics import metric_card
from ui import charts as ui_charts


@st.cache_data(show_spinner=False)
def compute_rf_engine(packets, station_lat, station_lon):
    engine = RFAnalysisEngine(packets, station_lat, station_lon)
    return engine.run()


def _map_style(ctx: dict):
    if pdk is None:
        return None
    label = str(ctx.get("basemap_label") or "")
    if "Positron" in label or "clair" in label:
        return pdk.map_styles.CARTO_LIGHT
    if "Dark" in label or "dark" in label:
        return pdk.map_styles.CARTO_DARK
    return pdk.map_styles.ROAD


def _build_grid_polygons(grid):
    cell_size_deg = float(grid["cell_size_deg"].iloc[0]) if "cell_size_deg" in grid.columns else 0.01
    df = grid.copy()
    df["polygon"] = df.apply(
        lambda r: [
            [r["lon"], r["lat"]],
            [r["lon"] + cell_size_deg, r["lat"]],
            [r["lon"] + cell_size_deg, r["lat"] + cell_size_deg],
            [r["lon"], r["lat"] + cell_size_deg],
        ],
        axis=1,
    )
    return df, cell_size_deg


def _compute_station_points(ctx, packets_window):
    station_points = []
    compare_map = (
        ctx.get("parse_compare_stations")(ctx.get("os").getenv("OGN_COMPARE_STATIONS", ""))
        if ctx.get("parse_compare_stations")
        else {}
    )
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


def render_coverage_explorer_page(ctx):
    st.markdown("<h2>Coverage Explorer</h2>", unsafe_allow_html=True)

    rf_packets = ctx.get("rf_packets")
    packets_window = ctx.get("packets_window")
    dataset = rf_packets if rf_packets is not None and not rf_packets.empty else packets_window

    rf_local_count = int(ctx.get("rf_local_count", 0))
    readiness = "GOOD" if rf_local_count >= 2000 else "FAIR" if rf_local_count >= 500 else "LOW"

    st.markdown("**RF DATASET STATUS**")
    st.write(f"Packets heard by station: {ctx['fmt_int'](rf_local_count)}")
    st.write("Recommended minimum: 2000")
    st.write(f"Coverage readiness: {readiness}")
    if rf_local_count < 2000:
        st.warning("Dataset too small for reliable RF coverage analysis")

    if dataset is None or (hasattr(dataset, "empty") and dataset.empty):
        st.info("No packets available for coverage explorer.")
        return

    engine_result = compute_rf_engine(dataset, ctx.get("station_lat"), ctx.get("station_lon"))
    rf_grid = engine_result.coverage_grid

    station_points = _compute_station_points(ctx, packets_window)
    station_choices = ["(network)"] + [s["callsign"] for s in station_points] if station_points else ["(network)"]

    st.markdown("**Active station**")
    active_station = st.selectbox("Select a station", station_choices, index=0)

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
            station_engine = engine_result
    else:
        station_meta = None
        station_engine = engine_result

    left, right = st.columns([7, 3])

    with left:
        st.markdown("**Map layers**")
        show_prob = st.checkbox("Probability field", value=True, key="ce_show_prob")
        show_conf = st.checkbox("Confidence grid", value=True, key="ce_show_conf")
        show_points = st.checkbox("Raw packets", value=False, key="ce_show_points")
        show_stations = st.checkbox("Station markers", value=True, key="ce_show_stations")
        show_rings = st.checkbox("Range rings", value=True, key="ce_show_rings")
        st.caption("Tip: use the station selector and grid cell selector to drive the analysis panels.")

        if pdk is None:
            st.error("Missing dependency: pydeck. Install: pip install pydeck")
        else:
            deck_layers = []
            grid_df = None
            if rf_grid is not None and not rf_grid.empty:
                grid = rf_grid.dropna(subset=["lat", "lon"])
                if not grid.empty:
                    grid_df, cell_size = _build_grid_polygons(grid)
                    grid_df["probability_val"] = ctx["pd"].to_numeric(grid_df.get("probability"), errors="coerce")
                    grid_df["confidence_val"] = ctx["pd"].to_numeric(grid_df.get("confidence"), errors="coerce")
                    grid_df["max_distance_val"] = ctx["pd"].to_numeric(grid_df.get("max_distance"), errors="coerce")

                    if show_prob and "probability" in grid_df.columns:
                        prob_colors = [
                            [220, 38, 38, 110],
                            [249, 115, 22, 120],
                            [234, 179, 8, 130],
                            [132, 204, 22, 140],
                            [34, 197, 94, 150],
                        ]
                        probs = ctx["pd"].cut(
                            grid_df["probability_val"].fillna(0.0),
                            bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                            include_lowest=True,
                            right=True,
                        )
                        grid_df["probability_color"] = [
                            prob_colors[i] if i is not None else [153, 153, 153, 80]
                            for i in probs.cat.codes
                        ]
                        deck_layers.append(
                            pdk.Layer(
                                "PolygonLayer",
                                data=grid_df,
                                get_polygon="polygon",
                                get_fill_color="probability_color",
                                get_line_color=[255, 255, 255, 30],
                                line_width_min_pixels=1,
                                stroked=True,
                                filled=True,
                                opacity=0.7,
                                pickable=True,
                            )
                        )

                    if show_conf and "confidence" in grid_df.columns:
                        conf_colors = [
                            [148, 163, 184, 90],
                            [125, 211, 252, 100],
                            [59, 130, 246, 110],
                            [37, 99, 235, 120],
                            [30, 64, 175, 130],
                        ]
                        conf_bins = ctx["pd"].cut(
                            grid_df["confidence_val"].fillna(0.0),
                            bins=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
                            include_lowest=True,
                            right=True,
                        )
                        grid_df["confidence_color"] = [
                            conf_colors[i] if i is not None else [153, 153, 153, 80]
                            for i in conf_bins.cat.codes
                        ]
                        deck_layers.append(
                            pdk.Layer(
                                "PolygonLayer",
                                data=grid_df,
                                get_polygon="polygon",
                                get_fill_color="confidence_color",
                                get_line_color=[255, 255, 255, 30],
                                line_width_min_pixels=1,
                                stroked=True,
                                filled=True,
                                opacity=0.7,
                                pickable=True,
                            )
                        )

            if show_points:
                points = dataset.dropna(subset=["lat", "lon"]).copy()
                if not points.empty:
                    deck_layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=points,
                            get_position=["lon", "lat"],
                            get_radius=200,
                            get_fill_color=[255, 80, 0, 120],
                            pickable=True,
                        )
                    )

            if show_stations and station_points:
                deck_layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=station_points,
                        get_position=["lon", "lat"],
                        get_radius=450,
                        get_fill_color=[37, 99, 235, 200],
                        pickable=True,
                    )
                )
                if station_meta:
                    deck_layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=[station_meta],
                            get_position=["lon", "lat"],
                            get_radius=650,
                            get_fill_color=[14, 116, 144, 220],
                            pickable=False,
                        )
                    )

            if show_rings and station_meta:
                for r_km in (10, 20, 40):
                    deck_layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=[station_meta],
                            get_position=["lon", "lat"],
                            get_radius=r_km * 1000,
                            get_fill_color=[0, 0, 0, 0],
                            get_line_color=[37, 99, 235, 120],
                            line_width_min_pixels=1,
                            stroked=True,
                            filled=False,
                        )
                    )

            view = pdk.ViewState(
                latitude=ctx.get("station_lat"),
                longitude=ctx.get("station_lon"),
                zoom=8,
                pitch=35,
            )
            tooltip = {
                "html": "<b>{callsign}</b><br/>Packets: {packet_count}<br/>Aircraft: {aircraft_seen}"
                "<br/>Prob: {probability_val}<br/>Conf: {confidence_val}<br/>Max dist: {max_distance_val}",
                "style": {"backgroundColor": "white", "color": "black"},
            }
            deck = pdk.Deck(layers=deck_layers, initial_view_state=view, map_style=_map_style(ctx), tooltip=tooltip)
            st.pydeck_chart(deck, use_container_width=True, height=660)

    with right:
        st.markdown("**Station Health**")
        range_summary = (station_engine.metrics.get("station_range") or {}).get("summary") or {}
        max_dist = range_summary.get("max_distance_km")
        p95_dist = range_summary.get("p95_distance_km")
        aircraft_seen = None
        if active_station != "(network)" and station_meta is not None:
            aircraft_seen = station_meta.get("aircraft_seen")
        elif rf_packets is not None and "src" in rf_packets.columns:
            aircraft_seen = rf_packets["src"].nunique()

        c1, c2 = st.columns(2)
        metric_card(c1, "RF packets", ctx["fmt_int"](station_engine.metrics.get("rf_packets", 0)))
        metric_card(c2, "Aircraft", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
        metric_card(c1, "Max distance", ctx["fmt_float"](max_dist, 1) if max_dist is not None else "—")
        metric_card(c2, "P95 distance", ctx["fmt_float"](p95_dist, 1) if p95_dist is not None else "—")

        st.markdown("**Directional RF**")
        anisotropy = None
        if station_engine.azimuth_df is not None and not station_engine.azimuth_df.empty:
            p95 = ctx["pd"].to_numeric(station_engine.azimuth_df.get("p95_distance_km"), errors="coerce")
            if p95.notna().any():
                mean_val = float(p95.mean())
                std_val = float(p95.std())
                anisotropy = std_val / mean_val if mean_val else None
        metric_card(c1, "RF health score", ctx["fmt_float"](station_engine.metrics.get("health"), 0) if station_engine.metrics.get("health") is not None else "—")
        metric_card(c2, "Anisotropy", ctx["fmt_float"](anisotropy, 2) if anisotropy is not None else "—")

        terrain_flag = (station_engine.metrics.get("terrain") or {}).get("summary", {}).get("terrain_mask_suspected")
        confidence = (
            "GOOD"
            if station_engine.metrics.get("rf_packets", 0) >= 2000
            else "FAIR"
            if station_engine.metrics.get("rf_packets", 0) >= 500
            else "LOW"
        )
        metric_card(c1, "Terrain shadow", "yes" if terrain_flag else "no" if terrain_flag is not None else "N/A")
        metric_card(c2, "Dataset confidence", confidence)

    st.markdown("---")
    zone_col, station_col = st.columns([1, 1])

    with zone_col:
        st.markdown("**Zone Inspector**")
        zone_info = None
        if rf_grid is not None and not rf_grid.empty:
            grid = rf_grid.dropna(subset=["lat", "lon"]).copy()
            grid["label"] = grid.apply(lambda r: f"{r['lat']:.3f}, {r['lon']:.3f}", axis=1)
            selected_cell = st.selectbox("Select grid cell", grid["label"], key="ce_zone")
            if selected_cell in grid["label"].values:
                cell = grid[grid["label"] == selected_cell].iloc[0]
                cell_size = float(grid["cell_size_deg"].iloc[0]) if "cell_size_deg" in grid.columns else 0.01
                zone_info = cell.to_dict()
                if dataset is not None and "lat" in dataset.columns and "lon" in dataset.columns:
                    lat_min, lat_max = cell["lat"], cell["lat"] + cell_size
                    lon_min, lon_max = cell["lon"], cell["lon"] + cell_size
                    subset = dataset[
                        (dataset["lat"] >= lat_min)
                        & (dataset["lat"] < lat_max)
                        & (dataset["lon"] >= lon_min)
                        & (dataset["lon"] < lon_max)
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

    with station_col:
        st.markdown("**Station Inspector**")
        st.write(f"Station ID: {active_station}")
        st.write(f"Packets heard: {ctx['fmt_int'](station_engine.metrics.get('rf_packets', 0))}")
        st.write(f"Aircraft seen: {ctx['fmt_int'](aircraft_seen) if aircraft_seen is not None else '—'}")
        st.write(f"Max distance: {ctx['fmt_float'](max_dist, 1) if max_dist is not None else '—'}")
        st.write(f"P95 distance: {ctx['fmt_float'](p95_dist, 1) if p95_dist is not None else '—'}")
        st.write(f"RF health score: {ctx['fmt_float'](station_engine.metrics.get('health'), 0) if station_engine.metrics.get('health') is not None else '—'}")
        st.write(f"Directional anisotropy: {ctx['fmt_float'](anisotropy, 2) if anisotropy is not None else '—'}")
        st.write(f"Terrain shadow suspected: {'yes' if terrain_flag else 'no' if terrain_flag is not None else 'N/A'}")
        st.write(f"Dataset confidence: {confidence}")

    st.markdown("---")
    panel_cols = st.columns(3)

    with panel_cols[0]:
        st.markdown("**Propagation**")
        if station_engine.metrics.get("rf_packets", 0) < 200:
            st.info("Not enough RF packets for this analysis.")
        else:
            signal = station_engine.metrics.get("signal_distance") or {}
            if signal.get("implemented") and signal.get("data") is not None:
                data_plot = signal.get("data")
                binned = signal.get("binned_data")
                fig = ui_charts.plot_rssi_distance(data_plot, binned=binned)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
            altitude = station_engine.metrics.get("altitude_distance") or {}
            if altitude.get("implemented") and altitude.get("data") is not None:
                data_plot = altitude.get("data")
                med = altitude.get("binned_data")
                fig = ui_charts.plot_altitude_distance(data_plot, med=med)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)

    with panel_cols[1]:
        st.markdown("**Directional RF**")
        az = station_engine.azimuth_df
        if az is not None and not az.empty:
            fig = ui_charts.plot_polar_p95(az)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

    with panel_cols[2]:
        st.markdown("**Terrain impact**")
        terrain = station_engine.metrics.get("terrain") or {}
        data = terrain.get("data")
        if data is not None and not data.empty and "azimuth_center_deg" in data.columns:
            st.line_chart(data, x="azimuth_center_deg", y="p95_distance_km", height=220)
