from __future__ import annotations

from typing import Any

LOW_SNR_EDGE = "LOW_SNR_EDGE"
HIGH_INFERRED_RATIO = "HIGH_INFERRED_RATIO"
ASYMMETRIC_LINK = "ASYMMETRIC_LINK"
LOW_VOLUME_EDGE = "LOW_VOLUME_EDGE"

INFERRED_RATIO_THRESHOLD = 0.5
ASYMMETRIC_SNR_GAP = 5.0


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    base = int(position)
    rest = position - base

    if base + 1 < len(ordered):
        return ordered[base] + rest * (ordered[base + 1] - ordered[base])
    return ordered[base]


def detect_rf_anomalies(edges: list[dict]) -> list[dict]:
    if not isinstance(edges, list) or not edges:
        return []

    snr_values = []
    volume_values = []

    for edge in edges:
        snr = _to_float(edge.get("avg_snr"))
        if snr is not None:
            snr_values.append(snr)

        count = _to_float(edge.get("message_count"))
        if count is not None:
            volume_values.append(count)

    low_snr_threshold = _quantile(snr_values, 0.1)
    low_volume_threshold = _quantile(volume_values, 0.1)

    reverse_lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in edges:
        emitter_id = str(edge.get("emitter_id") or "")
        receiver_id = str(edge.get("receiver_id") or "")
        reverse_lookup[(emitter_id, receiver_id)] = edge

    enriched: list[dict[str, Any]] = []

    for edge in edges:
        anomalies: list[str] = []

        emitter_id = str(edge.get("emitter_id") or "")
        receiver_id = str(edge.get("receiver_id") or "")
        avg_snr = _to_float(edge.get("avg_snr"))
        message_count = _to_float(edge.get("message_count"))
        inferred_ratio = _to_float(edge.get("inferred_ratio")) or 0.0

        if low_snr_threshold is not None and avg_snr is not None and avg_snr < low_snr_threshold:
            anomalies.append(LOW_SNR_EDGE)

        if low_volume_threshold is not None and message_count is not None and message_count < low_volume_threshold:
            anomalies.append(LOW_VOLUME_EDGE)

        if inferred_ratio > INFERRED_RATIO_THRESHOLD:
            anomalies.append(HIGH_INFERRED_RATIO)

        reverse = reverse_lookup.get((receiver_id, emitter_id))
        reverse_snr = _to_float(reverse.get("avg_snr")) if reverse else None

        if reverse is None or reverse_snr is None:
            anomalies.append(ASYMMETRIC_LINK)
        elif avg_snr is not None and reverse_snr <= (avg_snr - ASYMMETRIC_SNR_GAP):
            anomalies.append(ASYMMETRIC_LINK)

        unique_anomalies = list(dict.fromkeys(anomalies))
        anomaly_score = len(unique_anomalies) / 4.0

        enriched.append(
            {
                **edge,
                "anomalies": unique_anomalies,
                "anomaly_score": anomaly_score,
            }
        )

    return enriched
