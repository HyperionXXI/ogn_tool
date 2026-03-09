from __future__ import annotations

import pydeck as pdk


def build_deck_map(layers, center_lat: float, center_lon: float):
    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=8,
        pitch=40,
    )
    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={
            "text": (
                "Aircraft: {aircraft_id}\n"
                "Station: {station_id}\n"
                "RSSI: {rssi}\n"
                "Distance: {distance_km} km\n"
                "Degree: {network_degree}\n"
                "Link: {station_a} ↔ {station_b}\n"
                "Shared: {shared_aircraft}\n"
                "Overlap: {overlap_ratio}"
            )
        },
    )
