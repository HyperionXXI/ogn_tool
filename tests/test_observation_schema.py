from __future__ import annotations

from ogn_tool.domain.rf.observation_schema import (
    SHADOW_COLUMNS,
    SPATIAL_COLUMNS,
    VISIBILITY_COLUMNS,
)


def test_spatial_schema_is_stable() -> None:
    assert SPATIAL_COLUMNS == ["station_id", "lat", "lon"]


def test_visibility_schema_is_stable() -> None:
    assert VISIBILITY_COLUMNS == ["src", "igate"]


def test_shadow_schema_is_stable() -> None:
    assert SHADOW_COLUMNS == [
        "station_id",
        "bearing_deg",
        "lat",
        "lon",
        "station_lat",
        "station_lon",
    ]
