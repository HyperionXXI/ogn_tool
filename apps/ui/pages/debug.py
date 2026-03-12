from __future__ import annotations

import streamlit as st

from apps.ui.view_models.station_view import StationAnalysisView


def render_debug_page(filters):
    ctx = filters
    view = StationAnalysisView.from_context(ctx)

    section_raw = st.container()
    section_stats = st.container()

    with section_raw:
        st.subheader("Raw packets")
        if not ctx['raw_packets_mode']:
            st.info(
                "Raw packets disabled for performance.\n"
                "Enable in Advanced settings -> Developer -> Raw packets mode"
            )
        else:
            packets_ctx = ctx['get_packets_context']()
            if packets_ctx.df_packets is None or packets_ctx.df_packets.empty:
                st.info("No raw packets available.")
            else:
                st.dataframe(packets_ctx.df_packets.head(100), use_container_width=True, height=300)

    with section_stats:
        st.subheader("Dataset statistics")
        station_metrics = view.metrics.get("station_metrics")
        if station_metrics is None or getattr(station_metrics, "empty", False):
            st.info("No station metrics available in dataset.")
        else:
            st.write(station_metrics.head(10))

