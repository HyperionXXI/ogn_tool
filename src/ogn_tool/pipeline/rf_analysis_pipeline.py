from __future__ import annotations

import time
from typing import Any, Dict, Iterable

from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from .rf_stages import (
    AntennaPatternStage,
    BlindZoneDetectionStage,
    FeatureMatrixStage,
    RFCoverageStage,
    RFDiagnosticsStage,
    VisibilityModelStage,
)


class RFAnalysisPipeline:
    def __init__(self, stages: Iterable[Any] | None = None):
        if stages is None:
            stages = [
                FeatureMatrixStage(),
                RFCoverageStage(),
                VisibilityModelStage(),
                BlindZoneDetectionStage(),
                AntennaPatternStage(),
                RFDiagnosticsStage(),
            ]
        self.stages = list(stages)
        self.metrics: Dict[str, Dict[str, Any]] = {}
        self.validate_pipeline()

    def validate_pipeline(self) -> None:
        # observations are pre-existing input on RFAnalysisDataset
        produced = {"observations"}

        for stage in self.stages:
            missing = [r for r in getattr(stage, "requires", []) if r not in produced]
            if missing:
                raise RuntimeError(
                    f"Stage {getattr(stage, 'name', stage.__class__.__name__)} requires {missing} "
                    "but they were not produced by previous stages"
                )
            produced.update(getattr(stage, "produces", []))

    @staticmethod
    def _count_items(value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(len(value))
        except TypeError:
            return 0

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        self.metrics = {}
        for stage in self.stages:
            stage_name = getattr(stage, "name", stage.__class__.__name__)
            requires = set(getattr(stage, "requires", []))
            available = dataset.available_fields()
            missing = sorted(requires - available)
            if missing:
                raise RuntimeError(f"Stage {stage_name} missing inputs {missing}")

            start = time.perf_counter()
            dataset = stage.run(dataset)
            elapsed = time.perf_counter() - start
            items_processed = self._count_items(getattr(dataset, "observations", []))
            self.metrics[stage_name] = {
                "executed": True,
                "time": elapsed,
                "items": items_processed,
            }
        return dataset
