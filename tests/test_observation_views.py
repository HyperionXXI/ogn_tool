from __future__ import annotations

import pandas as pd

from ogn_tool.reporting.views.observation_views import (
    build_shadow_observation_frame,
    build_spatial_observation_frame,
    build_visibility_observation_frame,
)
from ogn_tool.models.rf_observation_vector import RFObservationVector


def test_build_spatial_observation_frame_normalizes_station_id() -> None:
    observations = pd.DataFrame([{"igate": "S1", "lat": "47.0", "lon": "7.0"}])

    frame = build_spatial_observation_frame(observations)

    assert frame.to_dict(orient="records") == [{"station_id": "S1", "lat": 47.0, "lon": 7.0}]


def test_build_visibility_observation_frame_normalizes_src_and_igate() -> None:
    observations = pd.DataFrame([{"station_id": "S1", "aircraft_id": "A1"}])

    frame = build_visibility_observation_frame(observations)

    assert frame.to_dict(orient="records") == [{"src": "A1", "igate": "S1"}]


def test_build_shadow_observation_frame_preserves_directional_columns() -> None:
    observations = [
        RFObservationVector(
            station_id="S1",
            aircraft_id="A1",
            lat=47.0,
            lon=7.0,
            altitude_m=1000.0,
            distance_km=10.0,
            bearing_deg=30.0,
            radio_horizon_km=120.0,
            timestamp=1,
            timestamp_ns=1,
        )
    ]

    frame = build_shadow_observation_frame(observations)

    assert frame.loc[0, "station_id"] == "S1"
    assert float(frame.loc[0, "bearing_deg"]) == 30.0


def test_build_shadow_observation_frame_guarantees_schema() -> None:
    observations = pd.DataFrame([{"station_id": "S1"}])

    frame = build_shadow_observation_frame(observations)

    assert frame.columns.tolist() == [
        "station_id",
        "bearing_deg",
        "lat",
        "lon",
        "station_lat",
        "station_lon",
    ]
