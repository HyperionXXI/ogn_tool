from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.kernel.spatial.traffic_density import (
    build_aircraft_weights,
    compute_traffic_density,
)



def test_compute_traffic_density_counts_cells() -> None:
    observations = pd.DataFrame(
        [
            {"lat": 47.001, "lon": 7.001},
            {"lat": 47.009, "lon": 7.009},
            {"lat": 47.021, "lon": 7.021},
        ]
    )

    density = compute_traffic_density(observations, grid_size=0.02)

    assert density == {
        (47.0, 7.0): 2.0,
        (47.02, 7.02): 1.0,
    }



def test_compute_traffic_density_validates_inputs() -> None:
    with pytest.raises(ValueError):
        compute_traffic_density(None)

    with pytest.raises(ValueError):
        compute_traffic_density(pd.DataFrame([{"lat": 47.0}]))

    with pytest.raises(ValueError):
        compute_traffic_density(pd.DataFrame([{"lat": 47.0, "lon": 7.0}]), grid_size=0)



def test_build_aircraft_weights_uses_inverse_density() -> None:
    observations = pd.DataFrame(
        [
            {"lat": 47.001, "lon": 7.001, "aircraft_id": "A1"},
            {"lat": 47.009, "lon": 7.009, "aircraft_id": "A2"},
            {"lat": 47.021, "lon": 7.021, "aircraft_id": "A3"},
        ]
    )

    weights = build_aircraft_weights(observations, grid_size=0.02)

    assert weights == {
        "A1": 0.5,
        "A2": 0.5,
        "A3": 1.0,
    }



def test_build_aircraft_weights_accepts_src_column() -> None:
    observations = pd.DataFrame(
        [
            {"lat": 47.001, "lon": 7.001, "src": "A1"},
        ]
    )

    weights = build_aircraft_weights(observations, grid_size=0.02)

    assert weights == {"A1": 1.0}
