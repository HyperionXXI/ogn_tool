from __future__ import annotations

from .network_engineering_report import (
    NetworkEngineeringReport,
    StationRFDiagnostics,
)



def _interpret_station(entropy: float, risk: float) -> str:
    if entropy < 0.25:
        return "Directional coverage strongly biased; likely corridor reception."
    if entropy < 0.5:
        return "Moderate directional bias."
    if entropy >= 0.7:
        return "Robust directional coverage."
    return "Intermediate directional distribution."



def _extract_network_metrics(results):
    if isinstance(results, dict):
        metrics = results.get("network_metrics", {})
    else:
        metrics = getattr(results, "network_metrics", {})
    return metrics if isinstance(metrics, dict) else {}



def build_network_engineering_report(results) -> NetworkEngineeringReport:
    metrics = _extract_network_metrics(results)

    entropy = metrics.get("station_angular_entropy", {})
    if not isinstance(entropy, dict):
        entropy = {}

    risk = metrics.get("shadow_risk_scores", {})
    if not isinstance(risk, dict):
        risk = {}

    diagnostics = {}

    stations = set(entropy) | set(risk)

    for station_id in stations:
        station_key = str(station_id)
        entropy_value = float(entropy.get(station_id, 0.0) or 0.0)
        risk_value = float(risk.get(station_id, 0.0) or 0.0)

        diagnostics[station_key] = StationRFDiagnostics(
            station_id=station_key,
            angular_entropy=entropy_value,
            shadow_risk=risk_value,
            interpretation=_interpret_station(entropy_value, risk_value),
        )

    network_summary = metrics.get("network_summary", {})
    if not isinstance(network_summary, dict):
        network_summary = {}

    return NetworkEngineeringReport(
        station_diagnostics=diagnostics,
        network_summary=network_summary,
        notes=[],
    )


__all__ = ["build_network_engineering_report"]
