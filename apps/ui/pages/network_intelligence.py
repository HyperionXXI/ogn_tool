import streamlit as st
import pydeck as pdk
import pandas as pd

from ogn_tool.network.network_intelligence import compute_coverage_redundancy


def render_network_intelligence(ctx):
    st.title("Network Intelligence")

    df = ctx.get("rf_packets")
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        df = ctx.get("packets_window")

    st.write("Rows:", len(df) if isinstance(df, pd.DataFrame) else 0)

    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        st.warning("No packets available")
        return

    if "lat" not in df.columns or "lon" not in df.columns:
        st.warning("Packet dataset has no coordinates")
        return

    df_plot = df.copy()
    df_plot["lat"] = pd.to_numeric(df_plot["lat"], errors="coerce")
    df_plot["lon"] = pd.to_numeric(df_plot["lon"], errors="coerce")
    df_plot = df_plot.dropna(subset=["lat", "lon"])

    if df_plot.empty:
        st.warning("No valid aircraft coordinates available for RF map")
        return

    st.subheader("Coverage redundancy map")
    redundancy = compute_coverage_redundancy(df_plot)

    if redundancy is None or len(redundancy) == 0:
        st.warning("No redundancy map available (single-station dataset)")

        layer = pdk.Layer(
            "ScatterplotLayer",
            df_plot,
            get_position='[lon, lat]',
            get_radius=1500,
            get_fill_color=[0, 120, 255],
            pickable=True,
        )

        view = pdk.ViewState(
            latitude=float(df_plot["lat"].mean()),
            longitude=float(df_plot["lon"].mean()),
            zoom=7,
        )

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view),
            use_container_width=True,
        )

    else:
        layer = pdk.Layer(
            "ScatterplotLayer",
            redundancy,
            get_position='[grid_lon, grid_lat]',
            get_radius=5000,
            get_fill_color='[200, 30 * stations, 0]',
            pickable=True,
        )

        view = pdk.ViewState(
            latitude=float(df_plot["lat"].mean()),
            longitude=float(df_plot["lon"].mean()),
            zoom=6,
        )

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view),
            use_container_width=True,
        )
