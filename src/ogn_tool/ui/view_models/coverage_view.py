from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CoverageAnalysisView:
    packets_all: Any
    packets_rf: Any
    coverage_grid: Any
    station_metrics: Any
    station_id: str
    station_lat: float | None
    station_lon: float | None
    hours: int | None
    data_source: str | None
    dst_types: list[str]
    rf_local_count: int

    @classmethod
    def from_context(cls, ctx: dict) -> "CoverageAnalysisView":
        pd_mod = ctx["pd"]
        dataset = ctx.get("dataset", {}) or {}

        packets_window = ctx.get("packets_window")
        rf_packets = ctx.get("rf_packets")
        if packets_window is None:
            packets_window = pd_mod.DataFrame()
        if rf_packets is None:
            rf_packets = pd_mod.DataFrame()

        packets_all = dataset.get("packets_all")
        if packets_all is None:
            packets_all = packets_window

        packets_rf = dataset.get("packets_rf")
        if packets_rf is None:
            packets_rf = rf_packets

        coverage_grid = dataset.get("coverage_grid")
        if coverage_grid is None:
            coverage_grid = pd_mod.DataFrame()

        station_metrics = dataset.get("station_metrics")
        if station_metrics is None:
            station_metrics = pd_mod.DataFrame()

        return cls(
            packets_all=packets_all,
            packets_rf=packets_rf,
            coverage_grid=coverage_grid,
            station_metrics=station_metrics,
            station_id=ctx.get("station_callsign") or "—",
            station_lat=ctx.get("station_lat"),
            station_lon=ctx.get("station_lon"),
            hours=ctx.get("hours"),
            data_source=ctx.get("data_source"),
            dst_types=list(ctx.get("dst_types") or []),
            rf_local_count=int(ctx.get("rf_local_count", 0) or 0),
        )

    @property
    def total_packets(self) -> int:
        return len(self.packets_all) if self.packets_all is not None else 0

    @property
    def total_rf_packets(self) -> int:
        return len(self.packets_rf) if self.packets_rf is not None else 0

    @property
    def has_rf(self) -> bool:
        return self.total_rf_packets > 0
