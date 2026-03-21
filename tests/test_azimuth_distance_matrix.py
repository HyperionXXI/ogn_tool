from __future__ import annotations

import numpy as np
import pandas as pd

from ogn_tool.kernel.azimuth_distance_matrix import compute_azimuth_distance_matrix


AZIMUTH_BINS = [0.0, 90.0, 180.0, 270.0, 360.0]
DISTANCE_BINS_KM = [0.0, 10.0, 20.0]


def test_compute_azimuth_distance_matrix_returns_expected_shape() -> None:
    observations = pd.DataFrame(
        {
            'bearing_deg': [5.0, 95.0, 185.0],
            'distance_km': [1.0, 11.0, 19.0],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert matrix_array.shape == (len(AZIMUTH_BINS) - 1, len(DISTANCE_BINS_KM) - 1)


def test_compute_azimuth_distance_matrix_preserves_observation_count() -> None:
    observations = pd.DataFrame(
        {
            'bearing_deg': [5.0, 15.0, 95.0, 185.0, 275.0],
            'distance_km': [1.0, 9.9, 11.0, 19.5, 0.1],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert int(matrix_array.sum()) == matrix['packet_count'] == 5


def test_compute_azimuth_distance_matrix_handles_edge_values_deterministically() -> None:
    observations = pd.DataFrame(
        {
            'bearing_deg': [0.0, 359.999, 360.0, 180.0],
            'distance_km': [0.0, 9.999, 10.0, 20.0],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert matrix['packet_count'] == 3
    assert int(matrix_array[0, 0]) == 1
    assert int(matrix_array[3, 0]) == 1
    assert int(matrix_array[0, 1]) == 1
    assert int(matrix_array.sum()) == 3


def test_compute_azimuth_distance_matrix_normalizes_negative_azimuths() -> None:
    observations = pd.DataFrame(
        {
            'bearing_deg': [-5.0, -180.0],
            'distance_km': [5.0, 15.0],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert matrix['packet_count'] == 2
    assert int(matrix_array[3, 0]) == 1
    assert int(matrix_array[2, 1]) == 1


def test_compute_azimuth_distance_matrix_ignores_missing_and_out_of_range_values() -> None:
    observations = pd.DataFrame(
        {
            'bearing_deg': [5.0, None, 95.0, 270.0],
            'distance_km': [1.0, 5.0, 25.0, None],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert matrix['packet_count'] == 1
    assert int(matrix_array.sum()) == 1
    assert int(matrix_array[0, 0]) == 1


def test_compute_azimuth_distance_matrix_accepts_fallback_column_names() -> None:
    observations = pd.DataFrame(
        {
            'bearing': [45.0, 135.0],
            'distance': [5.0, 15.0],
        }
    )

    matrix = compute_azimuth_distance_matrix(observations, AZIMUTH_BINS, DISTANCE_BINS_KM)
    matrix_array = np.asarray(matrix['matrix'])

    assert matrix['packet_count'] == 2
    assert int(matrix_array[0, 0]) == 1
    assert int(matrix_array[1, 1]) == 1
