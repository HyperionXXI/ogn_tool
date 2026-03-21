"""RF propagation primitives.

This module must remain independent from analysis/pipeline layers.
"""

from __future__ import annotations

import math


def free_space_path_loss_db(distance_km: float, frequency_mhz: float = 868.0) -> float:
    """Compute free-space path loss in dB for distance in km and frequency in MHz."""
    d = max(float(distance_km), 1e-9)
    f = max(float(frequency_mhz), 1e-9)
    return 32.44 + 20.0 * math.log10(d) + 20.0 * math.log10(f)


__all__ = ["free_space_path_loss_db"]
