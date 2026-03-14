from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.models.rf_analysis_results import RFAnalysisResults

from .models import NetworkEngineeringReport


def _records(df: Any, columns: list[str], limit: int = 5) -> list[dict[str, Any]]:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []
    present = [column for column in columns if column in df.columns]
    if not present:
        return []
    return df[present].head(limit).to_dict(orient="records")


def build_network_engineering_report(results: RFAnalysisResults) -> NetworkEngineeringReport:
    metrics = dict(getattr(results, "network_metrics", None) or {})

    summary = dict(metrics.get("network_summary") or {})
    health = metrics.get("station_health")
    spof = metrics.get("spof")
    gaps = metrics.get("coverage_gaps")
    redundancy = metrics.get("station_redundancy_planner")
    addition = metrics.get("station_addition_simulation")

    critical_stations: list[str] = []
    warning_stations: list[str] = []
    if isinstance(health, pd.DataFrame) and not health.empty:
        if {"station_id", "health_status"}.issubset(health.columns):
            critical_stations = (
                health.loc[health["health_status"] == "CRITICAL", "station_id"].astype(str).tolist()
            )
            warning_stations = (
                health.loc[health["health_status"] == "WARNING", "station_id"].astype(str).tolist()
            )

    notes = [str(note) for note in summary.get("notes", []) if note]
    if not notes:
        if critical_stations:
            notes.append(f"{len(critical_stations)} critical station(s) require attention")
        elif warning_stations:
            notes.append(f"{len(warning_stations)} warning station(s) require monitoring")
        else:
            notes.append("No immediate network engineering issue detected")

    return NetworkEngineeringReport(
        network_status=str(summary.get("network_status", "UNKNOWN")),
        critical_stations=critical_stations,
        warning_stations=warning_stations,
        top_spof_stations=_records(
            spof,
            ["station_id", "spof_level", "coverage_loss_ratio", "aircraft_lost", "spof_score"],
        ),
        top_gap_candidates=_records(
            gaps,
            ["lat", "lon", "station_count", "gap_level", "notes"],
        ),
        top_redundancy_priorities=_records(
            redundancy,
            ["target_station", "coverage_loss", "aircraft_lost", "priority", "notes"],
        ),
        top_station_addition_candidates=_records(
            addition,
            ["lat", "lon", "coverage_gain", "redundancy_gain", "priority_score", "notes"],
        ),
        summary_notes=notes,
    )
