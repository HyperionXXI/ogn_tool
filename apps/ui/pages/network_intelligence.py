import streamlit as st
import pandas as pd
import pydeck as pdk
try:
    from pyvis.network import Network
except Exception:
    Network = None
import tempfile

from ogn_tool.network.network_intelligence import (
    compute_network_topology,
    compute_station_roles,
    compute_coverage_redundancy
)

from ogn_tool.analysis.rf_blind_zone_detection import detect_rf_blind_zones

from ogn_tool.services.data_service import load_packets


def render_network_intelligence():

    st.title("Network Intelligence")

    df = load_packets()

    if df is None or len(df) == 0:
        st.warning("No packets available")
        return

    st.subheader("Station roles")

    roles = compute_station_roles(df)
    roles_df = pd.DataFrame.from_dict(roles, orient="index")

    st.dataframe(roles_df)

    st.download_button(
        "Export station roles",
        roles_df.to_csv(),
        file_name="station_roles.csv"
    )

    st.subheader("Coverage redundancy")

    redundancy = compute_coverage_redundancy(df)

    st.dataframe(redundancy)


    st.subheader("RF blind zones")

    blind = detect_rf_blind_zones(df)

    st.dataframe(
        blind.sort_values("blind_score", ascending=False).head(20)
    )

    st.subheader("Network interpretation")

    station_count = roles_df.shape[0]
    aircraft_count = len(set(df["src"]))

    if station_count == 1:
        st.info("Single-station analysis mode")
    elif station_count < 5:
        st.warning("Sparse station network")
    else:
        st.success("Multi-station network detected")

    st.metric("Stations", station_count)
    st.metric("Aircraft", aircraft_count)

    st.subheader("Network topology")

    topo = compute_network_topology(df)

    st.metric("Nodes", len(topo["nodes"]))
    st.metric("Edges", len(topo["edges"]))

    st.subheader("Network graph")

    if Network is None:
        st.warning("pyvis is not installed. Install it to view the network graph.")
    else:
        net = Network(height="500px", width="100%")

        for node in topo["nodes"]:
            color = "red" if node["type"] == "station" else "blue"
            net.add_node(node["id"], label=node["id"], color=color)

        for edge in topo["edges"]:
            net.add_edge(edge["source"], edge["target"])

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        net.save_graph(tmp.name)

        with open(tmp.name, "r", encoding="utf-8") as f:
            html = f.read()

        st.components.v1.html(html, height=520)

    st.subheader("Coverage redundancy map")

    layer = pdk.Layer(
        "ScatterplotLayer",
        redundancy,
        get_position='[grid_lon, grid_lat]',
        get_radius=5000,
        get_fill_color='[200, 30 * stations, 0]',
        pickable=True
    )

    view = pdk.ViewState(
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=6
    )

    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view))
