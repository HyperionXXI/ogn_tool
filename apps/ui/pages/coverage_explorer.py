from __future__ import annotations

import streamlit as st

try:
    import pydeck as pdk
except Exception:  # pragma: no cover
    pdk = None

from ogn_tool.engine.rf_engine import RFAnalysisEngine

from ui.layout import DASHBOARD_COLUMNS
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


def _build_grid_polygons(grid, color_key):
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

    left, right = st.columns([7, 3])

    with left:
        st.markdown("**Map layers**")
        show_prob = st.checkbox("RF probability field", value=True)
        show_conf = st.checkbox("Confidence", value=True)
        show_points = st.checkbox("Raw packet points", value=False)
        show_station = st.checkbox("Station location", value=True)
        show_rings = st.checkbox("Range circles", value=True)

        if pdk is None:
            st.error("Missing dependency: pydeck. Install: pip install pydeck")
        else:
            deck_layers = []
            if rf_grid is not None and not rf_grid.empty:
                grid = rf_grid.dropna(subset=["lat", "lon"])
                if not grid.empty:
                    grid_df, cell_size = _build_grid_polygons(grid, "probability")

                    if show_prob and "probability" in grid_df.columns:
                        prob_bins = st.session_state.get("_prob_bins")
                        if prob_bins is None:
                            prob_bins = None
                        prob_colors = [
                            [220, 38, 38, 110],
                            [249, 115, 22, 120],
                            [234, 179, 8, 130],
                            [132, 204, 22, 140],
                            [34, 197, 94, 150],
                        ]
                        probs = ctx["pd"].cut(
                            ctx["pd"].to_numeric(grid_df.get("probability"), errors="coerce").fillna(0.0),
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
                            ctx["pd"].to_numeric(grid_df.get("confidence"), errors="coerce").fillna(0.0),
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
                        )
                    )

            station = {"lat": ctx.get("station_lat"), "lon": ctx.get("station_lon")}
            if show_station and station["lat"] is not None and station["lon"] is not None:
                deck_layers.append(
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=[station],
                        get_position=["lon", "lat"],
                        get_radius=300,
                        get_fill_color=[37, 99, 235, 200],
                    )
                )
            if show_rings and station["lat"] is not None and station["lon"] is not None:
                for r_km in (10, 20, 40):
                    deck_layers.append(
                        pdk.Layer(
                            "ScatterplotLayer",
                            data=[station],
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
            deck = pdk.Deck(layers=deck_layers, initial_view_state=view, map_style=_map_style(ctx))
            st.pydeck_chart(deck, use_container_width=True)

    with right:
        st.markdown("**Station Health**")
        range_summary = (engine_result.metrics.get("station_range") or {}).get("summary") or {}
        max_dist = range_summary.get("max_distance_km")
        p95_dist = range_summary.get("p95_distance_km")
        aircraft_seen = rf_packets["src"].nunique() if rf_packets is not None and "src" in rf_packets.columns else None
        c1, c2 = st.columns(2)
        metric_card(c1, "RF packets", ctx["fmt_int"](engine_result.metrics.get("rf_packets", 0)))
        metric_card(c2, "Aircraft", ctx["fmt_int"](aircraft_seen) if aircraft_seen is not None else "—")
        metric_card(c1, "Max distance", ctx["fmt_float"](max_dist, 1) if max_dist is not None else "—")
        metric_card(c2, "P95 distance", ctx["fmt_float"](p95_dist, 1) if p95_dist is not None else "—")

        st.markdown("**Propagation**")
        signal = engine_result.metrics.get("signal_distance") or {}
        if signal.get("implemented") and signal.get("data") is not None:
            data_plot = signal.get("data")
            binned = signal.get("binned_data")
            fig = ui_charts.plot_rssi_distance(data_plot, binned=binned)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
        altitude = engine_result.metrics.get("altitude_distance") or {}
        if altitude.get("implemented") and altitude.get("data") is not None:
            data_plot = altitude.get("data")
            med = altitude.get("binned_data")
            fig = ui_charts.plot_altitude_distance(data_plot, med=med)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Directional RF**")
        az = engine_result.azimuth_df
        if az is not None and not az.empty:
            fig = ui_charts.plot_polar_p95(az)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Terrain impact**")
        terrain = engine_result.metrics.get("terrain") or {}
        data = terrain.get("data")
        if data is not None and not data.empty and "azimuth_center_deg" in data.columns:
            st.line_chart(data, x="azimuth_center_deg", y="p95_distance_km", height=220)
