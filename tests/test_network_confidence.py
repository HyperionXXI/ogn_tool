from __future__ import annotations

from ogn_tool.analysis.intelligence.network_confidence import compute_network_confidence


def test_network_confidence_tiny_dataset_is_low() -> None:
    metrics = {
        "network_summary": {"station_count": 2},
        "visibility": {
            "summary": {
                "aircraft_count": 8,
                "mean_stations_per_aircraft": 1.0,
            }
        },
    }

    score, warnings = compute_network_confidence(metrics)

    assert score < 0.3
    assert warnings


def test_network_confidence_large_dataset_is_high() -> None:
    metrics = {
        "network_summary": {"station_count": 5},
        "visibility": {
            "summary": {
                "aircraft_count": 120,
                "mean_stations_per_aircraft": 2.4,
            }
        },
    }

    score, warnings = compute_network_confidence(metrics)

    assert score > 0.7
    assert not warnings


def test_network_confidence_missing_fields_degrades_safely() -> None:
    score, warnings = compute_network_confidence({})

    assert 0.0 <= score <= 1.0
    assert warnings


def test_network_confidence_is_strictly_clamped() -> None:
    metrics = {
        "network_summary": {"station_count": 1},
        "visibility": {
            "summary": {
                "aircraft_count": 0,
                "mean_stations_per_aircraft": 0.0,
            }
        },
    }

    score, warnings = compute_network_confidence(metrics)

    assert 0.0 <= score <= 1.0
    assert warnings
