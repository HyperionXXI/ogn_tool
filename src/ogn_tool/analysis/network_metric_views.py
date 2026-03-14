from __future__ import annotations

import pandas as pd


def network_confidence_level(metrics: dict) -> str:
    """Interpret the network confidence score into a qualitative level."""
    confidence = metrics.get("network_confidence") if isinstance(metrics, dict) else None
    if not isinstance(confidence, dict):
        return "unknown"

    score = float(confidence.get("confidence_score") or 0.0)

    if score >= 0.85:
        return "excellent"
    if score >= 0.70:
        return "good"
    if score >= 0.50:
        return "fair"
    return "weak"


def network_redundancy_level(metrics: dict) -> str:
    """Interpret the network redundancy score into a qualitative level."""
    redundancy = metrics.get("network_redundancy") if isinstance(metrics, dict) else None
    if not isinstance(redundancy, dict):
        return "unknown"

    score = float(redundancy.get("redundancy_score") or 0.0)

    if score >= 0.85:
        return "very_high"
    if score >= 0.70:
        return "high"
    if score >= 0.50:
        return "moderate"
    if score >= 0.30:
        return "fragile"
    return "critical"


def shadow_risk_level(metrics: dict, station_id: str) -> str | None:
    """Return qualitative shadow risk level for a single station."""
    scores = metrics.get("shadow_risk_scores") if isinstance(metrics, dict) else None
    if not isinstance(scores, dict):
        return None

    score = scores.get(station_id)
    if score is None:
        return None

    score = float(score)
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "moderate"
    return "low"


def station_dependency_level(metrics: dict, station_id: str) -> str | None:
    """Return qualitative dependency level for a single station."""
    dependency = metrics.get("station_dependency") if isinstance(metrics, dict) else None
    if not isinstance(dependency, pd.DataFrame) or dependency.empty:
        return None
    if "station_id" not in dependency.columns or "dependency_strength" not in dependency.columns:
        return None

    rows = dependency[dependency["station_id"].astype(str) == str(station_id)]
    if rows.empty:
        return None

    value = pd.to_numeric(rows.iloc[0]["dependency_strength"], errors="coerce")
    score = float(value) if pd.notna(value) else 0.0

    if score >= 0.7:
        return "critical"
    if score >= 0.4:
        return "elevated"
    return "normal"


__all__ = [
    "network_confidence_level",
    "network_redundancy_level",
    "shadow_risk_level",
    "station_dependency_level",
]
