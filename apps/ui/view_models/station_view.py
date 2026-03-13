from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ogn_tool.models.rf_analysis_results import RFAnalysisResults


@dataclass
class StationAnalysisView:
    """UI boundary adapter for station-focused analysis views.

    Canonical path: `from_results(...)`.
    Legacy compatibility path: `from_dataset_dict(...)`, which first converts the
    dataset dict into an `RFAnalysisResults`-shaped object before delegating to
    the canonical typed constructor.
    """
    packet_count: int = 0
    max_range_km: float | None = None
    shadow_sectors: list = field(default_factory=list)
    blind_zones: Any = None
    coverage: Any = None
    metrics: dict = field(default_factory=dict)
    rf_models: dict = field(default_factory=dict)
    azimuth_df: Any = None
    azimuth_histogram: dict | None = None
    directional_balance: dict | None = None
    shadow_map: Any = None

    station_id: str = "—"
    station_lat: float | None = None
    station_lon: float | None = None
    hours: int | None = None
    data_source: str | None = None
    dst_types: list[str] = field(default_factory=list)
    rf_local_count: int = 0

    @staticmethod
    def _results_from_dataset_dict(dataset: dict | None) -> RFAnalysisResults:
        dataset = dataset or {}
        metrics = dict(dataset.get("metrics") or {})

        packets_all = dataset.get("packets_all")
        packets_rf = dataset.get("packets_rf")
        metrics.setdefault("packets_all", packets_all)
        metrics.setdefault("packets_rf", packets_rf)
        metrics.setdefault("station_metrics", dataset.get("station_metrics"))
        metrics.setdefault("azimuth_df", dataset.get("azimuth_df"))
        metrics.setdefault("azimuth_histogram", dataset.get("azimuth_histogram"))
        metrics.setdefault("directional_balance", dataset.get("directional_balance"))
        metrics.setdefault("shadow_map", dataset.get("shadow_map"))

        return RFAnalysisResults(
            coverage=dataset.get("coverage_grid"),
            blind_zones=dataset.get("blind_cells"),
            antenna_shadow_sectors=metrics.get("antenna_shadow_sectors") or [],
            metrics=metrics,
        )

    @classmethod
    def from_results(cls, results: RFAnalysisResults | Any, packet_count: int = 0, **context: Any) -> "StationAnalysisView":
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
            azimuth_histogram=metrics.get("azimuth_histogram") if isinstance(metrics, dict) else None,
            directional_balance=metrics.get("directional_balance") if isinstance(metrics, dict) else None,
            shadow_map=metrics.get("shadow_map") if isinstance(metrics, dict) else None,
            station_id=context.get("station_id") or "-",
            station_lat=context.get("station_lat"),
            station_lon=context.get("station_lon"),
            hours=context.get("hours"),
            data_source=context.get("data_source"),
            dst_types=list(context.get("dst_types") or []),
            rf_local_count=int(context.get("rf_local_count", 0) or 0),
        )

    @classmethod
    def from_dataset_dict(cls, dataset: dict | None, **context: Any) -> "StationAnalysisView":
        dataset = dataset or {}
        packet_count = len(dataset.get("rf_receptions") or [])
        results = cls._results_from_dataset_dict(dataset)
        return cls.from_results(results, packet_count=packet_count, **context)

    @classmethod
    def from_context(cls, ctx: dict) -> "StationAnalysisView":
        results = ctx.get("results")
        if results is not None:
            packet_count = int(ctx.get("rf_local_count", 0) or 0)
            return cls.from_results(
                results,
                packet_count=packet_count,
                station_id=ctx.get("station_callsign") or "—",
                station_lat=ctx.get("station_lat"),
                station_lon=ctx.get("station_lon"),
                hours=ctx.get("hours"),
                data_source=ctx.get("data_source"),
                dst_types=list(ctx.get("dst_types") or []),
                rf_local_count=int(ctx.get("rf_local_count", 0) or 0),
            )

        pd_mod = ctx["pd"]
        dataset = ctx.get("dataset", {}) or {}

        packets_window = ctx.get("packets_window")
        rf_packets = ctx.get("rf_packets")
        if packets_window is None:
            packets_window = pd_mod.DataFrame()
        if rf_packets is None:
            rf_packets = pd_mod.DataFrame()

        metrics = dict(dataset.get("metrics") or {})
        metrics.setdefault("packets_all", dataset.get("packets_all") if dataset.get("packets_all") is not None else packets_window)
        metrics.setdefault("packets_rf", dataset.get("packets_rf") if dataset.get("packets_rf") is not None else rf_packets)
        metrics.setdefault("station_metrics", dataset.get("station_metrics") if dataset.get("station_metrics") is not None else pd_mod.DataFrame())

        max_range_km = metrics.get("observed_max_km")
        if max_range_km is None:
            max_range_km = metrics.get("max_range_km")

        return cls(
            packet_count=len(rf_packets),
            max_range_km=max_range_km,
            shadow_sectors=metrics.get("antenna_shadow_sectors") or [],
            blind_zones=dataset.get("blind_cells"),
            coverage=dataset.get("coverage_grid") if dataset.get("coverage_grid") is not None else pd_mod.DataFrame(),
            metrics=metrics,
            rf_models=metrics.get("rf_models", {}),
            azimuth_df=dataset.get("azimuth_df") or metrics.get("azimuth_df"),
            azimuth_histogram=dataset.get("azimuth_histogram") or metrics.get("azimuth_histogram"),
            directional_balance=dataset.get("directional_balance") or metrics.get("directional_balance"),
            shadow_map=dataset.get("shadow_map") or metrics.get("shadow_map"),
            station_id=ctx.get("station_callsign") or "—",
            station_lat=ctx.get("station_lat"),
            station_lon=ctx.get("station_lon"),
            hours=ctx.get("hours"),
            data_source=ctx.get("data_source"),
            dst_types=list(ctx.get("dst_types") or []),
            rf_local_count=int(ctx.get("rf_local_count", 0) or 0),
        )

    @property
    def has_rf(self) -> bool:
        packets_rf = self.metrics.get("packets_rf")
        return packets_rf is not None and len(packets_rf) > 0
