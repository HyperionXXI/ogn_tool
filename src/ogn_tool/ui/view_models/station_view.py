from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class StationAnalysisView:
    packet_count: int = 0
    max_range_km: float | None = None
    shadow_sectors: list = field(default_factory=list)
    blind_zones: Any = None
    coverage: Any = None
    metrics: dict = field(default_factory=dict)
    rf_models: dict = field(default_factory=dict)
    azimuth_df: Any = None

    @classmethod
    def from_results(cls, results: Any, packet_count: int = 0) -> "StationAnalysisView":
        metrics = getattr(results, "metrics", None) or {}
        max_range_km = metrics.get("observed_max_km")
        if max_range_km is None:
            max_range_km = metrics.get("max_range_km")

        return cls(
            packet_count=int(packet_count),
            max_range_km=max_range_km,
            shadow_sectors=getattr(results, "antenna_shadow_sectors", None) or [],
            blind_zones=getattr(results, "blind_zones", None),
            coverage=getattr(results, "coverage", None),
            metrics=metrics,
            rf_models=metrics.get("rf_models", {}) if isinstance(metrics, dict) else {},
            azimuth_df=metrics.get("azimuth_df") if isinstance(metrics, dict) else None,
        )

    @classmethod
    def from_dataset_dict(cls, dataset: dict | None) -> "StationAnalysisView":
        dataset = dataset or {}
        metrics = dataset.get("metrics") or {}
        return cls(
            packet_count=len(dataset.get("rf_receptions") or []),
            max_range_km=metrics.get("max_range_km"),
            shadow_sectors=metrics.get("antenna_shadow_sectors") or [],
            blind_zones=dataset.get("blind_cells"),
            coverage=dataset.get("coverage_grid"),
            metrics=metrics,
            rf_models=metrics.get("rf_models", {}),
            azimuth_df=dataset.get("azimuth_df"),
        )
