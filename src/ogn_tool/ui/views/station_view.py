from __future__ import annotations

import streamlit as st

from ogn_tool.ui.models.station_insight import StationInsight


def render_station_list(insights: list[StationInsight]) -> None:
    st.subheader('Stations')

    if not insights:
        st.info('No station insights available.')
        return

    for insight in insights:
        title = f"{insight.station_id} ({insight.health_status or 'UNKNOWN'})"
        with st.expander(title, expanded=False):
            st.markdown('**Activity**')
            st.write(
                {
                    'packet_count': insight.activity.packet_count,
                    'unique_aircraft': insight.activity.unique_aircraft,
                }
            )

            st.markdown('**Direction**')
            st.write(
                {
                    'corridor_center_deg': insight.direction.corridor_center_deg,
                    'dominant_corridor_share': insight.direction.dominant_corridor_share,
                    'coverage_uniformity_score': insight.direction.coverage_uniformity_score,
                    'gap_count': insight.direction.gap_count,
                    'largest_gap_deg': insight.direction.largest_gap_deg,
                }
            )

            st.markdown('**Network**')
            st.write(
                {
                    'station_count': insight.network.station_count,
                    'co_visible_stations': insight.network.co_visible_stations,
                }
            )

            st.markdown('**Impact**')
            st.write(
                {
                    'impact_score': insight.impact.impact_score,
                    'only_seen_aircraft_count': insight.impact.only_seen_aircraft_count,
                }
            )


__all__ = ['render_station_list']
