from __future__ import annotations

import time
from typing import Any, Dict, Iterable

from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset


class RFAnalysisPipeline:
    def __init__(self, stages: Iterable[Any]):
        self.stages = list(stages)
        self.metrics: Dict[str, Dict[str, Any]] = {}

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
