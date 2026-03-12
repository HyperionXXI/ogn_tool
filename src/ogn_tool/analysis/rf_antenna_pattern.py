import numpy as np


def _get_field(feature_matrix, name):
    if isinstance(feature_matrix, dict):
        return feature_matrix[name]
    return getattr(feature_matrix, name)


def estimate_antenna_pattern(feature_matrix, bins=36):

    bearing = _get_field(feature_matrix, "bearing")
    distance = _get_field(feature_matrix, "distance")
    # backward-compatible: horizon may be dynamic attr or legacy dict key
    horizon = _get_field(feature_matrix, "horizon")

    edges = np.linspace(0, 360, bins + 1)

    exposure = np.zeros(bins)
    received = np.zeros(bins)

    bin_index = np.digitize(bearing, edges) - 1

    for i in range(len(bearing)):

        b = bin_index[i]

        if b < 0 or b >= bins:
            continue

        if distance[i] < horizon[i]:
            exposure[b] += 1
            received[b] += 1

    probability = np.divide(
        received,
        exposure,
        out=np.zeros_like(received),
        where=exposure > 0,
    )

    azimuth = (edges[:-1] + edges[1:]) / 2

    return {
        "azimuth": azimuth,
        "probability": probability,
        "exposure": exposure,
        "received": received,
    }


def detect_shadow_sectors(pattern, threshold=0.4):

    p = pattern["probability"]
    az = pattern["azimuth"]

    sectors = []

    for i in range(len(p)):
        if p[i] < threshold * np.max(p):
            sectors.append(az[i])

    return sectors
