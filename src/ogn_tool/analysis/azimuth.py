"""Legacy entry point for experimental azimuth diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from .experimental.azimuth import compute_azimuth_radiation


def compute_azimuth_histogram(bearing_deg):
    """Compute a fixed 36-sector (10°) azimuth histogram.

    This uses a fixed binning of 0-360° into 36 equal sectors.

    Accepts either a DataFrame with a `bearing_deg` column or a sequence
    (Series/ndarray/list) of bearing values.
    """

    import numpy as np
    import pandas as pd

    # Support passing the bearing column directly
    if isinstance(bearing_deg, (pd.Series, list, tuple, np.ndarray)):
        bearings_series = pd.to_numeric(bearing_deg, errors="coerce")
    elif isinstance(bearing_deg, dict):
        # Allow dict-like input containing 'bearing_deg'
        if "bearing_deg" not in bearing_deg:
            return None
        bearings_series = pd.to_numeric(bearing_deg["bearing_deg"], errors="coerce")
    else:
        # Assume it's a DataFrame-like with columns
        try:
            bearings_series = pd.to_numeric(bearing_deg["bearing_deg"], errors="coerce")
        except Exception:
            return None

    # Ensure we can call `.dropna()` regardless of input type
    if isinstance(bearings_series, np.ndarray):
        bearings_series = pd.Series(bearings_series)
    bearings_series = bearings_series.dropna()
    if bearings_series.empty:
        return None

    bins = np.linspace(0, 360, 37)  # 36 bins (10° each)
    hist, edges = np.histogram(bearings_series, bins=bins)

    sectors = []
    for i in range(len(hist)):
        sectors.append({
            "azimuth_start": float(edges[i]),
            "azimuth_end": float(edges[i + 1]),
            "packet_count": int(hist[i]),
        })

    return sectors

def detect_sector_bias(azimuth_histogram: dict) -> dict:
    """Detect directional bias in packet distribution per azimuth sector.

    A sector is considered *weak* if its count is below 40% of the average
    sector count, and *strong* if it is above 160% of the average.

    Args:
        azimuth_histogram: Mapping of cardinal sector labels (e.g. "N", "NE")
            to packet counts.

    Returns:
        A dict containing lists of weak/strong sectors and a bias flag.
    """

    if not azimuth_histogram:
        return {"weak_sectors": [], "strong_sectors": [], "bias_detected": False}

    counts = list(azimuth_histogram.values())
    if not counts:
        return {"weak_sectors": [], "strong_sectors": [], "bias_detected": False}

    avg = sum(counts) / len(counts)
    if avg == 0:
        return {"weak_sectors": [], "strong_sectors": [], "bias_detected": False}

    weak_threshold = 0.4 * avg
    strong_threshold = 1.6 * avg

    weak_sectors = [sector for sector, count in azimuth_histogram.items() if count < weak_threshold]
    strong_sectors = [sector for sector, count in azimuth_histogram.items() if count > strong_threshold]

    return {
        "weak_sectors": weak_sectors,
        "strong_sectors": strong_sectors,
        "bias_detected": bool(weak_sectors or strong_sectors),
    }


def analyze_directional_balance(azimuth_histogram: dict) -> dict:
    """Analyze gross directional imbalance in packet counts.

    This is a lightweight heuristic to find possible terrain masking,
    local obstacles, or antenna pattern issues based purely on azimuth data.

    Args:
        azimuth_histogram: Either a dict mapping cardinal sector labels (e.g. "N",
            "NE") to packet counts, or the output of `compute_azimuth_histogram`.

    Returns:
        A dict containing average packet count, weak/strong sectors, and a
        `directional_bias` flag.
    """

    if not azimuth_histogram:
        return {
            "average_packets": 0.0,
            "weak_sectors": [],
            "strong_sectors": [],
            "directional_bias": False,
        }

    # If we got a histogram dict from compute_azimuth_histogram, or its
    # legacy output, convert it into sector counts using 8 cardinal directions.
    if isinstance(azimuth_histogram, dict) and "hist" in azimuth_histogram:
        hist = azimuth_histogram.get("hist") or []
        edges = azimuth_histogram.get("edges") or []

        if not hist or not edges or len(edges) != len(hist) + 1:
            return {
                "average_packets": 0.0,
                "weak_sectors": [],
                "strong_sectors": [],
                "directional_bias": False,
            }

        bins = list(zip(edges[:-1], edges[1:]))
        counts = hist
    elif isinstance(azimuth_histogram, list):
        # New output format: list of sectors with explicit start/end and packet
        # count.
        bins = [(s.get("azimuth_start"), s.get("azimuth_end")) for s in azimuth_histogram]
        counts = [s.get("packet_count", 0) for s in azimuth_histogram]
    else:
        bins = []
        counts = []

    if not bins or not counts or len(bins) != len(counts):
        return {
            "average_packets": 0.0,
            "weak_sectors": [],
            "strong_sectors": [],
            "directional_bias": False,
        }

    sector_map = {
        "N": (337.5, 22.5),
        "NE": (22.5, 67.5),
        "E": (67.5, 112.5),
        "SE": (112.5, 157.5),
        "S": (157.5, 202.5),
        "SW": (202.5, 247.5),
        "W": (247.5, 292.5),
        "NW": (292.5, 337.5),
    }

    def _sector_for_angle(angle: float) -> str | None:
        for sector, (start, end) in sector_map.items():
            if start < end:
                if start <= angle < end:
                    return sector
            else:
                # wrap-around case (e.g., N)
                if angle >= start or angle < end:
                    return sector
        return None

    # Map histogram bins to sectors
    sector_counts: dict[str, float] = {s: 0.0 for s in sector_map}
    for (start, end), count in zip(bins, counts):
        if start is None or end is None:
            continue
        bin_center = (start + end) / 2.0
        sector = _sector_for_angle(bin_center % 360.0)
        if sector is not None:
            sector_counts[sector] += count

    azimuth_histogram = sector_counts

    counts = list(azimuth_histogram.values())
    if not counts:
        return {
            "average_packets": 0.0,
            "weak_sectors": [],
            "strong_sectors": [],
            "directional_bias": False,
        }

    avg = sum(counts) / len(counts)
    if avg == 0:
        return {
            "average_packets": 0.0,
            "weak_sectors": [],
            "strong_sectors": [],
            "directional_bias": False,
        }

    weak_threshold = 0.4 * avg
    strong_threshold = 1.6 * avg

    weak_sectors = [sector for sector, count in azimuth_histogram.items() if count < weak_threshold]
    strong_sectors = [sector for sector, count in azimuth_histogram.items() if count > strong_threshold]

    return {
        "average_packets": avg,
        "weak_sectors": weak_sectors,
        "strong_sectors": strong_sectors,
        "directional_bias": bool(weak_sectors or strong_sectors),
    }


__all__ = [
    "compute_azimuth_radiation",
    "compute_azimuth_histogram",
    "detect_sector_bias",
    "analyze_directional_balance",
]
