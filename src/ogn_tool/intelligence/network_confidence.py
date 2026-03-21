from __future__ import annotations


def compute_network_confidence(metrics: dict | None) -> tuple[float, list[str]]:
    """Estimate statistical confidence of inferred network metrics.

    The score reflects whether the observed dataset is large and diverse enough
    to support stable RF network inference.

    Returns
    -------
    tuple[float, list[str]]
        Confidence score clamped to [0.0, 1.0] and human-readable warnings
        explaining degraded confidence.
    """
    metrics = metrics or {}

    summary = metrics.get("network_summary")
    if not isinstance(summary, dict):
        summary = {}

    visibility = metrics.get("visibility")
    if not isinstance(visibility, dict):
        visibility = {}

    visibility_summary = visibility.get("summary")
    if not isinstance(visibility_summary, dict):
        visibility_summary = {}

    station_count = int(summary.get("station_count") or 0)
    aircraft_count = int(visibility_summary.get("aircraft_count") or 0)
    mean_stations_per_aircraft = float(visibility_summary.get("mean_stations_per_aircraft") or 0.0)

    confidence = 1.0
    warnings: list[str] = []

    if station_count < 3:
        confidence *= 0.5
        warnings.append("Too few stations to infer network structure reliably.")

    if aircraft_count < 10:
        confidence *= 0.2
        warnings.append("Insufficient dataset for reliable network inference.")
    elif aircraft_count < 50:
        confidence *= 0.5
        warnings.append("Low aircraft count; network metrics may be unstable.")

    if mean_stations_per_aircraft < 1.2:
        confidence *= 0.8
        warnings.append("Observed redundancy is too sparse for robust network inference.")

    confidence = min(max(float(confidence), 0.0), 1.0)
    return confidence, warnings
