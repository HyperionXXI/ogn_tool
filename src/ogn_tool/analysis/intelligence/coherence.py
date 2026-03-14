from __future__ import annotations

import pandas as pd


def check_intelligence_coherence(metrics: dict) -> list[str]:
    warnings: list[str] = []

    if not isinstance(metrics, dict):
        return warnings

    redundancy = metrics.get("network_redundancy")
    dependency = metrics.get("station_dependency")
    dominance = metrics.get("station_dominance")
    spof = metrics.get("spof")

    if not isinstance(redundancy, dict):
        return warnings

    redundancy_score = float(redundancy.get("redundancy_score") or 0.0)

    mean_dominance_ratio = 0.0
    if isinstance(dominance, pd.DataFrame) and not dominance.empty and "dominance_ratio" in dominance.columns:
        mean_dominance_ratio = float(pd.to_numeric(dominance["dominance_ratio"], errors="coerce").fillna(0.0).mean())

    strong_dependency_ratio = 0.0
    if isinstance(dependency, pd.DataFrame) and not dependency.empty and "dependency_strength" in dependency.columns:
        strengths = pd.to_numeric(dependency["dependency_strength"], errors="coerce").fillna(0.0)
        strong_dependency_ratio = float((strengths >= 0.7).mean())

    if redundancy_score > 0.7 and strong_dependency_ratio > 0.0:
        warnings.append(
            "High network redundancy reported but strong station dependencies detected."
        )

    if redundancy_score > 0.7 and isinstance(spof, pd.DataFrame) and not spof.empty:
        warnings.append(
            "High network redundancy reported but single points of failure are still present."
        )

    if redundancy_score > 0.7 and mean_dominance_ratio > 0.6:
        warnings.append(
            "High network redundancy reported but station dominance remains strongly concentrated."
        )

    if strong_dependency_ratio > 0.0 and mean_dominance_ratio < 0.2:
        warnings.append(
            "Strong station dependencies detected without corresponding station dominance signal."
        )

    return warnings
