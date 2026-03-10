"""Legacy entry point for experimental shadow diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from .experimental.shadow import compute_shadow_proxy


def detect_rf_shadows(
    packets_filtered,
    azimuth_histogram: dict | None,
    directional_balance: dict | None,
    station_lat: float,
    station_lon: float,
) -> dict:
    """Detect RF shadowing based on azimuth/coverage imbalance.

    This is a lightweight wrapper over existing shadow diagnostics. It is
    intentionally conservative: when directional imbalance is observed it
    returns a basic report structure without making strong assumptions.
    """

    if not directional_balance or not directional_balance.get("directional_bias"):
        return {
            "shadow_sectors": [],
            "suspected_causes": [],
            "confidence": 0.0,
        }

    # Map cardinal sectors to rough azimuth ranges.
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

    weak = directional_balance.get("weak_sectors") or []
    shadow_sectors = []
    for sector in weak:
        if sector in sector_map:
            az0, az1 = sector_map[sector]
            shadow_sectors.append(
                {"azimuth_start": az0, "azimuth_end": az1, "severity": 0.7}
            )

    # Use a simple confidence metric based on number of weak sectors.
    confidence = min(1.0, 0.2 + 0.2 * len(shadow_sectors))

    return {
        "shadow_sectors": shadow_sectors,
        "suspected_causes": ["terrain", "building_obstruction"],
        "confidence": confidence,
    }


__all__ = ["compute_shadow_proxy", "detect_rf_shadows"]
