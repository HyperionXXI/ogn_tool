from __future__ import annotations

import pandas as pd

from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.runtime.scenario_ranking import rank_station_addition_candidates


REQUIRED_COLUMNS = {"lat", "lon"}


def search_station_candidates(
    baseline_snapshot: dict[str, object],
    *,
    observations,
    candidates: pd.DataFrame,
    top_k: int = 10,
) -> list[ScenarioResult]:
    if not isinstance(candidates, pd.DataFrame):
        raise ValueError("candidates must be a pandas DataFrame")

    missing = REQUIRED_COLUMNS - set(candidates.columns)
    if missing:
        raise ValueError(f"Missing candidate columns: {sorted(missing)}")

    normalized = candidates[["lat", "lon"]].copy()
    normalized["lat"] = pd.to_numeric(normalized["lat"], errors="coerce")
    normalized["lon"] = pd.to_numeric(normalized["lon"], errors="coerce")
    normalized = normalized.dropna(subset=["lat", "lon"])

    candidate_list = normalized.to_dict(orient="records")
    ranked = rank_station_addition_candidates(
        baseline_snapshot,
        observations=observations,
        candidates=candidate_list,
    )

    if top_k <= 0:
        return []
    return ranked[:top_k]


__all__ = ["search_station_candidates"]
