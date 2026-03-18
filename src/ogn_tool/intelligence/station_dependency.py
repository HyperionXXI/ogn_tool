from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics


def compute_station_dependency(network_metrics: NetworkMetrics | None) -> pd.DataFrame:
    """Estimate inter-station dependency from existing network metrics.

    This is an intelligence-layer heuristic. It does not rebuild the network
    graph and does not compute new low-level RF metrics.
    """
    network_metrics = ensure_metrics(network_metrics)
    overlap = ((network_metrics.get("visibility") or {}).get("overlap") if isinstance(network_metrics.get("visibility"), dict) else None)
    influence = network_metrics.get("station_influence")
    robustness = network_metrics.get("network_robustness")

    if not isinstance(overlap, pd.DataFrame) or overlap.empty:
        return pd.DataFrame(columns=[
            "station_id",
            "depends_on_station",
            "dependency_strength",
            "dependency_type",
            "notes",
        ])

    influence_map: dict[str, float] = {}
    if isinstance(influence, pd.DataFrame) and not influence.empty and {"station_id", "influence_score"}.issubset(influence.columns):
        influence_map = {
            str(row["station_id"]): float(row["influence_score"] or 0.0)
            for _, row in influence[["station_id", "influence_score"]].iterrows()
        }

    impact_map: dict[str, float] = {}
    if isinstance(robustness, pd.DataFrame) and not robustness.empty and {"station_id", "impact_score"}.issubset(robustness.columns):
        impact_map = {
            str(row["station_id"]): float(row["impact_score"] or 0.0)
            for _, row in robustness[["station_id", "impact_score"]].iterrows()
        }

    rows: list[dict] = []
    for station_id in overlap.index:
        station_key = str(station_id)
        row = pd.to_numeric(overlap.loc[station_id], errors="coerce").drop(labels=[station_id], errors="ignore").dropna()
        if row.empty:
            continue

        dominant_station = str(row.idxmax())
        dominant_overlap = float(row.max())
        total_overlap = float(row.sum())
        dependency_strength = float(dominant_overlap / total_overlap) if total_overlap > 0 else 0.0

        dominant_influence = float(influence_map.get(dominant_station, 0.0))
        local_influence = float(influence_map.get(station_key, 0.0))
        dominant_impact = float(impact_map.get(dominant_station, 0.0))
        local_impact = float(impact_map.get(station_key, 0.0))

        if dependency_strength >= 0.7:
            dependency_type = "overlap_dominance"
            notes = "coverage overlap is dominated by a single neighbouring station"
        elif dominant_impact > local_impact and dominant_influence > local_influence:
            dependency_type = "robustness_asymmetry"
            notes = "neighbouring station appears structurally more critical"
        else:
            dependency_type = "shared_coverage_bias"
            notes = "coverage appears shared but biased toward one neighbouring station"

        rows.append(
            {
                "station_id": station_key,
                "depends_on_station": dominant_station,
                "dependency_strength": dependency_strength,
                "dependency_type": dependency_type,
                "notes": notes,
            }
        )

    if not rows:
        return pd.DataFrame(columns=[
            "station_id",
            "depends_on_station",
            "dependency_strength",
            "dependency_type",
            "notes",
        ])

    return pd.DataFrame(rows).sort_values(["dependency_strength", "station_id"], ascending=[False, True]).reset_index(drop=True)
