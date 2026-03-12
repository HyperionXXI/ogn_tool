from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from ogn_tool.analysis.rf_diagnosis import RFDiagnosis


def build_metrics_summary(dataset) -> Dict[str, Any]:
    metrics = dict((dataset.results.metrics or {}))
    distance_df = metrics.get("distance_df")
    if isinstance(distance_df, pd.DataFrame) and not distance_df.empty:
        metrics.setdefault("rf_packets", int(len(distance_df)))
    return metrics


def compute_rf_health(metrics: Dict[str, Any], directional_balance: Any | None = None) -> Dict[str, Any]:
    diagnosis = RFDiagnosis(metrics, directional_balance)
    return {
        "health": diagnosis.health_score(),
        "issues": diagnosis.evaluate(),
    }


def aggregate_metrics(dataset) -> Dict[str, Any]:
    metrics = build_metrics_summary(dataset)
    directional_balance = metrics.get("directional_balance")
    rf_diag = compute_rf_health(metrics, directional_balance=directional_balance)
    metrics.setdefault("rf_diagnosis", rf_diag)
    dataset.results.metrics = metrics
    return metrics


__all__ = ["aggregate_metrics", "build_metrics_summary", "compute_rf_health"]
