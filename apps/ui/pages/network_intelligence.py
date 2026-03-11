import streamlit as st
import pandas as pd

from ogn_tool.network.network_intelligence import (
    compute_network_topology,
    compute_station_roles,
    compute_coverage_redundancy
)

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

    st.subheader("Coverage redundancy")

    redundancy = compute_coverage_redundancy(df)

    st.dataframe(redundancy)

    st.subheader("Network topology")

    topo = compute_network_topology(df)

    st.metric("Nodes", len(topo["nodes"]))
    st.metric("Edges", len(topo["edges"]))
