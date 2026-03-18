"""RF coverage reconstruction from observation events.

Estimator:
coverage(d, a) = P(reception | distance=d, azimuth=a)
                = hits(d, a) / distance_exposures(d)

Where:
- hits(d, a): observations in azimuth bin a at distance bin d
- distance_exposures(d): all observations seen at distance bin d

This uses sparse dict storage and optional Gaussian interpolation for
missing cells.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, Tuple

import pandas as pd


class RFCoverageMap:
    """Reconstructs RF reception probability on a polar distance/azimuth grid."""

    def __init__(
        self,
        distance_bin_km: int = 1,
        azimuth_bin_deg: int = 10,
        max_distance_km: int = 60,
    ) -> None:
        self.distance_bin_km = int(distance_bin_km)
        self.azimuth_bin_deg = int(azimuth_bin_deg)
        self.max_distance_km = int(max_distance_km)

        self._num_distance_bins = max(1, self.max_distance_km // max(1, self.distance_bin_km))
        self._num_azimuth_bins = max(1, 360 // max(1, self.azimuth_bin_deg))

        self.grid: Dict[Tuple[int, int], Dict[str, int]] = {}
        self.distance_exposures = defaultdict(int)

    @staticmethod
    def _get_value(observation: Any, *names: str) -> Any:
        if isinstance(observation, dict):
            for name in names:
                if name in observation:
                    return observation.get(name)
            return None

        for name in names:
            if hasattr(observation, name):
                return getattr(observation, name)
        return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            num = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(num):
            return None
        return num

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _cell(self, distance_km: float, bearing_deg: float) -> Tuple[int, int] | None:
        if distance_km < 0:
            return None
        if distance_km >= float(self.max_distance_km):
            return None

        d_bin = int(distance_km / self.distance_bin_km)
        a_bin = int((bearing_deg % 360.0) / self.azimuth_bin_deg)

        if d_bin < 0 or d_bin >= self._num_distance_bins:
            return None
        if a_bin < 0 or a_bin >= self._num_azimuth_bins:
            return None
        return d_bin, a_bin

    def update(self, observation: Any) -> None:
        """Ingest one RF observation event into the sparse grid."""
        distance = self._to_float(
            self._get_value(observation, "distance_km", "distance")
        )
        bearing = self._to_float(
            self._get_value(observation, "bearing_deg", "bearing")
        )

        if distance is None or bearing is None:
            return

        key = self._cell(distance, bearing)
        if key is None:
            return

        d_bin, _ = key
        self.distance_exposures[d_bin] += 1

        entry = self.grid.setdefault(key, {"hits": 0, "exposures": 0})
        entry["hits"] += 1

    def compute_probability(self) -> Dict[Tuple[int, int], float]:
        """Return direct probability map using distance-conditioned exposures."""
        out: Dict[Tuple[int, int], float] = {}
        for key, counts in self.grid.items():
            d_bin, _ = key
            exp = int(self.distance_exposures.get(d_bin, 0))
            if exp > 0:
                p = float(counts.get("hits", 0)) / float(exp)
                out[key] = self._clamp01(p)
        return out

    def interpolate_missing(self, radius_bins: int = 2, sigma: float = 1.5) -> Dict[Tuple[int, int], float]:
        """Estimate probabilities for unobserved bins using Gaussian neighbors."""
        base = self.compute_probability()
        if not base:
            return {}

        out = dict(base)
        sigma2 = float(sigma) * float(sigma)

        for d_bin in range(self._num_distance_bins):
            for a_bin in range(self._num_azimuth_bins):
                key = (d_bin, a_bin)
                if key in base:
                    continue

                w_sum = 0.0
                p_sum = 0.0

                for dd in range(-radius_bins, radius_bins + 1):
                    nd = d_bin + dd
                    if nd < 0 or nd >= self._num_distance_bins:
                        continue

                    for da in range(-radius_bins, radius_bins + 1):
                        na = (a_bin + da) % self._num_azimuth_bins
                        n_key = (nd, na)
                        p = base.get(n_key)
                        if p is None:
                            continue

                        dist2 = float(dd * dd + da * da)
                        w = math.exp(-dist2 / sigma2)
                        w_sum += w
                        p_sum += w * p

                if w_sum > 0.0:
                    out[key] = self._clamp01(p_sum / w_sum)

        return out

    def to_dataframe(self, interpolate: bool = True) -> pd.DataFrame:
        """Export coverage map as DataFrame with probability per grid cell."""
        probs = self.interpolate_missing() if interpolate else self.compute_probability()
        rows = [
            {
                "distance_bin": int(d),
                "azimuth_bin": int(a),
                "coverage_probability": float(p),
            }
            for (d, a), p in probs.items()
        ]
        if not rows:
            return pd.DataFrame(columns=["distance_bin", "azimuth_bin", "coverage_probability"])
        return pd.DataFrame(rows).sort_values(["distance_bin", "azimuth_bin"]).reset_index(drop=True)


__all__ = ["RFCoverageMap"]
