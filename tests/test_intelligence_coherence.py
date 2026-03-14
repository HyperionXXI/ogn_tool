from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence.coherence import check_intelligence_coherence


def test_detects_redundancy_dependency_conflict() -> None:
    metrics = {
        "station_dependency": pd.DataFrame([{"station_id": "A", "dependency_strength": 0.9}]),
        "station_dominance": pd.DataFrame([{"station_id": "A", "dominance_ratio": 0.2}]),
        "network_redundancy": {"redundancy_score": 0.8},
        "spof": pd.DataFrame(),
    }

    warnings = check_intelligence_coherence(metrics)

    assert any("redundancy" in warning.lower() for warning in warnings)


def test_detects_redundancy_spof_conflict() -> None:
    metrics = {
        "station_dependency": pd.DataFrame(),
        "station_dominance": pd.DataFrame([{"station_id": "A", "dominance_ratio": 0.1}]),
        "network_redundancy": {"redundancy_score": 0.8},
        "spof": pd.DataFrame([{"station_id": "S1"}]),
    }

    warnings = check_intelligence_coherence(metrics)

    assert any("single points of failure" in warning.lower() for warning in warnings)
