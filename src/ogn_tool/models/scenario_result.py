from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScenarioMetrics:
    values: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]


@dataclass
class ScenarioResult:
    baseline_run_id: str | None
    scenario: str
    candidate: dict[str, float] | None = None
    station_id: str | None = None
    metrics: ScenarioMetrics = field(default_factory=ScenarioMetrics)
    anomalies: list[str] = field(default_factory=list)

    def priority_score(self) -> float:
        return float(self.metrics.get("priority_score", 0))
