from __future__ import annotations

from .network_engineering_report import (
    NetworkEngineeringReport,
    StationRFDiagnostics,
)


EXPECTED_REPORT_METRICS = {
    "network_summary",
    "station_angular_entropy",
    "shadow_risk_scores",
}



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



def _ensure_dict(metrics: dict, key: str, warnings: list[str]) -> dict:
    value = metrics.get(key)

    if value is None:
        warnings.append(f"{key} missing from network_metrics")
        return {}

    if not isinstance(value, dict):
        warnings.append(f"{key} expected dict but got {type(value).__name__}")
        return {}

    return value


def build_network_engineering_report(results) -> NetworkEngineeringReport:
    metrics = _extract_network_metrics(results)
    warnings: list[str] = []

    pipeline_warnings = metrics.get("_contract_warnings", [])
    if isinstance(pipeline_warnings, list):
        warnings.extend(str(warning) for warning in pipeline_warnings)

    coherence_warnings = metrics.get("_coherence_warnings", [])
    if isinstance(coherence_warnings, list):
        warnings.extend(str(warning) for warning in coherence_warnings)

    for key in sorted(EXPECTED_REPORT_METRICS):
        if key not in metrics:
            warnings.append(f"{key} missing from network_metrics")

    entropy = _ensure_dict(metrics, "station_angular_entropy", warnings)
    risk = _ensure_dict(metrics, "shadow_risk_scores", warnings)
    network_summary = _ensure_dict(metrics, "network_summary", warnings)

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

    return NetworkEngineeringReport(
        station_diagnostics=diagnostics,
        network_summary=network_summary,
        notes=[],
        input_warnings=warnings,
    )


__all__ = ["build_network_engineering_report"]
