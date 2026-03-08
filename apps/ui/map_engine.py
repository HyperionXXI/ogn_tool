import streamlit as st
import folium
from streamlit_folium import st_folium


def render_map_click(m):
    map_data = st_folium(m, height=700, use_container_width=True)
    if isinstance(map_data, dict):
        clicked = map_data.get("last_clicked")
        if clicked:
            return clicked.get("lat"), clicked.get("lng")
    return None, None
