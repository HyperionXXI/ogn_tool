from __future__ import annotations

from typing import Any, Dict, Iterable


class RFAnalysisPipeline:
    def __init__(self, stages: Iterable[Any]):
        self.stages = list(stages)

    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        for stage in self.stages:
            dataset = stage.run(dataset)
        return dataset
