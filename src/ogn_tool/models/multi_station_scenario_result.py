from __future__ import annotations

from dataclasses import dataclass, field

from ogn_tool.models.scenario_result import ScenarioMetrics


@dataclass
class MultiStationScenarioResult:
    baseline_run_id: str | None
    scenario: str
    candidates: list[dict[str, float]] = field(default_factory=list)
    metrics: ScenarioMetrics = field(default_factory=ScenarioMetrics)
    anomalies: list[str] = field(default_factory=list)
